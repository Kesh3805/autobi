"""
Query Engine with Complete Fallback Logic
Converts natural language to SQL using LangChain + OpenAI.
Falls back to comprehensive rule-based parsing when LLM unavailable.
"""

import os
import re
import time
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from app.database import DatabaseManager

load_dotenv()


class QueryEngine:
    """
    Natural Language to SQL conversion engine with full fallback support.
    """
    
    FORBIDDEN_KEYWORDS = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
        'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC',
        'EXECUTE', 'XP_', 'SP_', '--', ';--', '/*', '*/'
    ]
    
    INTENT_PATTERNS = {
        'aggregate_sum': [r'\b(total|sum|combined|aggregate)\b', r'\bhow much\b', r'\bsum of\b'],
        'aggregate_avg': [r'\b(average|avg|mean)\b', r'\btypical\b'],
        'aggregate_count': [r'\b(count|how many|number of)\b', r'\bhow often\b'],
        'aggregate_max': [r'\b(max|maximum|highest|largest|biggest|top|best)\b', r'\bmost\b'],
        'aggregate_min': [r'\b(min|minimum|lowest|smallest|least|worst|bottom)\b'],
        'trend': [r'\b(trend|over time|by date|by month|by week|by year|by day)\b', r'\b(history|historical|timeline)\b'],
        'distribution': [r'\b(distribution|spread|histogram|range|frequency)\b'],
        'comparison': [r'\b(compare|vs|versus|comparison)\b', r'\bby category\b'],
        'ranking': [r'\b(top \d+|bottom \d+|first \d+|last \d+)\b', r'\b(rank|ranking)\b'],
        'show_all': [r'\b(show all|list all|all data|everything|all records)\b'],
    }
    
    TIME_PATTERNS = {
        'year': [r'\byear(ly|s)?\b', r'\bannual(ly)?\b'],
        'quarter': [r'\bquarter(ly|s)?\b'],
        'month': [r'\bmonth(ly|s)?\b'],
        'week': [r'\bweek(ly|s)?\b'],
        'day': [r'\bdai?ly\b', r'\bday(s)?\b', r'\bdate\b'],
    }
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.llm = None
        self.llm_available = False
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LangChain with OpenAI."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and api_key != "your_openai_api_key_here" and len(api_key) > 20:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0,
                    api_key=api_key,
                    request_timeout=30
                )
                self.llm_available = True
                print("✓ LLM initialized successfully")
            except ImportError:
                print("⚠ langchain-openai not installed, using fallback")
            except Exception as e:
                print(f"⚠ LLM initialization failed: {e}")
        else:
            print("ℹ No OpenAI API key configured, using rule-based SQL generation")
    
    def process_question(
        self, 
        question: str, 
        table_name: str, 
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process natural language question and return query results."""
        start_time = time.time()
        
        if self.llm_available:
            sql_result = self._generate_sql_with_llm(question, table_name, schema)
            if not sql_result["success"]:
                sql_result = self._generate_sql_fallback(question, table_name, schema)
                sql_result["assumptions"].append("LLM unavailable, used rule-based generation")
        else:
            sql_result = self._generate_sql_fallback(question, table_name, schema)
        
        if not sql_result["success"]:
            return sql_result
        
        sql = sql_result["sql"]
        
        validation = self._validate_sql(sql)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        try:
            result = self.db.execute_query(sql)
            execution_time = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "sql": sql,
                "data": result["data"],
                "columns": result["columns"],
                "row_count": result["row_count"],
                "execution_time_ms": round(execution_time, 2),
                "confidence": sql_result.get("confidence", 0.8),
                "assumptions": sql_result.get("assumptions", [])
            }
        except Exception as e:
            fixed_result = self._try_fix_sql_error(sql, str(e), table_name, schema)
            if fixed_result:
                execution_time = (time.time() - start_time) * 1000
                fixed_result["execution_time_ms"] = round(execution_time, 2)
                return fixed_result
            
            return {"success": False, "error": f"Query execution failed: {str(e)}", "sql": sql}
    
    def _generate_sql_with_llm(self, question: str, table_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL using LLM."""
        schema_context = self._build_schema_context(table_name, schema)
        prompt = self._build_prompt(question, table_name, schema_context)
        
        try:
            response = self.llm.invoke(prompt)
            sql = self._extract_sql(response.content)
            return {"success": True, "sql": sql, "confidence": 0.85, "assumptions": []}
        except Exception as e:
            return {"success": False, "error": f"LLM generation failed: {str(e)}", "assumptions": []}
    
    def _generate_sql_fallback(self, question: str, table_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive rule-based SQL generation."""
        question_lower = question.lower().strip()
        
        measures = schema.get("measure_columns", [])
        dimensions = schema.get("dimension_columns", [])
        dates = schema.get("date_columns", [])
        all_columns = [c["name"] for c in schema.get("columns", [])]
        
        assumptions = []
        intent = self._detect_intent(question_lower)
        mentioned_cols = self._extract_mentioned_columns(question_lower, all_columns)
        filters = self._extract_filters(question_lower, all_columns)
        limit = self._extract_limit(question_lower)
        
        if intent == 'show_all':
            return self._build_show_all_query(table_name, all_columns, filters, limit, assumptions)
        elif intent == 'aggregate_sum':
            return self._build_aggregate_query('SUM', table_name, measures, dimensions, dates, question_lower, mentioned_cols, filters, assumptions)
        elif intent == 'aggregate_avg':
            return self._build_aggregate_query('AVG', table_name, measures, dimensions, dates, question_lower, mentioned_cols, filters, assumptions)
        elif intent == 'aggregate_count':
            return self._build_count_query(table_name, dimensions, dates, question_lower, mentioned_cols, filters, assumptions)
        elif intent in ('aggregate_max', 'ranking'):
            return self._build_ranking_query(table_name, measures, dimensions, question_lower, mentioned_cols, filters, limit, assumptions, ascending=False)
        elif intent == 'aggregate_min':
            return self._build_ranking_query(table_name, measures, dimensions, question_lower, mentioned_cols, filters, limit, assumptions, ascending=True)
        elif intent == 'trend':
            return self._build_trend_query(table_name, measures, dates, question_lower, mentioned_cols, filters, assumptions)
        elif intent == 'distribution':
            return self._build_distribution_query(table_name, measures, question_lower, mentioned_cols, assumptions)
        elif intent == 'comparison':
            return self._build_comparison_query(table_name, measures, dimensions, question_lower, mentioned_cols, filters, assumptions)
        
        return self._build_inferred_query(table_name, measures, dimensions, dates, all_columns, question_lower, mentioned_cols, filters, limit, assumptions)
    
    def _detect_intent(self, question: str) -> Optional[str]:
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    return intent
        return None
    
    def _extract_mentioned_columns(self, question: str, columns: List[str]) -> List[str]:
        mentioned = []
        for col in columns:
            col_pattern = col.replace('_', r'[\s_]?')
            if re.search(rf'\b{col_pattern}\b', question, re.IGNORECASE):
                mentioned.append(col)
        return mentioned
    
    def _extract_filters(self, question: str, columns: List[str]) -> List[Dict[str, Any]]:
        filters = []
        for col in columns:
            col_pattern = col.replace('_', r'[\s_]?')
            match = re.search(rf'{col_pattern}\s*(?:is|=|equals?)\s*["\']?(\w+)["\']?', question, re.IGNORECASE)
            if match:
                filters.append({'column': col, 'operator': '=', 'value': match.group(1)})
            match = re.search(rf'{col_pattern}\s*(?:>|greater than|more than|above|over)\s*(\d+(?:\.\d+)?)', question, re.IGNORECASE)
            if match:
                filters.append({'column': col, 'operator': '>', 'value': float(match.group(1))})
            match = re.search(rf'{col_pattern}\s*(?:<|less than|under|below)\s*(\d+(?:\.\d+)?)', question, re.IGNORECASE)
            if match:
                filters.append({'column': col, 'operator': '<', 'value': float(match.group(1))})
        return filters
    
    def _extract_limit(self, question: str) -> Optional[int]:
        match = re.search(r'\b(?:top|first|limit)\s*(\d+)\b', question, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
    
    def _detect_time_granularity(self, question: str) -> Optional[str]:
        for granularity, patterns in self.TIME_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question, re.IGNORECASE):
                    return granularity
        return None
    
    def _build_where_clause(self, filters: List[Dict]) -> str:
        if not filters:
            return ""
        conditions = []
        for f in filters:
            if isinstance(f['value'], str):
                conditions.append(f"{f['column']} {f['operator']} '{f['value']}'")
            else:
                conditions.append(f"{f['column']} {f['operator']} {f['value']}")
        return "WHERE " + " AND ".join(conditions)
    
    def _build_show_all_query(self, table_name: str, columns: List[str], filters: List[Dict], limit: Optional[int], assumptions: List[str]) -> Dict[str, Any]:
        cols = ", ".join(columns)
        where = self._build_where_clause(filters)
        limit_clause = f"LIMIT {limit or 100}"
        if not limit:
            assumptions.append("Limited to 100 rows for preview")
        sql = f"SELECT {cols} FROM {table_name} {where} {limit_clause}".strip()
        return {"success": True, "sql": sql, "confidence": 0.9, "assumptions": assumptions}
    
    def _build_aggregate_query(self, agg_func: str, table_name: str, measures: List[str], dimensions: List[str], dates: List[str], question: str, mentioned_cols: List[str], filters: List[Dict], assumptions: List[str]) -> Dict[str, Any]:
        measure = None
        for col in mentioned_cols:
            if col in measures:
                measure = col
                break
        if not measure and measures:
            measure = measures[0]
            assumptions.append(f"Using first measure column: {measure}")
        if not measure:
            return self._build_show_all_query(table_name, [c for c in mentioned_cols] or dimensions[:3], filters, 50, assumptions)
        
        group_by = None
        for col in mentioned_cols:
            if col in dimensions:
                group_by = col
                break
        for dim in dimensions:
            if re.search(rf'\bby\s+{dim.replace("_", r"[s_]?")}\b', question, re.IGNORECASE):
                group_by = dim
                break
        
        granularity = self._detect_time_granularity(question)
        if granularity and dates:
            date_col = dates[0]
            group_by = self._format_date_group(date_col, granularity)
            assumptions.append(f"Grouping by {granularity}")
        
        where = self._build_where_clause(filters)
        
        if group_by:
            sql = f"SELECT {group_by}, {agg_func}({measure}) as {agg_func.lower()}_{measure} FROM {table_name} {where} GROUP BY {group_by} ORDER BY {agg_func.lower()}_{measure} DESC LIMIT 50".strip()
        else:
            sql = f"SELECT {agg_func}({measure}) as {agg_func.lower()}_{measure} FROM {table_name} {where}".strip()
        return {"success": True, "sql": sql, "confidence": 0.8, "assumptions": assumptions}
    
    def _build_count_query(self, table_name: str, dimensions: List[str], dates: List[str], question: str, mentioned_cols: List[str], filters: List[Dict], assumptions: List[str]) -> Dict[str, Any]:
        group_by = None
        for col in mentioned_cols:
            if col in dimensions:
                group_by = col
                break
        for dim in dimensions:
            if re.search(rf'\bby\s+{dim.replace("_", r"[s_]?")}\b', question, re.IGNORECASE):
                group_by = dim
                break
        where = self._build_where_clause(filters)
        if group_by:
            sql = f"SELECT {group_by}, COUNT(*) as count FROM {table_name} {where} GROUP BY {group_by} ORDER BY count DESC".strip()
        else:
            sql = f"SELECT COUNT(*) as total_count FROM {table_name} {where}".strip()
        return {"success": True, "sql": sql, "confidence": 0.85, "assumptions": assumptions}
    
    def _build_ranking_query(self, table_name: str, measures: List[str], dimensions: List[str], question: str, mentioned_cols: List[str], filters: List[Dict], limit: Optional[int], assumptions: List[str], ascending: bool = False) -> Dict[str, Any]:
        measure = None
        for col in mentioned_cols:
            if col in measures:
                measure = col
                break
        if not measure and measures:
            measure = measures[0]
            assumptions.append(f"Ranking by: {measure}")
        dim = None
        for col in mentioned_cols:
            if col in dimensions:
                dim = col
                break
        if not dim and dimensions:
            dim = dimensions[0]
        where = self._build_where_clause(filters)
        order = "ASC" if ascending else "DESC"
        limit_val = limit or 10
        if dim and measure:
            sql = f"SELECT {dim}, {measure} FROM {table_name} {where} ORDER BY {measure} {order} LIMIT {limit_val}".strip()
        elif measure:
            sql = f"SELECT * FROM {table_name} {where} ORDER BY {measure} {order} LIMIT {limit_val}".strip()
        else:
            sql = f"SELECT * FROM {table_name} {where} LIMIT {limit_val}".strip()
        return {"success": True, "sql": sql, "confidence": 0.8, "assumptions": assumptions}
    
    def _build_trend_query(self, table_name: str, measures: List[str], dates: List[str], question: str, mentioned_cols: List[str], filters: List[Dict], assumptions: List[str]) -> Dict[str, Any]:
        if not dates:
            assumptions.append("No date column found for trend analysis")
            return {"success": False, "error": "No date column available for trend analysis", "assumptions": assumptions}
        date_col = dates[0]
        granularity = self._detect_time_granularity(question) or 'day'
        measure = None
        for col in mentioned_cols:
            if col in measures:
                measure = col
                break
        if not measure and measures:
            measure = measures[0]
            assumptions.append(f"Using measure: {measure}")
        where = self._build_where_clause(filters)
        date_group = self._format_date_group(date_col, granularity)
        if measure:
            sql = f"SELECT {date_group} as period, SUM({measure}) as total_{measure} FROM {table_name} {where} GROUP BY {date_group} ORDER BY {date_group}".strip()
        else:
            sql = f"SELECT {date_group} as period, COUNT(*) as count FROM {table_name} {where} GROUP BY {date_group} ORDER BY {date_group}".strip()
        return {"success": True, "sql": sql, "confidence": 0.75, "assumptions": assumptions}
    
    def _build_distribution_query(self, table_name: str, measures: List[str], question: str, mentioned_cols: List[str], assumptions: List[str]) -> Dict[str, Any]:
        measure = None
        for col in mentioned_cols:
            if col in measures:
                measure = col
                break
        if not measure and measures:
            measure = measures[0]
            assumptions.append(f"Analyzing distribution of: {measure}")
        if not measure:
            return {"success": False, "error": "No numeric column found for distribution analysis", "assumptions": assumptions}
        sql = f"""
WITH stats AS (
    SELECT MIN({measure}) as min_val, MAX({measure}) as max_val, (MAX({measure}) - MIN({measure})) / 10 as bucket_size
    FROM {table_name}
)
SELECT FLOOR(({measure} - stats.min_val) / NULLIF(stats.bucket_size, 0)) as bucket, MIN({measure}) as bucket_min, MAX({measure}) as bucket_max, COUNT(*) as frequency
FROM {table_name}, stats
GROUP BY bucket ORDER BY bucket""".strip()
        return {"success": True, "sql": sql, "confidence": 0.7, "assumptions": assumptions}
    
    def _build_comparison_query(self, table_name: str, measures: List[str], dimensions: List[str], question: str, mentioned_cols: List[str], filters: List[Dict], assumptions: List[str]) -> Dict[str, Any]:
        measure = None
        for col in mentioned_cols:
            if col in measures:
                measure = col
                break
        if not measure and measures:
            measure = measures[0]
        dim = None
        for col in mentioned_cols:
            if col in dimensions:
                dim = col
                break
        if not dim and dimensions:
            dim = dimensions[0]
        if not measure or not dim:
            return self._build_show_all_query(table_name, mentioned_cols or dimensions[:3] + measures[:2], filters, 50, assumptions)
        where = self._build_where_clause(filters)
        sql = f"SELECT {dim}, SUM({measure}) as total_{measure}, AVG({measure}) as avg_{measure}, COUNT(*) as count FROM {table_name} {where} GROUP BY {dim} ORDER BY total_{measure} DESC".strip()
        return {"success": True, "sql": sql, "confidence": 0.75, "assumptions": assumptions}
    
    def _build_inferred_query(self, table_name: str, measures: List[str], dimensions: List[str], dates: List[str], all_columns: List[str], question: str, mentioned_cols: List[str], filters: List[Dict], limit: Optional[int], assumptions: List[str]) -> Dict[str, Any]:
        by_match = re.search(r'\bby\s+(\w+)', question)
        if by_match:
            group_col = by_match.group(1)
            for col in all_columns:
                if group_col in col.lower() or col.lower() in group_col:
                    if measures:
                        measure = measures[0]
                        sql = f"SELECT {col}, SUM({measure}) as total_{measure} FROM {table_name} {self._build_where_clause(filters)} GROUP BY {col} ORDER BY total_{measure} DESC LIMIT 50".strip()
                        assumptions.append(f"Grouped by {col}, summing {measure}")
                        return {"success": True, "sql": sql, "confidence": 0.7, "assumptions": assumptions}
        if mentioned_cols:
            cols = ", ".join(mentioned_cols)
            where = self._build_where_clause(filters)
            sql = f"SELECT {cols} FROM {table_name} {where} LIMIT {limit or 100}".strip()
            return {"success": True, "sql": sql, "confidence": 0.6, "assumptions": assumptions}
        key_cols = (dimensions[:2] + measures[:2] + dates[:1])[:5]
        if not key_cols:
            key_cols = all_columns[:5]
        cols = ", ".join(key_cols)
        where = self._build_where_clause(filters)
        assumptions.append("Could not parse specific intent. Showing sample data with key columns.")
        sql = f"SELECT {cols} FROM {table_name} {where} LIMIT 50".strip()
        return {"success": True, "sql": sql, "confidence": 0.5, "assumptions": assumptions}
    
    def _format_date_group(self, date_col: str, granularity: str) -> str:
        if granularity == 'year':
            return f"DATE_TRUNC('year', {date_col})"
        elif granularity == 'quarter':
            return f"DATE_TRUNC('quarter', {date_col})"
        elif granularity == 'month':
            return f"DATE_TRUNC('month', {date_col})"
        elif granularity == 'week':
            return f"DATE_TRUNC('week', {date_col})"
        return date_col
    
    def _try_fix_sql_error(self, sql: str, error: str, table_name: str, schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        all_columns = [c["name"] for c in schema.get("columns", [])]
        if "column" in error.lower() and "not found" in error.lower():
            match = re.search(r'column\s+"?(\w+)"?\s+not found', error, re.IGNORECASE)
            if match:
                bad_col = match.group(1)
                for col in all_columns:
                    if bad_col.lower() in col.lower() or col.lower() in bad_col.lower():
                        fixed_sql = re.sub(rf'\b{bad_col}\b', col, sql, flags=re.IGNORECASE)
                        try:
                            result = self.db.execute_query(fixed_sql)
                            return {
                                "success": True, "sql": fixed_sql, "data": result["data"],
                                "columns": result["columns"], "row_count": result["row_count"],
                                "confidence": 0.6, "assumptions": [f"Corrected column name: {bad_col} → {col}"]
                            }
                        except:
                            continue
        return None
    
    def _build_schema_context(self, table_name: str, schema: Dict) -> str:
        lines = [f"Table: {table_name}", "Columns:"]
        for col in schema.get("columns", []):
            semantic = col.get("semantic_type", "unknown")
            sql_type = col.get("sql_type", "unknown")
            lines.append(f"  - {col['name']} ({semantic}, {sql_type})")
        if schema.get("date_columns"):
            lines.append(f"\nDate columns: {', '.join(schema['date_columns'])}")
        if schema.get("measure_columns"):
            lines.append(f"Measure columns: {', '.join(schema['measure_columns'])}")
        if schema.get("dimension_columns"):
            lines.append(f"Dimension columns: {', '.join(schema['dimension_columns'])}")
        return "\n".join(lines)
    
    def _build_prompt(self, question: str, table_name: str, schema_context: str) -> str:
        return f"""You are a SQL expert. Generate a DuckDB-compatible SQL query for the following question.

SCHEMA:
{schema_context}

RULES:
1. Use only columns that exist in the schema
2. Use explicit column names (no SELECT *)
3. Use CTEs for complex queries
4. Include appropriate aggregations for measures
5. Add LIMIT 1000 for large result sets
6. Use proper date functions for time-based queries
7. Generate READ-ONLY queries only (no INSERT, UPDATE, DELETE, DROP)

QUESTION: {question}

Respond with ONLY the SQL query, no explanation."""
    
    def _extract_sql(self, response: str) -> str:
        sql = response.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.startswith("```"):
            sql = sql[3:]
        if sql.endswith("```"):
            sql = sql[:-3]
        lines = sql.strip().split("\n")
        sql_lines = [l for l in lines if not l.strip().startswith("-- Assumption")]
        return "\n".join(sql_lines).strip()
    
    def _validate_sql(self, sql: str) -> Dict[str, Any]:
        sql_upper = sql.upper()
        for keyword in self.FORBIDDEN_KEYWORDS:
            if re.search(rf'\b{keyword}\b', sql_upper):
                return {"valid": False, "error": f"Forbidden operation detected: {keyword}"}
        if sql.count(';') > 1:
            return {"valid": False, "error": "Multiple statements not allowed"}
        return {"valid": True}
