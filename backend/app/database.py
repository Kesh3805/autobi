"""
DuckDB Database Manager with Complete Error Handling
Handles CSV ingestion, query execution, and schema inspection.
"""

import duckdb
import io
import time
import re
from typing import List, Dict, Any, Optional


class DatabaseManager:
    """
    DuckDB database manager with comprehensive error handling and fallbacks.
    """
    
    def __init__(self, db_path: str = ":memory:"):
        """Initialize DuckDB connection."""
        self.conn = duckdb.connect(db_path)
        self._tables: Dict[str, Dict] = {}
        self._setup_extensions()
    
    def _setup_extensions(self):
        """Setup DuckDB extensions for better CSV handling."""
        try:
            self.conn.execute("SET enable_progress_bar = false")
        except:
            pass
    
    def ingest_csv(self, content: bytes, table_name: str) -> Dict[str, Any]:
        """
        Ingest CSV content into DuckDB table.
        Handles various CSV formats and encodings.
        """
        errors = []
        
        # Approach 1: Using pandas (most robust)
        try:
            return self._ingest_with_pandas(content, table_name)
        except Exception as e:
            errors.append(f"Pandas: {str(e)}")
        
        # Approach 2: Manual parsing
        try:
            return self._ingest_manual(content, table_name)
        except Exception as e:
            errors.append(f"Manual: {str(e)}")
        
        raise Exception(f"Failed to ingest CSV. Errors: {'; '.join(errors)}")
    
    def _ingest_with_pandas(self, content: bytes, table_name: str) -> Dict[str, Any]:
        """Ingest using pandas as intermediary."""
        try:
            import pandas as pd
        except ImportError:
            raise Exception("Pandas not available")
        
        # Try different encodings
        df = None
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                break
            except:
                continue
        
        if df is None:
            df = pd.read_csv(io.BytesIO(content), encoding='utf-8', errors='ignore')
        
        # Clean column names
        df.columns = [
            self._clean_column_name(col)
            for col in df.columns
        ]
        
        # Remove duplicate column names
        seen = {}
        new_cols = []
        for col in df.columns:
            if col in seen:
                seen[col] += 1
                new_cols.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                new_cols.append(col)
        df.columns = new_cols
        
        # Register and create table
        temp_name = f'{table_name}_df'
        self.conn.register(temp_name, df)
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {temp_name}")
        self.conn.unregister(temp_name)
        
        # Store metadata
        self._tables[table_name] = {
            "row_count": len(df),
            "columns": list(df.columns)
        }
        
        return {
            "row_count": len(df),
            "columns": list(df.columns)
        }
    
    def _ingest_manual(self, content: bytes, table_name: str) -> Dict[str, Any]:
        """Manual CSV parsing as last resort."""
        text = content.decode('utf-8', errors='ignore')
        lines = text.strip().split('\n')
        
        if len(lines) < 2:
            raise Exception("CSV must have header and at least one data row")
        
        # Parse header
        header = self._parse_csv_line(lines[0])
        header = [self._clean_column_name(h) for h in header]
        
        # Parse data rows
        rows = []
        for line in lines[1:]:
            if line.strip():
                values = self._parse_csv_line(line)
                if len(values) == len(header):
                    rows.append(values)
        
        if not rows:
            raise Exception("No valid data rows found")
        
        # Create table
        col_defs = ", ".join([f'"{col}" VARCHAR' for col in header])
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} ({col_defs})")
        
        # Insert data
        placeholders = ", ".join(["?" for _ in header])
        for row in rows:
            self.conn.execute(
                f"INSERT INTO {table_name} VALUES ({placeholders})",
                row
            )
        
        self._tables[table_name] = {
            "row_count": len(rows),
            "columns": header
        }
        
        return {
            "row_count": len(rows),
            "columns": header
        }
    
    def _parse_csv_line(self, line: str) -> List[str]:
        """Parse a CSV line handling quotes."""
        result = []
        current = ""
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                result.append(current.strip().strip('"'))
                current = ""
            else:
                current += char
        
        result.append(current.strip().strip('"'))
        return result
    
    def _clean_column_name(self, name: str) -> str:
        """Clean column name for SQL compatibility."""
        cleaned = re.sub(r'[^\w\s]', '', str(name))
        cleaned = cleaned.strip().lower().replace(' ', '_')
        cleaned = re.sub(r'_+', '_', cleaned)
        if cleaned and cleaned[0].isdigit():
            cleaned = 'col_' + cleaned
        if not cleaned:
            cleaned = 'column'
        return cleaned
    
    def list_tables(self) -> List[Dict[str, Any]]:
        """List all tables with their column info."""
        try:
            result = self.conn.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main'
            """).fetchall()
        except:
            return []
        
        tables = []
        for (table_name,) in result:
            try:
                columns = self.get_columns(table_name)
                row_count = self._tables.get(table_name, {}).get("row_count", 0)
                
                if row_count == 0:
                    try:
                        count_result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                        row_count = count_result[0] if count_result else 0
                    except:
                        pass
                
                tables.append({
                    "name": table_name,
                    "columns": columns,
                    "row_count": row_count
                })
            except:
                continue
        
        return tables
    
    def get_columns(self, table_name: str) -> List[Dict[str, str]]:
        """Get column names and types for a table."""
        try:
            result = self.conn.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
            """).fetchall()
            
            return [{"name": name, "type": dtype} for name, dtype in result]
        except:
            return []
    
    def execute_query(self, sql: str, limit: Optional[int] = 10000) -> Dict[str, Any]:
        """
        Execute SQL query and return results.
        """
        start_time = time.time()
        
        sql = sql.strip()
        if sql.endswith(';'):
            sql = sql[:-1]
        
        sql_upper = sql.upper()
        if limit and "LIMIT" not in sql_upper:
            sql = f"{sql} LIMIT {limit}"
        
        try:
            result = self.conn.execute(sql)
            
            if result.description:
                columns = [desc[0] for desc in result.description]
                rows = result.fetchall()
            else:
                columns = []
                rows = []
            
            execution_time = (time.time() - start_time) * 1000
            
            data = [dict(zip(columns, row)) for row in rows]
            
            column_info = []
            for col in columns:
                sample_values = [row[col] for row in data[:100] if row.get(col) is not None]
                col_type = self._infer_semantic_type(col, sample_values)
                column_info.append({
                    "name": col,
                    "type": col_type
                })
            
            return {
                "success": True,
                "data": data,
                "columns": column_info,
                "row_count": len(data),
                "execution_time_ms": round(execution_time, 2)
            }
        except Exception as e:
            raise Exception(f"Query failed: {str(e)}")
    
    def _infer_semantic_type(self, col_name: str, values: List[Any]) -> str:
        """Infer semantic type from column name and values."""
        col_lower = col_name.lower()
        
        date_keywords = ['date', 'time', 'created', 'updated', 'timestamp', 'day', 'month', 'year', 'period']
        if any(kw in col_lower for kw in date_keywords):
            return "date"
        
        measure_keywords = [
            'amount', 'price', 'cost', 'revenue', 'sales', 'count', 
            'total', 'sum', 'avg', 'quantity', 'value', 'rate', 'score',
            'balance', 'fee', 'tax', 'profit', 'margin', 'volume'
        ]
        if any(kw in col_lower for kw in measure_keywords):
            return "measure"
        
        if values:
            numeric_count = sum(1 for v in values[:20] if isinstance(v, (int, float)))
            if numeric_count > len(values[:20]) * 0.8:
                unique_ratio = len(set(str(v) for v in values)) / len(values) if values else 0
                if unique_ratio > 0.3:
                    return "measure"
        
        return "dimension"
    
    def get_table_sample(self, table_name: str, n: int = 5) -> List[Dict]:
        """Get sample rows from a table."""
        result = self.execute_query(f"SELECT * FROM {table_name} LIMIT {n}")
        return result["data"]
    
    def get_column_stats(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """Get statistics for a specific column."""
        try:
            col_info = self.conn.execute(f"""
                SELECT data_type FROM information_schema.columns 
                WHERE table_name = '{table_name}' AND column_name = '{column_name}'
            """).fetchone()
        except:
            return {"error": "Column not found"}
        
        if not col_info:
            return {"error": "Column not found"}
        
        dtype = col_info[0]
        stats = {"column": column_name, "type": dtype}
        
        try:
            if dtype.upper() in ['INTEGER', 'BIGINT', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC']:
                result = self.conn.execute(f"""
                    SELECT 
                        COUNT(*) as count,
                        COUNT(DISTINCT "{column_name}") as unique_count,
                        SUM(CASE WHEN "{column_name}" IS NULL THEN 1 ELSE 0 END) as null_count,
                        MIN("{column_name}") as min_val,
                        MAX("{column_name}") as max_val,
                        AVG("{column_name}") as mean,
                        STDDEV("{column_name}") as std
                    FROM {table_name}
                """).fetchone()
                
                stats.update({
                    "count": result[0],
                    "unique_count": result[1],
                    "null_count": result[2],
                    "min": result[3],
                    "max": result[4],
                    "mean": round(result[5], 2) if result[5] else None,
                    "std": round(result[6], 2) if result[6] else None
                })
            else:
                result = self.conn.execute(f"""
                    SELECT 
                        COUNT(*) as count,
                        COUNT(DISTINCT "{column_name}") as unique_count,
                        SUM(CASE WHEN "{column_name}" IS NULL THEN 1 ELSE 0 END) as null_count
                    FROM {table_name}
                """).fetchone()
                
                stats.update({
                    "count": result[0],
                    "unique_count": result[1],
                    "null_count": result[2]
                })
                
                try:
                    top_values = self.conn.execute(f"""
                        SELECT "{column_name}", COUNT(*) as freq 
                        FROM {table_name} 
                        WHERE "{column_name}" IS NOT NULL
                        GROUP BY "{column_name}" 
                        ORDER BY freq DESC 
                        LIMIT 10
                    """).fetchall()
                    
                    stats["top_values"] = [{"value": v, "count": c} for v, c in top_values]
                except:
                    stats["top_values"] = []
        except Exception as e:
            stats["error"] = str(e)
        
        return stats
