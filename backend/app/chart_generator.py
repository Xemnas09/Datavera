from typing import List, Dict, Any, Tuple, Optional

def generate_echarts_options(
    question: str,
    results: List[Dict[str, Any]],
    columns: List[str]
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Analyzes SQL query output and generates an ECharts options object.
    Returns: (chart_recommended, chart_type, chart_options)
    """
    if not results or not columns:
        return False, "table", None

    if len(results) < 1 or len(columns) < 2:
        return False, "table", None

    # Inspect column types from first row
    first_row = results[0]
    string_cols = []
    numeric_cols = []
    date_cols = []

    for col in columns:
        val = first_row.get(col)
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            numeric_cols.append(col)
        elif isinstance(val, str) and any(d in col.lower() for d in ['date', 'time', 'annee', 'mois', 'day', 'dt']):
            date_cols.append(col)
        else:
            string_cols.append(col)

    if not numeric_cols:
        return False, "table", None

    row_count = len(results)
    q_lower = question.lower()

    # 1. Line chart for Time Series (date column + numeric column)
    if date_cols and numeric_cols:
        x_col = date_cols[0]
        y_col = numeric_cols[0]
        x_data = [str(r.get(x_col, '')) for r in results]
        y_data = [r.get(y_col, 0) for r in results]

        options = {
            "title": {"text": f"{y_col} par {x_col}", "left": "center", "textStyle": {"fontSize": 14}},
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "3%", "right": "4%", "bottom": "10%", "top": "15%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data, "name": x_col},
            "yAxis": {"type": "value", "name": y_col},
            "series": [{
                "name": y_col,
                "type": "line",
                "smooth": True,
                "data": y_data,
                "itemStyle": {"color": "#3b82f6"},
                "areaStyle": {"opacity": 0.1}
            }]
        }
        return True, "line", options

    # 2. Pie chart if explicit pie/repartition intent AND small category count
    wants_pie = any(w in q_lower for w in ["part", "pourcentage", "proportion", "repartition", "répartition", "camembert", "pie"])
    if wants_pie and string_cols and len(numeric_cols) == 1 and 2 <= row_count <= 10:
        cat_col = string_cols[0]
        num_col = numeric_cols[0]
        pie_data = [{"name": str(r.get(cat_col, 'N/A')), "value": r.get(num_col, 0)} for r in results]

        options = {
            "title": {"text": f"Répartition de {num_col} par {cat_col}", "left": "center", "textStyle": {"fontSize": 14}},
            "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
            "legend": {"orient": "horizontal", "bottom": "bottom"},
            "series": [{
                "name": num_col,
                "type": "pie",
                "radius": "60%",
                "center": ["50%", "45%"],
                "data": pie_data,
                "emphasis": {
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }]
        }
        return True, "pie", options

    # 3. Bar chart for Categorical comparison (string column + 1 or more numeric columns)
    if string_cols and numeric_cols:
        cat_col = string_cols[0]
        x_data = [str(r.get(cat_col, '')) for r in results[:30]] # Limit to top 30 categories for readability
        series = []

        colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"]
        for idx, num_col in enumerate(numeric_cols[:3]): # Up to 3 series
            y_data = [r.get(num_col, 0) for r in results[:30]]
            series.append({
                "name": num_col,
                "type": "bar",
                "data": y_data,
                "itemStyle": {"color": colors[idx % len(colors)]}
            })

        options = {
            "title": {"text": f"Comparaison par {cat_col}", "left": "center", "textStyle": {"fontSize": 14}},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"top": "8%"},
            "grid": {"left": "3%", "right": "4%", "bottom": "10%", "top": "20%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data, "name": cat_col, "axisLabel": {"rotate": 30 if row_count > 8 else 0}},
            "yAxis": {"type": "value"},
            "series": series
        }
        return True, "bar", options

    # 4. Scatter plot if 2 numeric columns and no categorical column
    if len(numeric_cols) >= 2 and not string_cols:
        col_x = numeric_cols[0]
        col_y = numeric_cols[1]
        scatter_data = [[r.get(col_x, 0), r.get(col_y, 0)] for r in results]

        options = {
            "title": {"text": f"Relation entre {col_x} et {col_y}", "left": "center", "textStyle": {"fontSize": 14}},
            "tooltip": {"trigger": "item", "formatter": f"{col_x}: {{c}}[0]<br/>{col_y}: {{c}}[1]"},
            "xAxis": {"type": "value", "name": col_x},
            "yAxis": {"type": "value", "name": col_y},
            "grid": {"left": "3%", "right": "4%", "bottom": "10%", "top": "15%", "containLabel": True},
            "series": [{
                "type": "scatter",
                "symbolSize": 10,
                "data": scatter_data,
                "itemStyle": {"color": "#6366f1"}
            }]
        }
        return True, "scatter", options

    return False, "table", None
