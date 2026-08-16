import math
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from app.column_classifier import ColumnClassification, validate_chart_config, ChartValidationResult

def build_echarts_for_config(
    df: pd.DataFrame,
    chart_type: str,
    mapping: Dict[str, str],
    classifications: Dict[str, ColumnClassification]
) -> Dict[str, Any]:
    """
    Builds an ECharts options dictionary for any of the 16 supported chart types.
    """
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#6366f1", "#f43f5e"]

    # --- 1. Bar Charts ---
    if chart_type in ["bar", "bar_sorted"]:
        x_col = mapping.get("x") or list(mapping.values())[0]
        y_col = mapping.get("y") or (list(mapping.values())[1] if len(mapping) > 1 else x_col)

        sub_df = df.dropna(subset=[x_col, y_col]).head(50)
        if chart_type == "bar_sorted":
            sub_df = sub_df.sort_values(by=y_col, ascending=False)

        x_data = [str(v) for v in sub_df[x_col].tolist()]
        y_data = [float(v) if isinstance(v, (int, float)) and not math.isnan(v) else 0.0 for v in sub_df[y_col].tolist()]

        return {
            "title": {"text": f"{y_col} par {x_col}", "left": "center", "textStyle": {"fontSize": 14}},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "15%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data, "name": x_col, "axisLabel": {"rotate": 30 if len(x_data) > 8 else 0}},
            "yAxis": {"type": "value", "name": y_col},
            "series": [{"name": y_col, "type": "bar", "data": y_data, "itemStyle": {"color": colors[0]}}]
        }

    if chart_type in ["bar_grouped", "bar_stacked", "bar_100pct"]:
        x_col = mapping.get("x")
        y_col = mapping.get("y")
        color_col = mapping.get("color") or mapping.get("group")
        cols = [c for c in [x_col, y_col, color_col] if c]

        sub_df = df.dropna(subset=cols)
        pivot = sub_df.pivot_table(index=x_col, columns=color_col, values=y_col, aggfunc="sum").fillna(0)

        if chart_type == "bar_100pct":
            row_sums = pivot.sum(axis=1)
            pivot = pivot.div(row_sums.replace(0, 1), axis=0) * 100

        x_data = [str(v) for v in pivot.index.tolist()]
        series = []
        is_stacked = chart_type in ["bar_stacked", "bar_100pct"]

        for idx, col in enumerate(pivot.columns):
            series.append({
                "name": str(col),
                "type": "bar",
                "stack": "total" if is_stacked else None,
                "data": [float(v) for v in pivot[col].tolist()],
                "itemStyle": {"color": colors[idx % len(colors)]}
            })

        return {
            "title": {"text": f"{y_col} par {x_col} et {color_col}", "left": "center", "textStyle": {"fontSize": 14}},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"top": "8%"},
            "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "20%", "containLabel": True},
            "xAxis": {"type": "category", "data": x_data, "name": x_col},
            "yAxis": {"type": "value", "max": 100 if chart_type == "bar_100pct" else None},
            "series": series
        }

    # --- 2. Histogram ---
    if chart_type == "histogram":
        val_col = mapping.get("x") or list(mapping.values())[0]
        vals = pd.to_numeric(df[val_col], errors="coerce").dropna().tolist()

        if not vals:
            counts, bin_edges = [0], [0, 1]
        else:
            counts, bin_edges = pd.cut(vals, bins=10, retbins=True, labels=False), None
            # Compute manually
            min_v, max_v = min(vals), max(vals)
            step = (max_v - min_v) / 10 if max_v > min_v else 1
            bin_labels = [f"{round(min_v + i*step, 1)}-{round(min_v + (i+1)*step, 1)}" for i in range(10)]
            bin_counts = [0] * 10
            for v in vals:
                idx = min(int((v - min_v) / step), 9) if step > 0 else 0
                bin_counts[idx] += 1

        return {
            "title": {"text": f"Distribution de {val_col}", "left": "center", "textStyle": {"fontSize": 14}},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "15%", "containLabel": True},
            "xAxis": {"type": "category", "data": bin_labels, "name": val_col, "axisLabel": {"rotate": 30}},
            "yAxis": {"type": "value", "name": "Fréquence"},
            "series": [{"type": "bar", "data": bin_counts, "itemStyle": {"color": colors[1]}}]
        }

    # --- 3. Line & Area Charts ---
    if chart_type in ["line", "area", "area_stacked"]:
        x_col = mapping.get("x") or list(mapping.values())[0]
        y_col = mapping.get("y") or (list(mapping.values())[1] if len(mapping) > 1 else x_col)
        color_col = mapping.get("color")

        if color_col and color_col in df.columns:
            pivot = df.pivot_table(index=x_col, columns=color_col, values=y_col, aggfunc="mean").fillna(0)
            x_data = [str(v) for v in pivot.index.tolist()]
            series = []
            for idx, col in enumerate(pivot.columns):
                s_item = {
                    "name": str(col),
                    "type": "line",
                    "smooth": True,
                    "data": [float(v) for v in pivot[col].tolist()],
                    "itemStyle": {"color": colors[idx % len(colors)]}
                }
                if "area" in chart_type:
                    s_item["areaStyle"] = {"opacity": 0.3}
                if chart_type == "area_stacked":
                    s_item["stack"] = "total"
                series.append(s_item)

            return {
                "title": {"text": f"Évolution de {y_col} par {x_col}", "left": "center", "textStyle": {"fontSize": 14}},
                "tooltip": {"trigger": "axis"},
                "legend": {"top": "8%"},
                "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "20%", "containLabel": True},
                "xAxis": {"type": "category", "data": x_data, "name": x_col},
                "yAxis": {"type": "value"},
                "series": series
            }
        else:
            sub_df = df.dropna(subset=[x_col, y_col]).sort_values(by=x_col).head(100)
            x_data = [str(v) for v in sub_df[x_col].tolist()]
            y_data = [float(v) for v in sub_df[y_col].tolist()]

            s_item = {
                "name": y_col,
                "type": "line",
                "smooth": True,
                "data": y_data,
                "itemStyle": {"color": colors[0]}
            }
            if "area" in chart_type:
                s_item["areaStyle"] = {"opacity": 0.2}

            return {
                "title": {"text": f"Évolution de {y_col} par {x_col}", "left": "center", "textStyle": {"fontSize": 14}},
                "tooltip": {"trigger": "axis"},
                "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "15%", "containLabel": True},
                "xAxis": {"type": "category", "data": x_data, "name": x_col},
                "yAxis": {"type": "value", "name": y_col},
                "series": [s_item]
            }

    # --- 4. Pie & Donut Charts ---
    if chart_type in ["pie", "donut", "treemap"]:
        cat_col = mapping.get("category") or mapping.get("x") or list(mapping.values())[0]
        val_col = mapping.get("value") or mapping.get("y") or list(mapping.values())[1]

        sub_df = df.groupby(cat_col)[val_col].sum().reset_index().head(10)
        chart_data = [{"name": str(r[cat_col]), "value": float(r[val_col])} for _, r in sub_df.iterrows() if float(r[val_col]) >= 0]

        if chart_type == "treemap":
            return {
                "title": {"text": f"Treemap de {val_col} par {cat_col}", "left": "center", "textStyle": {"fontSize": 14}},
                "tooltip": {"trigger": "item", "formatter": "{b}: {c}"},
                "series": [{
                    "type": "treemap",
                    "data": chart_data,
                    "label": {"show": True, "formatter": "{b}"}
                }]
            }

        return {
            "title": {"text": f"Répartition de {val_col} par {cat_col}", "left": "center", "textStyle": {"fontSize": 14}},
            "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
            "legend": {"orient": "horizontal", "bottom": "bottom"},
            "series": [{
                "type": "pie",
                "radius": ["40%", "70%"] if chart_type == "donut" else "65%",
                "center": ["50%", "45%"],
                "data": chart_data
            }]
        }

    # --- 5. Scatter & Bubble ---
    if chart_type in ["scatter", "bubble"]:
        x_col = mapping.get("x") or list(mapping.values())[0]
        y_col = mapping.get("y") or list(mapping.values())[1]
        size_col = mapping.get("size") if chart_type == "bubble" else None

        cols = [c for c in [x_col, y_col, size_col] if c]
        sub_df = df.dropna(subset=cols).head(500)

        scatter_data = []
        for _, r in sub_df.iterrows():
            item = [float(r[x_col]), float(r[y_col])]
            if size_col:
                item.append(float(r[size_col]))
            scatter_data.append(item)

        return {
            "title": {"text": f"Relation entre {x_col} et {y_col}", "left": "center", "textStyle": {"fontSize": 14}},
            "tooltip": {"trigger": "item"},
            "xAxis": {"type": "value", "name": x_col},
            "yAxis": {"type": "value", "name": y_col},
            "grid": {"left": "3%", "right": "4%", "bottom": "15%", "top": "15%", "containLabel": True},
            "series": [{
                "type": "scatter",
                "data": scatter_data,
                "symbolSize": (lambda val: min(max(val[2] / 10, 8), 30)) if size_col else 10,
                "itemStyle": {"color": colors[3]}
            }]
        }

    # --- 6. Box plot & Violin ---
    if chart_type in ["box", "violin"]:
        val_col = mapping.get("y") or mapping.get("x") or list(mapping.values())[0]
        cat_col = mapping.get("x") or mapping.get("category")

        if cat_col and cat_col in df.columns:
            groups = df.groupby(cat_col)[val_col]
            categories = []
            box_data = []
            for name, group in groups:
                vals = pd.to_numeric(group, errors="coerce").dropna().sort_values().tolist()
                if len(vals) >= 4:
                    categories.append(str(name))
                    q1, med, q3 = pd.Series(vals).quantile([0.25, 0.5, 0.75]).tolist()
                    min_v, max_v = vals[0], vals[-1]
                    box_data.append([min_v, q1, med, q3, max_v])

            return {
                "title": {"text": f"Boîte à moustaches de {val_col} par {cat_col}", "left": "center", "textStyle": {"fontSize": 14}},
                "tooltip": {"trigger": "item"},
                "xAxis": {"type": "category", "data": categories, "name": cat_col},
                "yAxis": {"type": "value", "name": val_col},
                "series": [{"type": "boxplot", "data": box_data, "itemStyle": {"color": colors[0]}}]
            }
        else:
            vals = pd.to_numeric(df[val_col], errors="coerce").dropna().sort_values().tolist()
            if len(vals) >= 4:
                q1, med, q3 = pd.Series(vals).quantile([0.25, 0.5, 0.75]).tolist()
                box_data = [[vals[0], q1, med, q3, vals[-1]]]
            else:
                box_data = []

            return {
                "title": {"text": f"Boîte à moustaches de {val_col}", "left": "center", "textStyle": {"fontSize": 14}},
                "tooltip": {"trigger": "item"},
                "xAxis": {"type": "category", "data": [val_col]},
                "yAxis": {"type": "value"},
                "series": [{"type": "boxplot", "data": box_data, "itemStyle": {"color": colors[0]}}]
            }

    # --- 7. Correlation Heatmap ---
    if chart_type == "correlation_heatmap":
        num_cols = [c for c in mapping.values() if c in df.columns]
        if len(num_cols) < 2:
            num_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()[:6]

        corr_matrix = df[num_cols].corr().fillna(0)
        heatmap_data = []
        for i, col1 in enumerate(num_cols):
            for j, col2 in enumerate(num_cols):
                heatmap_data.append([i, j, round(float(corr_matrix.loc[col1, col2]), 2)])

        return {
            "title": {"text": "Matrice de Corrélation", "left": "center", "textStyle": {"fontSize": 14}},
            "tooltip": {"position": "top"},
            "grid": {"height": "65%", "top": "15%"},
            "xAxis": {"type": "category", "data": num_cols, "axisLabel": {"rotate": 30}},
            "yAxis": {"type": "category", "data": num_cols},
            "visualMap": {
                "min": -1, "max": 1, "calculable": True,
                "orient": "horizontal", "left": "center", "bottom": "0%",
                "inRange": {"color": ["#ef4444", "#f8fafc", "#3b82f6"]}
            },
            "series": [{
                "type": "heatmap",
                "data": heatmap_data,
                "label": {"show": True}
            }]
        }

    # Fallback bar chart
    cols = list(mapping.values())
    x_col = cols[0] if cols else df.columns[0]
    y_col = cols[1] if len(cols) > 1 else df.columns[1] if len(df.columns) > 1 else x_col
    sub_df = df.head(20)

    return {
        "title": {"text": f"{y_col} par {x_col}", "left": "center"},
        "xAxis": {"type": "category", "data": [str(v) for v in sub_df[x_col].tolist()]},
        "yAxis": {"type": "value"},
        "series": [{"type": "bar", "data": [float(v) if isinstance(v, (int, float)) else 0 for v in sub_df[y_col].tolist()]}]
    }

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
