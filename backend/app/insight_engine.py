"""
Insight Engine with Complete Fallback Logic
Detects non-obvious patterns, changes, and anomalies in query results.
Zero external dependencies beyond Python standard library.
"""

from typing import Dict, List, Any, Optional, Tuple
import math


class InsightEngine:
    """
    Detects actionable insights from query results.
    Fully self-contained with no external dependencies.
    """
    
    NOISE_THRESHOLD = 0.05
    MIN_SAMPLE_SIZE = 30
    MAX_CV_THRESHOLD = 1.5
    
    def detect_insights(self, data: List[Dict], columns: List[Dict], question: str) -> List[Dict[str, Any]]:
        if not data:
            return []
        
        insights = []
        measure_cols = [c["name"] for c in columns if c.get("type") == "measure"]
        date_cols = [c["name"] for c in columns if c.get("type") == "date"]
        dim_cols = [c["name"] for c in columns if c.get("type") == "dimension"]
        
        if not measure_cols and not dim_cols:
            measure_cols, dim_cols, date_cols = self._infer_column_types(data, columns)
        
        try:
            insights.extend(self._detect_trend_changes(data, measure_cols, date_cols))
        except:
            pass
        try:
            insights.extend(self._detect_outliers(data, measure_cols))
        except:
            pass
        try:
            insights.extend(self._detect_concentration(data, measure_cols, dim_cols))
        except:
            pass
        try:
            insights.extend(self._detect_statistical_summary(data, measure_cols))
        except:
            pass
        try:
            insights.extend(self._detect_patterns(data, measure_cols, dim_cols))
        except:
            pass
        
        priority_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
        
        seen = set()
        unique_insights = []
        for insight in insights:
            key = (insight.get("type"), insight.get("title", "")[:50])
            if key not in seen:
                seen.add(key)
                unique_insights.append(insight)
        
        return unique_insights[:5]
    
    def _infer_column_types(self, data: List[Dict], columns: List[Dict]) -> Tuple[List[str], List[str], List[str]]:
        measures, dimensions, dates = [], [], []
        for col in columns:
            col_name = col["name"]
            values = [row.get(col_name) for row in data[:100] if row.get(col_name) is not None]
            if not values:
                dimensions.append(col_name)
                continue
            numeric_count = sum(1 for v in values if isinstance(v, (int, float)))
            if numeric_count / len(values) > 0.8:
                unique_ratio = len(set(values)) / len(values)
                if unique_ratio > 0.3:
                    measures.append(col_name)
                else:
                    dimensions.append(col_name)
            else:
                date_keywords = ['date', 'time', 'created', 'updated', 'day', 'month', 'year']
                if any(kw in col_name.lower() for kw in date_keywords):
                    dates.append(col_name)
                else:
                    dimensions.append(col_name)
        return measures, dimensions, dates
    
    def _safe_mean(self, values: List[float]) -> float:
        return sum(values) / len(values) if values else 0
    
    def _safe_stdev(self, values: List[float]) -> float:
        if len(values) < 2:
            return 0
        mean = self._safe_mean(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
    
    def _detect_trend_changes(self, data: List[Dict], measure_cols: List[str], date_cols: List[str]) -> List[Dict]:
        insights = []
        if not measure_cols or len(data) < 2:
            return insights
        for measure in measure_cols:
            values = []
            for row in data:
                val = row.get(measure)
                if val is not None:
                    try:
                        values.append(float(val))
                    except:
                        continue
            if len(values) < 2:
                continue
            current, previous = values[-1], values[-2]
            if previous != 0:
                pct_change = (current - previous) / abs(previous)
                if abs(pct_change) >= self.NOISE_THRESHOLD:
                    direction = "increased" if pct_change > 0 else "decreased"
                    insights.append({
                        "type": "trend_change",
                        "title": f"{self._format_column_name(measure)} {direction} {abs(pct_change)*100:.1f}%",
                        "description": f"Changed from {self._format_number(previous)} to {self._format_number(current)}",
                        "magnitude": pct_change,
                        "confidence": self._calculate_confidence(values),
                        "priority": "high" if abs(pct_change) > 0.15 else "medium",
                        "metric": measure
                    })
            if len(values) >= 5:
                first_half = self._safe_mean(values[:len(values)//2])
                second_half = self._safe_mean(values[len(values)//2:])
                if first_half != 0:
                    overall_change = (second_half - first_half) / abs(first_half)
                    if abs(overall_change) >= self.NOISE_THRESHOLD * 2:
                        direction = "upward" if overall_change > 0 else "downward"
                        insights.append({
                            "type": "trend_direction",
                            "title": f"Overall {direction} trend in {self._format_column_name(measure)}",
                            "description": f"Average changed from {self._format_number(first_half)} to {self._format_number(second_half)} ({overall_change*100:+.1f}%)",
                            "magnitude": overall_change,
                            "confidence": self._calculate_confidence(values),
                            "priority": "medium",
                            "metric": measure
                        })
        return insights
    
    def _detect_outliers(self, data: List[Dict], measure_cols: List[str]) -> List[Dict]:
        insights = []
        for measure in measure_cols:
            values = []
            for row in data:
                val = row.get(measure)
                if val is not None:
                    try:
                        values.append((float(val), row))
                    except:
                        continue
            if len(values) < self.MIN_SAMPLE_SIZE:
                continue
            nums = [v[0] for v in values]
            mean = self._safe_mean(nums)
            std = self._safe_stdev(nums)
            if std == 0:
                continue
            outliers = [(v, row) for v, row in values if abs(v - mean) > 2 * std]
            if outliers:
                outlier_pct = len(outliers) / len(values) * 100
                max_outlier = max(outliers, key=lambda x: abs(x[0] - mean))
                insights.append({
                    "type": "outlier",
                    "title": f"{len(outliers)} outlier{'s' if len(outliers) > 1 else ''} in {self._format_column_name(measure)}",
                    "description": f"{outlier_pct:.1f}% of values are >2σ from mean. Most extreme: {self._format_number(max_outlier[0])}",
                    "magnitude": outlier_pct / 100,
                    "confidence": 0.9 if len(values) >= 100 else 0.7,
                    "priority": "medium" if outlier_pct < 5 else "high",
                    "metric": measure
                })
        return insights
    
    def _detect_concentration(self, data: List[Dict], measure_cols: List[str], dim_cols: List[str]) -> List[Dict]:
        insights = []
        if not measure_cols or not dim_cols:
            return insights
        measure = measure_cols[0]
        for dim in dim_cols:
            totals = {}
            for row in data:
                dim_val, measure_val = row.get(dim), row.get(measure)
                if dim_val is not None and measure_val is not None:
                    try:
                        totals[str(dim_val)] = totals.get(str(dim_val), 0) + float(measure_val)
                    except:
                        continue
            if len(totals) < 2:
                continue
            total_sum = sum(totals.values())
            if total_sum == 0:
                continue
            sorted_items = sorted(totals.items(), key=lambda x: x[1], reverse=True)
            sorted_vals = [v for _, v in sorted_items]
            top1_pct = sorted_vals[0] / total_sum
            if top1_pct >= 0.5:
                top_category = sorted_items[0][0]
                insights.append({
                    "type": "concentration",
                    "title": f"High concentration: '{top_category}' = {top1_pct*100:.0f}%",
                    "description": f"Single {self._format_column_name(dim)} accounts for over half of {self._format_column_name(measure)}",
                    "magnitude": top1_pct,
                    "confidence": 0.95,
                    "priority": "high",
                    "dimension": dim
                })
            elif len(sorted_vals) >= 5:
                cumsum = 0
                for i, val in enumerate(sorted_vals):
                    cumsum += val
                    if cumsum / total_sum >= 0.8:
                        pct_of_categories = (i + 1) / len(sorted_vals) * 100
                        if pct_of_categories <= 25:
                            insights.append({
                                "type": "pareto",
                                "title": f"Pareto pattern: {i+1} of {len(sorted_vals)} {self._format_column_name(dim)}s = 80%",
                                "description": f"Top {pct_of_categories:.0f}% of categories drive 80% of {self._format_column_name(measure)}",
                                "magnitude": 0.8,
                                "confidence": 0.9,
                                "priority": "medium",
                                "dimension": dim
                            })
                        break
        return insights
    
    def _detect_patterns(self, data: List[Dict], measure_cols: List[str], dim_cols: List[str]) -> List[Dict]:
        insights = []
        if not measure_cols or not dim_cols or len(data) < 10:
            return insights
        measure = measure_cols[0]
        for dim in dim_cols[:2]:
            category_stats = {}
            for row in data:
                dim_val, measure_val = row.get(dim), row.get(measure)
                if dim_val is not None and measure_val is not None:
                    try:
                        key = str(dim_val)
                        if key not in category_stats:
                            category_stats[key] = []
                        category_stats[key].append(float(measure_val))
                    except:
                        continue
            if len(category_stats) < 2:
                continue
            averages = {k: self._safe_mean(v) for k, v in category_stats.items() if v}
            if not averages:
                continue
            overall_avg = self._safe_mean([v for vals in category_stats.values() for v in vals])
            if overall_avg == 0:
                continue
            for cat, avg in averages.items():
                deviation = (avg - overall_avg) / overall_avg
                if abs(deviation) > 0.3 and len(category_stats[cat]) >= 5:
                    direction = "above" if deviation > 0 else "below"
                    insights.append({
                        "type": "category_deviation",
                        "title": f"'{cat}' is {abs(deviation)*100:.0f}% {direction} average",
                        "description": f"{self._format_column_name(dim)} '{cat}' has avg {self._format_column_name(measure)} of {self._format_number(avg)} vs overall {self._format_number(overall_avg)}",
                        "magnitude": deviation,
                        "confidence": min(0.9, len(category_stats[cat]) / 50),
                        "priority": "medium" if abs(deviation) < 0.5 else "high",
                        "dimension": dim,
                        "category": cat
                    })
        return insights
    
    def _detect_statistical_summary(self, data: List[Dict], measure_cols: List[str]) -> List[Dict]:
        insights = []
        for measure in measure_cols:
            values = []
            for row in data:
                val = row.get(measure)
                if val is not None:
                    try:
                        values.append(float(val))
                    except:
                        continue
            if not values:
                continue
            n = len(values)
            mean = self._safe_mean(values)
            if n < self.MIN_SAMPLE_SIZE:
                insights.append({
                    "type": "sample_size",
                    "title": f"Small sample: {n} records",
                    "description": f"Results for {self._format_column_name(measure)} may be unreliable. Need ≥{self.MIN_SAMPLE_SIZE} for stable patterns.",
                    "magnitude": n / self.MIN_SAMPLE_SIZE,
                    "confidence": 0.5,
                    "priority": "low",
                    "metric": measure
                })
            if n >= 2:
                std = self._safe_stdev(values)
                cv = std / abs(mean) if mean != 0 else 0
                if cv > self.MAX_CV_THRESHOLD:
                    insights.append({
                        "type": "volatility",
                        "title": f"High variance in {self._format_column_name(measure)}",
                        "description": f"Coefficient of variation: {cv:.2f}. Consider segmenting analysis.",
                        "magnitude": cv,
                        "confidence": 0.8,
                        "priority": "low",
                        "metric": measure
                    })
        return insights
    
    def _calculate_confidence(self, values: List[float]) -> float:
        n = len(values)
        if n < 10:
            return 0.4
        elif n < self.MIN_SAMPLE_SIZE:
            return 0.6
        elif n < 100:
            return 0.8
        return 0.9
    
    def _format_number(self, value: float) -> str:
        if abs(value) >= 1_000_000:
            return f"{value/1_000_000:.1f}M"
        elif abs(value) >= 1_000:
            return f"{value/1_000:.1f}K"
        elif abs(value) < 1:
            return f"{value:.3f}"
        return f"{value:,.2f}"
    
    def _format_column_name(self, name: str) -> str:
        return name.replace('_', ' ').title()
