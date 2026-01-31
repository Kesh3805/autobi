"""
Chart Selector with Complete Fallback Logic
Chooses the optimal visualization based on data characteristics and user intent.
Zero external dependencies.
"""

from typing import Dict, List, Any, Optional
import re


class ChartSelector:
    """Intelligent chart selection with comprehensive fallback."""
    
    INTENT_PATTERNS = {
        "trend": [r"\btrend\b", r"\bover time\b", r"\bby date\b", r"\bby month\b", r"\bby week\b", r"\bhistory\b"],
        "comparison": [r"\bcompare\b", r"\bvs\b", r"\bversus\b", r"\bby\b", r"\bper\b", r"\bbreakdown\b"],
        "distribution": [r"\bdistribution\b", r"\bspread\b", r"\bhistogram\b", r"\bfrequency\b"],
        "composition": [r"\bcomposition\b", r"\bshare\b", r"\bproportion\b", r"\bpercentage\b"],
        "correlation": [r"\bcorrelation\b", r"\brelationship\b", r"\bscatter\b"],
        "ranking": [r"\btop\b", r"\bbottom\b", r"\bhighest\b", r"\blowest\b", r"\bbest\b", r"\bworst\b"]
    }
    
    COLORS = {
        "primary": "rgba(59, 130, 246, 0.8)",
        "primary_line": "rgb(59, 130, 246)",
        "primary_fill": "rgba(59, 130, 246, 0.1)",
        "secondary": "rgba(16, 185, 129, 0.8)",
        "tertiary": "rgba(139, 92, 246, 0.8)",
        "palette": [
            "rgba(59, 130, 246, 0.8)", "rgba(16, 185, 129, 0.8)",
            "rgba(139, 92, 246, 0.8)", "rgba(245, 158, 11, 0.8)",
            "rgba(239, 68, 68, 0.8)", "rgba(14, 165, 233, 0.8)"
        ]
    }
    
    def recommend(self, data: List[Dict], columns: List[Dict], question: str) -> Dict[str, Any]:
        if not data or not columns:
            return self._no_chart_needed("No data available")
        
        row_count = len(data)
        col_count = len(columns)
        
        date_cols, measure_cols, dim_cols = [], [], []
        for col in columns:
            col_name = col["name"]
            col_type = col.get("type", "unknown")
            if col_type == "date" or self._looks_like_date(col_name, data):
                date_cols.append(col_name)
            elif col_type == "measure" or self._looks_like_measure(col_name, data):
                measure_cols.append(col_name)
            else:
                dim_cols.append(col_name)
        
        if row_count == 1:
            return self._recommend_metric_card(data, columns)
        
        if row_count > 100:
            return self._recommend_table(data, columns, f"Large dataset ({row_count} rows). Showing table view.")
        
        intent = self._detect_intent(question)
        
        if intent == "trend" and date_cols:
            return self._recommend_line_chart(data, date_cols, measure_cols, dim_cols)
        if intent == "distribution" and measure_cols:
            return self._recommend_histogram(data, measure_cols[0])
        if intent == "correlation" and len(measure_cols) >= 2:
            return self._recommend_scatter(data, measure_cols[0], measure_cols[1])
        if intent == "composition" and dim_cols and measure_cols:
            unique_dims = len(set(str(row.get(dim_cols[0])) for row in data))
            if unique_dims <= 8:
                return self._recommend_doughnut_chart(data, dim_cols[0], measure_cols[0])
        
        if date_cols and measure_cols:
            return self._recommend_line_chart(data, date_cols, measure_cols, dim_cols)
        
        if dim_cols and measure_cols:
            unique_dims = len(set(str(row.get(dim_cols[0])) for row in data))
            if unique_dims <= 6:
                return self._recommend_bar_chart(data, dim_cols[0], measure_cols[0])
            elif unique_dims <= 15:
                return self._recommend_horizontal_bar(data, dim_cols[0], measure_cols[0])
            else:
                return self._recommend_table(data, columns, f"Too many categories ({unique_dims})")
        
        if measure_cols and len(measure_cols) >= 2:
            return self._recommend_multi_measure_bar(data, measure_cols)
        
        return self._recommend_table(data, columns, "No clear chart pattern detected")
    
    def _detect_intent(self, question: str) -> Optional[str]:
        question_lower = question.lower()
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question_lower):
                    return intent
        return None
    
    def _looks_like_date(self, col_name: str, data: List[Dict]) -> bool:
        date_keywords = ['date', 'time', 'day', 'month', 'year', 'week', 'period']
        if any(kw in col_name.lower() for kw in date_keywords):
            return True
        sample = [str(data[i].get(col_name, '')) for i in range(min(5, len(data)))]
        date_patterns = [r'\d{4}-\d{2}-\d{2}', r'\d{2}/\d{2}/\d{4}']
        for val in sample:
            for pattern in date_patterns:
                if re.match(pattern, val):
                    return True
        return False
    
    def _looks_like_measure(self, col_name: str, data: List[Dict]) -> bool:
        measure_keywords = ['amount', 'price', 'cost', 'revenue', 'sales', 'total', 'sum', 'count', 'quantity', 'value']
        if any(kw in col_name.lower() for kw in measure_keywords):
            return True
        numeric_count = sum(1 for row in data[:10] if isinstance(row.get(col_name), (int, float)))
        return numeric_count > 5
    
    def _recommend_line_chart(self, data: List[Dict], date_cols: List[str], measure_cols: List[str], dim_cols: List[str]) -> Dict[str, Any]:
        x_col = date_cols[0] if date_cols else (dim_cols[0] if dim_cols else None)
        y_col = measure_cols[0] if measure_cols else None
        if not x_col or not y_col:
            return self._recommend_table(data, [], "Insufficient columns for line chart")
        sorted_data = sorted(data, key=lambda r: str(r.get(x_col, '')))
        labels = [str(row.get(x_col, "")) for row in sorted_data]
        values = [row.get(y_col) for row in sorted_data]
        datasets = [{"label": self._format_label(y_col), "data": values, "borderColor": self.COLORS["primary_line"], "backgroundColor": self.COLORS["primary_fill"], "fill": True, "tension": 0.1, "pointRadius": 3}]
        if len(measure_cols) >= 2:
            y_col2 = measure_cols[1]
            values2 = [row.get(y_col2) for row in sorted_data]
            datasets.append({"label": self._format_label(y_col2), "data": values2, "borderColor": "rgb(16, 185, 129)", "backgroundColor": "rgba(16, 185, 129, 0.1)", "fill": False, "tension": 0.1})
        return {
            "chart_type": "line",
            "config": {"type": "line", "data": {"labels": labels, "datasets": datasets}, "options": {"responsive": True, "plugins": {"legend": {"display": len(datasets) > 1}}, "scales": {"y": {"beginAtZero": False}}, "interaction": {"intersect": False, "mode": "index"}}},
            "reasoning": f"Line chart for time series: {x_col} → {y_col}",
            "alternatives": ["area", "bar"],
            "x_column": x_col, "y_column": y_col
        }
    
    def _recommend_bar_chart(self, data: List[Dict], x_col: str, y_col: str) -> Dict[str, Any]:
        sorted_data = sorted(data, key=lambda r: float(r.get(y_col, 0) or 0), reverse=True)
        labels = [str(row.get(x_col, ""))[:20] for row in sorted_data]
        values = [row.get(y_col) for row in sorted_data]
        return {
            "chart_type": "bar",
            "config": {"type": "bar", "data": {"labels": labels, "datasets": [{"label": self._format_label(y_col), "data": values, "backgroundColor": self.COLORS["primary"], "borderRadius": 4}]}, "options": {"responsive": True, "plugins": {"legend": {"display": False}}, "scales": {"y": {"beginAtZero": True}}}},
            "reasoning": f"Bar chart for category comparison: {x_col} by {y_col}",
            "alternatives": ["horizontal_bar"],
            "x_column": x_col, "y_column": y_col
        }
    
    def _recommend_horizontal_bar(self, data: List[Dict], x_col: str, y_col: str) -> Dict[str, Any]:
        sorted_data = sorted(data, key=lambda r: float(r.get(y_col, 0) or 0), reverse=True)[:15]
        labels = [str(row.get(x_col, ""))[:25] for row in sorted_data]
        values = [row.get(y_col) for row in sorted_data]
        return {
            "chart_type": "bar",
            "config": {"type": "bar", "data": {"labels": labels, "datasets": [{"label": self._format_label(y_col), "data": values, "backgroundColor": self.COLORS["primary"], "borderRadius": 4}]}, "options": {"indexAxis": "y", "responsive": True, "plugins": {"legend": {"display": False}}}},
            "reasoning": f"Horizontal bar chart ({len(data)} categories, showing top 15)",
            "alternatives": ["table"],
            "x_column": x_col, "y_column": y_col
        }
    
    def _recommend_histogram(self, data: List[Dict], measure_col: str) -> Dict[str, Any]:
        values = [float(row.get(measure_col)) for row in data if row.get(measure_col) is not None]
        if not values:
            return self._recommend_table(data, [], "No numeric values for histogram")
        min_val, max_val = min(values), max(values)
        bin_count = min(10, len(set(values)))
        if bin_count < 2:
            return self._recommend_table(data, [], "Insufficient variance for histogram")
        bin_width = (max_val - min_val) / bin_count if bin_count > 0 else 1
        bins = {}
        for v in values:
            bin_idx = min(int((v - min_val) / bin_width), bin_count - 1) if bin_width > 0 else 0
            bin_start = min_val + bin_idx * bin_width
            bin_label = f"{bin_start:.0f}-{bin_start + bin_width:.0f}"
            bins[bin_label] = bins.get(bin_label, 0) + 1
        sorted_bins = sorted(bins.items(), key=lambda x: float(x[0].split('-')[0]))
        labels = [b[0] for b in sorted_bins]
        counts = [b[1] for b in sorted_bins]
        return {
            "chart_type": "bar",
            "config": {"type": "bar", "data": {"labels": labels, "datasets": [{"label": "Frequency", "data": counts, "backgroundColor": self.COLORS["secondary"]}]}, "options": {"responsive": True, "plugins": {"legend": {"display": False}, "title": {"display": True, "text": f"Distribution of {self._format_label(measure_col)}"}}}},
            "reasoning": f"Histogram for distribution of {measure_col}",
            "alternatives": ["box"],
            "measure_column": measure_col
        }
    
    def _recommend_scatter(self, data: List[Dict], x_col: str, y_col: str) -> Dict[str, Any]:
        points = [{"x": float(row.get(x_col)), "y": float(row.get(y_col))} for row in data if row.get(x_col) is not None and row.get(y_col) is not None]
        if len(points) < 3:
            return self._recommend_table(data, [], "Insufficient points for scatter")
        return {
            "chart_type": "scatter",
            "config": {"type": "scatter", "data": {"datasets": [{"label": f"{x_col} vs {y_col}", "data": points, "backgroundColor": self.COLORS["tertiary"], "pointRadius": 5}]}, "options": {"responsive": True, "scales": {"x": {"title": {"display": True, "text": x_col}}, "y": {"title": {"display": True, "text": y_col}}}}},
            "reasoning": f"Scatter plot for correlation: {x_col} vs {y_col}",
            "alternatives": ["line"],
            "x_column": x_col, "y_column": y_col
        }
    
    def _recommend_multi_measure_bar(self, data: List[Dict], measure_cols: List[str]) -> Dict[str, Any]:
        if len(data) == 1:
            row = data[0]
            labels = [self._format_label(col) for col in measure_cols[:6]]
            values = [row.get(col, 0) for col in measure_cols[:6]]
            return {
                "chart_type": "bar",
                "config": {"type": "bar", "data": {"labels": labels, "datasets": [{"label": "Values", "data": values, "backgroundColor": self.COLORS["palette"][:len(labels)]}]}, "options": {"responsive": True, "plugins": {"legend": {"display": False}}}},
                "reasoning": "Bar chart comparing multiple metrics",
                "alternatives": ["table"]
            }
        return self._recommend_table(data, [], "Multiple measures comparison")
    
    def _recommend_doughnut_chart(self, data: List[Dict], dim_col: str, measure_col: str) -> Dict[str, Any]:
        """Recommend a doughnut chart for composition/share queries."""
        # Sort by measure value descending
        sorted_data = sorted(data, key=lambda r: float(r.get(measure_col, 0) or 0), reverse=True)[:8]
        labels = [str(row.get(dim_col, ""))[:20] for row in sorted_data]
        values = [row.get(measure_col, 0) for row in sorted_data]
        
        # Calculate total for percentage display
        total = sum(v for v in values if v is not None)
        
        return {
            "chart_type": "doughnut",
            "config": {
                "type": "doughnut",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "data": values,
                        "backgroundColor": self.COLORS["palette"][:len(labels)],
                        "borderWidth": 2,
                        "borderColor": "#ffffff"
                    }]
                },
                "options": {
                    "responsive": True,
                    "cutout": "60%",
                    "plugins": {
                        "legend": {
                            "display": True,
                            "position": "right"
                        },
                        "tooltip": {
                            "callbacks": {
                                "label": f"Shows percentage of total ({total:,.0f})"
                            }
                        }
                    }
                }
            },
            "reasoning": f"Doughnut chart for composition: {dim_col} share of {measure_col}",
            "alternatives": ["pie", "bar"],
            "x_column": dim_col,
            "y_column": measure_col
        }
    
    def _recommend_pie_chart(self, data: List[Dict], dim_col: str, measure_col: str) -> Dict[str, Any]:
        """Recommend a pie chart for simple composition queries."""
        sorted_data = sorted(data, key=lambda r: float(r.get(measure_col, 0) or 0), reverse=True)[:6]
        labels = [str(row.get(dim_col, ""))[:20] for row in sorted_data]
        values = [row.get(measure_col, 0) for row in sorted_data]
        
        return {
            "chart_type": "pie",
            "config": {
                "type": "pie",
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "data": values,
                        "backgroundColor": self.COLORS["palette"][:len(labels)],
                        "borderWidth": 2,
                        "borderColor": "#ffffff"
                    }]
                },
                "options": {
                    "responsive": True,
                    "plugins": {
                        "legend": {
                            "display": True,
                            "position": "right"
                        }
                    }
                }
            },
            "reasoning": f"Pie chart for composition: {dim_col} distribution",
            "alternatives": ["doughnut", "bar"],
            "x_column": dim_col,
            "y_column": measure_col
        }
    
    def _recommend_metric_card(self, data: List[Dict], columns: List[Dict]) -> Dict[str, Any]:
        row = data[0]
        metrics = [{"label": self._format_label(col["name"]), "value": row.get(col["name"])} for col in columns if row.get(col["name"]) is not None]
        return {"chart_type": "metric", "config": {"metrics": metrics}, "reasoning": "Single value result - display as metric card", "alternatives": []}
    
    def _recommend_table(self, data: List[Dict], columns: List[Dict], reason: str) -> Dict[str, Any]:
        col_names = [c["name"] for c in columns] if columns else list(data[0].keys()) if data else []
        return {"chart_type": "table", "config": {"columns": col_names, "data": data[:100]}, "reasoning": reason, "alternatives": [], "row_count": len(data)}
    
    def _no_chart_needed(self, reason: str) -> Dict[str, Any]:
        return {"chart_type": "none", "config": None, "reasoning": reason, "alternatives": []}
    
    def _format_label(self, name: str) -> str:
        return name.replace('_', ' ').title()
