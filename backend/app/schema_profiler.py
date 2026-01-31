"""
Schema Profiler
Analyzes table structure, detects column types, and profiles data quality.
"""

from typing import Dict, List, Any
from app.database import DatabaseManager


class SchemaProfiler:
    """
    Profiles database schemas to provide context for NL→SQL conversion.
    
    Detects:
    - Date columns (for time series analysis)
    - Measures (numeric columns for aggregation)
    - Dimensions (categorical columns for grouping)
    - Data quality issues (nulls, outliers, sparse data)
    """
    
    DATE_KEYWORDS = [
        'date', 'time', 'created', 'updated', 'timestamp', 
        'day', 'month', 'year', 'week', 'quarter'
    ]
    
    MEASURE_KEYWORDS = [
        'amount', 'price', 'cost', 'revenue', 'sales', 'count',
        'total', 'sum', 'quantity', 'value', 'rate', 'score',
        'balance', 'fee', 'tax', 'discount', 'profit', 'margin'
    ]
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def profile_table(self, table_name: str) -> Dict[str, Any]:
        """
        Generate comprehensive profile for a table.
        
        Returns:
        - columns: List of column profiles
        - row_count: Total rows
        - quality_score: 0-100 data quality metric
        - date_columns: Detected date columns
        - measure_columns: Detected numeric measures
        - dimension_columns: Detected categorical dimensions
        """
        columns = self.db.get_columns(table_name)
        
        # Get row count
        result = self.db.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        row_count = result[0]
        
        column_profiles = []
        date_columns = []
        measure_columns = []
        dimension_columns = []
        
        total_quality = 0
        
        for col in columns:
            col_name = col["name"]
            col_type = col["type"]
            
            # Get column stats
            stats = self.db.get_column_stats(table_name, col_name)
            
            # Determine semantic type
            semantic_type = self._classify_column(col_name, col_type, stats)
            
            # Calculate quality score for column
            quality = self._calculate_quality(stats, row_count)
            total_quality += quality
            
            profile = {
                "name": col_name,
                "sql_type": col_type,
                "semantic_type": semantic_type,
                "stats": stats,
                "quality_score": quality
            }
            
            column_profiles.append(profile)
            
            # Categorize
            if semantic_type == "date":
                date_columns.append(col_name)
            elif semantic_type == "measure":
                measure_columns.append(col_name)
            else:
                dimension_columns.append(col_name)
        
        avg_quality = total_quality / len(columns) if columns else 0
        
        return {
            "table_name": table_name,
            "row_count": row_count,
            "column_count": len(columns),
            "columns": column_profiles,
            "date_columns": date_columns,
            "measure_columns": measure_columns,
            "dimension_columns": dimension_columns,
            "quality_score": round(avg_quality, 1),
            "warnings": self._generate_warnings(column_profiles, row_count)
        }
    
    def _classify_column(self, name: str, sql_type: str, stats: Dict) -> str:
        """Classify column as date, measure, or dimension."""
        name_lower = name.lower()
        
        # Check for date patterns
        if any(kw in name_lower for kw in self.DATE_KEYWORDS):
            return "date"
        
        # Check SQL type for timestamps
        if 'DATE' in sql_type.upper() or 'TIME' in sql_type.upper():
            return "date"
        
        # Check for measure patterns
        if any(kw in name_lower for kw in self.MEASURE_KEYWORDS):
            return "measure"
        
        # Numeric types with high cardinality are likely measures
        if sql_type.upper() in ['INTEGER', 'BIGINT', 'DOUBLE', 'FLOAT', 'DECIMAL']:
            unique_ratio = stats.get("unique_count", 0) / stats.get("count", 1) if stats.get("count", 0) > 0 else 0
            if unique_ratio > 0.3:
                return "measure"
        
        return "dimension"
    
    def _calculate_quality(self, stats: Dict, row_count: int) -> float:
        """Calculate data quality score (0-100) for a column."""
        if row_count == 0:
            return 0
        
        score = 100.0
        
        # Penalize nulls
        null_ratio = stats.get("null_count", 0) / row_count
        score -= null_ratio * 50
        
        # Penalize low cardinality in what should be unique columns
        if stats.get("unique_count", 0) == 1 and row_count > 10:
            score -= 20
        
        return max(0, min(100, score))
    
    def _generate_warnings(self, columns: List[Dict], row_count: int) -> List[str]:
        """Generate data quality warnings."""
        warnings = []
        
        if row_count < 30:
            warnings.append(f"Small sample size ({row_count} rows). Statistical insights may be unreliable.")
        
        for col in columns:
            stats = col.get("stats", {})
            null_count = stats.get("null_count", 0)
            
            if null_count > 0:
                null_pct = (null_count / row_count * 100) if row_count > 0 else 0
                if null_pct > 20:
                    warnings.append(f"Column '{col['name']}' has {null_pct:.1f}% null values.")
        
        return warnings
    
    def get_schema_context(self, table_name: str) -> str:
        """
        Generate natural language schema context for LLM prompting.
        Used to ground SQL generation in actual schema.
        """
        profile = self.profile_table(table_name)
        
        lines = [f"Table: {table_name}", f"Rows: {profile['row_count']}", "", "Columns:"]
        
        for col in profile["columns"]:
            type_info = f"{col['semantic_type']} ({col['sql_type']})"
            stats = col.get("stats", {})
            
            extra = []
            if col["semantic_type"] == "measure":
                if stats.get("min") is not None:
                    extra.append(f"range: {stats['min']} to {stats['max']}")
            elif col["semantic_type"] == "dimension":
                if stats.get("unique_count"):
                    extra.append(f"{stats['unique_count']} unique values")
                if stats.get("top_values"):
                    top = [str(v["value"]) for v in stats["top_values"][:3]]
                    extra.append(f"examples: {', '.join(top)}")
            
            extra_str = f" [{', '.join(extra)}]" if extra else ""
            lines.append(f"  - {col['name']}: {type_info}{extra_str}")
        
        if profile["warnings"]:
            lines.append("")
            lines.append("Warnings:")
            for w in profile["warnings"]:
                lines.append(f"  - {w}")
        
        return "\n".join(lines)
