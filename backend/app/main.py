"""
AutoBI Backend - FastAPI Application
LLM-Powered Data Explorer with DuckDB + LangChain
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Any
import os
import uuid

from app.database import DatabaseManager
from app.schema_profiler import SchemaProfiler
from app.query_engine import QueryEngine
from app.insight_engine import InsightEngine
from app.chart_selector import ChartSelector
from app.cache import (
    schema_cache, query_cache, get_cached_schema, 
    cache_schema, get_cached_query, cache_query_result,
    invalidate_table_cache
)
from app.logging_utils import (
    log_info, log_error, log_warning, log_query, 
    log_upload, log_error_detail, RequestContext, log_timing
)

app = FastAPI(
    title="AutoBI",
    description="LLM-Powered Data Explorer",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    """Add request ID and logging to all requests."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
    RequestContext.set_request_id(request_id)
    
    log_info(f"{request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        log_info(f"Completed with status {response.status_code}")
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        log_error_detail(e, f"{request.method} {request.url.path}")
        raise
    finally:
        RequestContext.clear()


# Initialize components
db_manager = DatabaseManager()
schema_profiler = SchemaProfiler(db_manager)
query_engine = QueryEngine(db_manager)
insight_engine = InsightEngine()
chart_selector = ChartSelector()


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    table_name: Optional[str] = Field(None, max_length=100)


class QueryResponse(BaseModel):
    sql: str
    data: List[dict]
    columns: List[dict]
    chart_recommendation: dict
    insights: List[dict]
    row_count: int
    execution_time_ms: float
    confidence: float
    assumptions: List[str]


class SchemaResponse(BaseModel):
    tables: List[dict]
    profile: dict


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload CSV file and ingest into DuckDB.
    Returns schema profile with column types, distributions, and quality metrics.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # Generate table name from filename
        table_name = file.filename.replace('.csv', '').replace(' ', '_').replace('-', '_').lower()
        
        # Ingest into DuckDB
        result = db_manager.ingest_csv(content, table_name)
        
        # Profile the schema
        profile = schema_profiler.profile_table(table_name)
        
        return {
            "success": True,
            "table_name": table_name,
            "row_count": result["row_count"],
            "profile": profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tables")
async def list_tables():
    """List all available tables with their schemas."""
    tables = db_manager.list_tables()
    return {"tables": tables}


@app.get("/schema/{table_name}")
async def get_schema(table_name: str):
    """Get detailed schema profile for a specific table."""
    try:
        profile = schema_profiler.profile_table(table_name)
        return profile
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")


@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Convert natural language to SQL, execute, and return results with insights.
    
    Pipeline:
    1. Intent decomposition
    2. Schema grounding
    3. SQL generation (DuckDB compatible)
    4. Execution with validation
    5. Insight detection
    6. Chart selection
    """
    try:
        # Get available tables
        tables = db_manager.list_tables()
        if not tables:
            raise HTTPException(status_code=400, detail="No tables available. Please upload data first.")
        
        # Use specified table or default to first available
        target_table = request.table_name or tables[0]["name"]
        
        # Get schema for context
        schema = schema_profiler.profile_table(target_table)
        
        # Generate and execute query
        result = query_engine.process_question(
            question=request.question,
            table_name=target_table,
            schema=schema
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Query failed"))
        
        # Detect insights
        insights = insight_engine.detect_insights(
            data=result["data"],
            columns=result["columns"],
            question=request.question
        )
        
        # Select appropriate chart
        chart_rec = chart_selector.recommend(
            data=result["data"],
            columns=result["columns"],
            question=request.question
        )
        
        return QueryResponse(
            sql=result["sql"],
            data=result["data"],
            columns=result["columns"],
            chart_recommendation=chart_rec,
            insights=insights,
            row_count=result["row_count"],
            execution_time_ms=result["execution_time_ms"],
            confidence=result["confidence"],
            assumptions=result.get("assumptions", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sql")
async def execute_raw_sql(sql: str):
    """Execute raw SQL query (read-only, validated)."""
    # Safety check
    sql_upper = sql.upper()
    forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
    for keyword in forbidden:
        if keyword in sql_upper:
            raise HTTPException(status_code=400, detail=f"Forbidden operation: {keyword}")
    
    try:
        result = db_manager.execute_query(sql)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/sample/{table_name}")
async def get_sample_data(table_name: str, limit: int = 100):
    """Get sample data from a table for preview."""
    try:
        result = db_manager.execute_query(f'SELECT * FROM "{table_name}" LIMIT {limit}')
        return {
            "table_name": table_name,
            "data": result["data"],
            "columns": result["columns"],
            "sample_size": len(result["data"])
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")


@app.get("/stats/{table_name}")
async def get_table_stats(table_name: str):
    """Get comprehensive statistics for a table."""
    try:
        profile = schema_profiler.profile_table(table_name)
        
        # Add row count
        count_result = db_manager.execute_query(f'SELECT COUNT(*) as total FROM "{table_name}"')
        row_count = count_result["data"][0]["total"] if count_result["data"] else 0
        
        # Calculate additional stats for numeric columns
        stats = {
            "table_name": table_name,
            "row_count": row_count,
            "column_count": len(profile.get("columns", [])),
            "columns": profile.get("columns", []),
            "quality_score": profile.get("quality_score", 0)
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")


@app.delete("/table/{table_name}")
async def delete_table(table_name: str):
    """Delete a table from the database."""
    try:
        db_manager.execute_query(f'DROP TABLE IF EXISTS "{table_name}"')
        return {"success": True, "message": f"Table {table_name} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/suggestions/{table_name}")
async def get_query_suggestions(table_name: str):
    """Get smart query suggestions based on table schema."""
    try:
        profile = schema_profiler.profile_table(table_name)
        columns = profile.get("columns", [])
        
        suggestions = []
        measure_cols = [c["name"] for c in columns if c.get("type") == "measure"]
        dim_cols = [c["name"] for c in columns if c.get("type") in ["dimension", "text"]]
        date_cols = [c["name"] for c in columns if c.get("type") == "date"]
        
        # Generate smart suggestions
        if measure_cols:
            suggestions.append(f"What is the total {measure_cols[0]}?")
            suggestions.append(f"What is the average {measure_cols[0]}?")
        
        if dim_cols and measure_cols:
            suggestions.append(f"Show {measure_cols[0]} by {dim_cols[0]}")
            suggestions.append(f"Top 10 {dim_cols[0]} by {measure_cols[0]}")
        
        if date_cols and measure_cols:
            suggestions.append(f"Trend of {measure_cols[0]} over time")
            suggestions.append(f"Show {measure_cols[0]} by {date_cols[0]}")
        
        if dim_cols:
            suggestions.append(f"Distribution by {dim_cols[0]}")
            if len(dim_cols) >= 2:
                suggestions.append(f"Breakdown by {dim_cols[0]} and {dim_cols[1]}")
        
        # Always add generic suggestions
        suggestions.extend([
            "Show all data",
            "Count of records",
            "Summary statistics"
        ])
        
        return {
            "table_name": table_name,
            "suggestions": suggestions[:10]  # Limit to 10
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table not found: {table_name}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
