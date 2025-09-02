"""
MCP Data Analysis & Visualization Service

Run with:
    uv run python main.py
"""

import os
import platform
import uuid
from datetime import datetime, timezone
from functools import wraps

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from mcp.server.fastmcp import FastMCP
from maas_client import LanyunMaaSClient, load_maas_config, DEFAULT_BASE_URL
import plotly.express as px
import plotly.io as pio

# Prepare directories for later tools
os.makedirs("data", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
os.makedirs("outputs/interactive", exist_ok=True)

SERVICE_NAME = "DataVizMCP"
SERVICE_VERSION = "0.1.0"

# Create an MCP server
mcp = FastMCP(SERVICE_NAME)

def tool_guard(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            return {
                "status": "error",
                "error": {
                    "type": e.__class__.__name__,
                    "message": str(e),
                },
            }
    return wrapper

# Health tool
@mcp.tool()
@tool_guard
def health() -> dict:
    """Service healthcheck and version info."""
    return {
        "status": "ok",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "time": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
    }

@mcp.tool()
@tool_guard
def upload_csv(data: str, delimiter: str = ",", encoding: str = "utf-8") -> dict:
    """
    Save a CSV string to data/{file_id}.csv and return identifiers.
    Note: delimiter is kept for future parsing; here we only persist the raw data.
    """
    if not isinstance(data, str) or len(data.strip()) == 0:
        raise ValueError("Empty CSV data")

    file_id = uuid.uuid4().hex
    filename = f"{file_id}.csv"
    path = os.path.join("data", filename)

    # Normalize newlines for cross-platform consistency
    content = data.replace("\r\n", "\n").replace("\r", "\n")
    with open(path, "w", encoding=encoding, newline="\n") as f:
        f.write(content)
        if not content.endswith("\n"):
            f.write("\n")

    size = os.path.getsize(path)
    return {
        "status": "saved",
        "file_id": file_id,
        "path": path,
        "size_bytes": size,
        "delimiter": delimiter,
        "encoding": encoding,
    }


@mcp.tool()
@tool_guard
def analyze_summary(file_id: str, delimiter: str = ",", encoding: str = "utf-8") -> dict:
    """
    Load data/{file_id}.csv and return row_count, columns, and numeric statistics.
    """
    if not isinstance(file_id, str) or len(file_id.strip()) == 0:
        raise ValueError("Invalid file_id")
    if any(c in file_id for c in ("/", "\\", "..")):
        raise ValueError("Invalid file_id")

    path = os.path.join("data", f"{file_id}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found for file_id={file_id}")

    try:
        df = pd.read_csv(path, sep=delimiter, encoding=encoding)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")

    row_count = int(len(df))
    columns = [{"name": str(col), "dtype": str(df[col].dtype)} for col in df.columns]

    num_df = df.select_dtypes(include="number")
    numeric_stats: dict = {}
    if not num_df.empty:
        desc = num_df.describe(include="all")
        medians = num_df.median(numeric_only=True)
        for col in num_df.columns:
            col_stats = {
                "count": (float(desc.loc["count", col]) if "count" in desc.index and pd.notna(desc.loc["count", col]) else None),
                "mean": (float(desc.loc["mean", col]) if "mean" in desc.index and pd.notna(desc.loc["mean", col]) else None),
                "std": (float(desc.loc["std", col]) if "std" in desc.index and pd.notna(desc.loc["std", col]) else None),
                "min": (float(desc.loc["min", col]) if "min" in desc.index and pd.notna(desc.loc["min", col]) else None),
                "median": (float(medians[col]) if col in medians and pd.notna(medians[col]) else None),
                "max": (float(desc.loc["max", col]) if "max" in desc.index and pd.notna(desc.loc["max", col]) else None),
            }
            numeric_stats[col] = col_stats

    return {
        "status": "ok",
        "file_id": file_id,
        "path": path,
        "row_count": row_count,
        "columns": columns,
        "numeric_stats": numeric_stats,
    }

@mcp.tool()
@tool_guard
def visualize_barchart(
    file_id: str,
    x: str,
    y: str,
    agg: str = "sum",
    delimiter: str = ",",
    encoding: str = "utf-8",
    figsize: tuple[float, float] = (8.0, 6.0),
) -> dict:
    """
    Generate a bar chart for aggregated y grouped by x.
    Supported agg: sum, mean, median, min, max, count.
    Saves a PNG under outputs/ and returns the path.
    """
    if not file_id or any(c in file_id for c in ("/", "\\", "..")):
        raise ValueError("Invalid file_id")
    if not x or not y:
        raise ValueError("x and y are required")

    path_csv = os.path.join("data", f"{file_id}.csv")
    if not os.path.exists(path_csv):
        raise FileNotFoundError(f"File not found for file_id={file_id}")

    try:
        df = pd.read_csv(path_csv, sep=delimiter, encoding=encoding)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")

    if x not in df.columns:
        raise ValueError(f"Column '{x}' not found")
    if y not in df.columns:
        raise ValueError(f"Column '{y}' not found")

    agg_lower = str(agg).lower()
    allowed = {"sum", "mean", "median", "min", "max", "count"}

    if agg_lower not in allowed:
        raise ValueError(f"Unsupported agg '{agg}'. Allowed: {sorted(list(allowed))}")

    # Prepare aggregation
    if agg_lower == "count":
        grouped = df.groupby(x)[y].count()
        y_label = f"count({y})"
    else:
        # Ensure y is numeric for numeric aggregations
        if not pd.api.types.is_numeric_dtype(df[y]):
            raise ValueError(f"Column '{y}' must be numeric for agg='{agg_lower}'")
        grouped = df.groupby(x)[y].agg(agg_lower)
        y_label = f"{agg_lower}({y})"

    # Sanitize filename components
    def _safe(s: str) -> str:
        return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(s))

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{_safe(file_id)}_{_safe(x)}_{_safe(y)}_{_safe(agg_lower)}_{ts}.png"
    out_path = os.path.join("outputs", filename)

    # Plot
    plt.figure(figsize=figsize)
    sns.barplot(x=grouped.index.astype(str), y=grouped.values)
    plt.xlabel(x)
    plt.ylabel(y_label)
    plt.title(f"{y_label} by {x}")
    plt.tight_layout()

    try:
        plt.savefig(out_path, dpi=150)
    finally:
        plt.close()

    return {
        "status": "ok",
        "file_id": file_id,
        "csv_path": path_csv,
        "chart_path": out_path,
        "x": x,
        "y": y,
        "agg": agg_lower,
        "categories": int(len(grouped)),
    }

@mcp.tool()
@tool_guard
def visualize_interactive(
    file_id: str,
    kind: str = "barchart",
    x: str = "",
    y: str | None = None,
    agg: str = "sum",
    delimiter: str = ",",
    encoding: str = "utf-8",
    include_plotlyjs: str = "cdn",
) -> dict:
    """
    Generate an interactive chart HTML via Plotly and save under outputs/interactive/.
    Supported currently: kind='barchart' with aggregation y grouped by x.
    Returns HTML path and metadata.
    """
    if not isinstance(file_id, str) or len(file_id.strip()) == 0 or any(c in file_id for c in ("/", "\\", "..")):
        raise ValueError("Invalid file_id")
    if kind not in ("barchart",):
        raise ValueError(f"Unsupported kind '{kind}'. Allowed: ['barchart']")
    if kind == "barchart":
        if not x or not y:
            raise ValueError("x and y are required for barchart")

    path_csv = os.path.join("data", f"{file_id}.csv")
    if not os.path.exists(path_csv):
        raise FileNotFoundError(f"File not found for file_id={file_id}")

    try:
        df = pd.read_csv(path_csv, sep=delimiter, encoding=encoding)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")

    def _safe(s: str) -> str:
        return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(s))

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    if kind == "barchart":
        agg_lower = str(agg).lower()
        allowed = {"sum", "mean", "median", "min", "max", "count"}
        if agg_lower not in allowed:
            raise ValueError(f"Unsupported agg '{agg}'. Allowed: {sorted(list(allowed))}")

        if x not in df.columns:
            raise ValueError(f"Column '{x}' not found")
        if y not in df.columns:
            raise ValueError(f"Column '{y}' not found")

        if agg_lower == "count":
            grouped = df.groupby(x)[y].count()
            y_label = f"count({y})"
        else:
            if not pd.api.types.is_numeric_dtype(df[y]):
                raise ValueError(f"Column '{y}' must be numeric for agg='{agg_lower}'")
            grouped = df.groupby(x)[y].agg(agg_lower)
            y_label = f"{agg_lower}({y})"

        filename = f"{_safe(file_id)}_{_safe(kind)}_{_safe(x)}_{_safe(y)}_{_safe(agg_lower)}_{ts}.html"
        out_path = os.path.join("outputs", "interactive", filename)

        fig = px.bar(
            x=grouped.index.astype(str),
            y=grouped.values,
            labels={"x": str(x), "y": y_label},
            title=f"{y_label} by {x}",
        )
        fig.update_layout(margin=dict(l=40, r=20, t=60, b=40), bargap=0.2)
        fig.write_html(out_path, include_plotlyjs=include_plotlyjs, full_html=True)

        return {
            "status": "ok",
            "file_id": file_id,
            "csv_path": path_csv,
            "kind": "barchart",
            "params": {"x": x, "y": y, "agg": agg_lower},
            "html_path": out_path,
            "categories": int(len(grouped)),
        }

@mcp.tool()
@tool_guard
def report(
    file_id: str,
    analysis: str = "summary",
    viz: dict | None = None,
    delimiter: str = ",",
    encoding: str = "utf-8",
) -> dict:
    """
    Orchestrate analysis and visualization for a given file_id.
    analysis: 'summary' | 'none'
    viz: {"kind":"barchart","x":str,"y":str,"agg":"sum|mean|median|min|max|count","figsize":[w,h]} or None
    """
    # Validate file_id and load CSV
    if not isinstance(file_id, str) or len(file_id.strip()) == 0 or any(c in file_id for c in ("/", "\\", "..")):
        raise ValueError("Invalid file_id")

    path_csv = os.path.join("data", f"{file_id}.csv")
    if not os.path.exists(path_csv):
        raise FileNotFoundError(f"File not found for file_id={file_id}")

    try:
        df = pd.read_csv(path_csv, sep=delimiter, encoding=encoding)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")

    result: dict = {
        "status": "ok",
        "file_id": file_id,
        "csv_path": path_csv,
    }

    # Analysis
    analysis_key = (analysis or "").strip().lower()
    analysis_payload = None
    if analysis_key in ("", "none"):
        analysis_payload = None
    elif analysis_key == "summary":
        row_count = int(len(df))
        columns = [{"name": str(col), "dtype": str(df[col].dtype)} for col in df.columns]

        num_df = df.select_dtypes(include="number")
        numeric_stats: dict = {}
        if not num_df.empty:
            desc = num_df.describe(include="all")
            medians = num_df.median(numeric_only=True)
            for col in num_df.columns:
                col_stats = {
                    "count": (float(desc.loc["count", col]) if "count" in desc.index and pd.notna(desc.loc["count", col]) else None),
                    "mean": (float(desc.loc["mean", col]) if "mean" in desc.index and pd.notna(desc.loc["mean", col]) else None),
                    "std": (float(desc.loc["std", col]) if "std" in desc.index and pd.notna(desc.loc["std", col]) else None),
                    "min": (float(desc.loc["min", col]) if "min" in desc.index and pd.notna(desc.loc["min", col]) else None),
                    "median": (float(medians[col]) if col in medians and pd.notna(medians[col]) else None),
                    "max": (float(desc.loc["max", col]) if "max" in desc.index and pd.notna(desc.loc["max", col]) else None),
                }
                numeric_stats[col] = col_stats

        analysis_payload = {
            "row_count": row_count,
            "columns": columns,
            "numeric_stats": numeric_stats,
        }
    else:
        raise ValueError(f"Unsupported analysis '{analysis}'. Allowed: ['summary','none']")

    result["analysis"] = analysis_payload

    # Visualization
    viz_out = None
    if viz is not None:
        if not isinstance(viz, dict):
            raise ValueError("viz must be an object when provided")

        kind = str(viz.get("kind", "")).lower()
        if kind != "barchart":
            raise ValueError(f"Unsupported viz.kind '{kind}'. Allowed: ['barchart']")

        x = viz.get("x")
        y = viz.get("y")
        if not x or not y:
            raise ValueError("viz requires 'x' and 'y' fields")

        agg = str(viz.get("agg", "sum")).lower()
        allowed = {"sum", "mean", "median", "min", "max", "count"}
        if agg not in allowed:
            raise ValueError(f"Unsupported agg '{agg}'. Allowed: {sorted(list(allowed))}")

        # figsize can be list/tuple of 2 numbers
        figsize_val = viz.get("figsize", [8, 6])
        try:
            if isinstance(figsize_val, (list, tuple)) and len(figsize_val) == 2:
                figsize = (float(figsize_val[0]), float(figsize_val[1]))
            else:
                figsize = (8.0, 6.0)
        except Exception:
            figsize = (8.0, 6.0)

        if x not in df.columns:
            raise ValueError(f"Column '{x}' not found")
        if y not in df.columns:
            raise ValueError(f"Column '{y}' not found")

        if agg == "count":
            grouped = df.groupby(x)[y].count()
            y_label = f"count({y})"
        else:
            if not pd.api.types.is_numeric_dtype(df[y]):
                raise ValueError(f"Column '{y}' must be numeric for agg='{agg}'")
            grouped = df.groupby(x)[y].agg(agg)
            y_label = f"{agg}({y})"

        # Safe filename
        def _safe(s: str) -> str:
            return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(s))

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{_safe(file_id)}_{_safe(x)}_{_safe(y)}_{_safe(agg)}_{ts}.png"
        out_path = os.path.join("outputs", filename)

        # Plot
        plt.figure(figsize=figsize)
        sns.barplot(x=grouped.index.astype(str), y=grouped.values)
        plt.xlabel(str(x))
        plt.ylabel(y_label)
        plt.title(f"{y_label} by {x}")
        plt.tight_layout()

        try:
            plt.savefig(out_path, dpi=150)
        finally:
            plt.close()

        viz_out = {
            "kind": "barchart",
            "params": {"x": x, "y": y, "agg": agg, "figsize": list(figsize)},
            "chart_path": out_path,
            "categories": int(len(grouped)),
        }

    result["viz"] = viz_out
    return result

# Demo addition tool (kept)
@mcp.tool()
@tool_guard
def generate_ai_insights(
    file_id: str,
    analysis: dict | None = None,
    viz: dict | None = None,
    delimiter: str = ",",
    encoding: str = "utf-8",
    max_chars: int = 2000,
    timeout_secs: float = 15.0,
) -> dict:
    """
    Generate AI insights via Lanyun MaaS if configured (.env), else fallback heuristics.
    Env:
      - LANYUN_API_KEY or LANYUN_MAAS_API_KEY
      - LANYUN_MAAS_BASE_URL (default: https://maas-api.lanyun.net/v1)
      - LANYUN_MODEL (default: Kimi-K2-instruct or user-provided model like /maas/deepseek-ai/DeepSeek-R1)
    """
    if not isinstance(file_id, str) or len(file_id.strip()) == 0 or any(c in file_id for c in ("/", "\\", "..")):
        raise ValueError("Invalid file_id")

    path_csv = os.path.join("data", f"{file_id}.csv")
    if not os.path.exists(path_csv):
        raise FileNotFoundError(f"File not found for file_id={file_id}")

    try:
        df = pd.read_csv(path_csv, sep=delimiter, encoding=encoding)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")

    # Prepare analysis payload if not provided
    if analysis is None:
        row_count = int(len(df))
        columns = [{"name": str(col), "dtype": str(df[col].dtype)} for col in df.columns]
        num_df = df.select_dtypes(include="number")
        numeric_stats: dict = {}
        if not num_df.empty:
            desc = num_df.describe(include="all")
            medians = num_df.median(numeric_only=True)
            for col in num_df.columns:
                col_stats = {
                    "count": (float(desc.loc["count", col]) if "count" in desc.index and pd.notna(desc.loc["count", col]) else None),
                    "mean": (float(desc.loc["mean", col]) if "mean" in desc.index and pd.notna(desc.loc["mean", col]) else None),
                    "std": (float(desc.loc["std", col]) if "std" in desc.index and pd.notna(desc.loc["std", col]) else None),
                    "min": (float(desc.loc["min", col]) if "min" in desc.index and pd.notna(desc.loc["min", col]) else None),
                    "median": (float(medians[col]) if col in medians and pd.notna(medians[col]) else None),
                    "max": (float(desc.loc["max", col]) if "max" in desc.index and pd.notna(desc.loc["max", col]) else None),
                }
                numeric_stats[col] = col_stats
        analysis_payload = {"row_count": row_count, "columns": columns, "numeric_stats": numeric_stats}
    else:
        analysis_payload = analysis

    # Optional viz summary text
    viz_summary_lines = []
    if isinstance(viz, dict):
        kind = str(viz.get("kind", ""))
        x = viz.get("x")
        y = viz.get("y")
        agg = viz.get("agg")
        viz_summary_lines.append(f"viz.kind={kind}, x={x}, y={y}, agg={agg}")

        # If barchart, summarize top 3 categories
        try:
            if kind == "barchart" and x in df.columns and y in df.columns:
                agg_lower = str(agg or "sum").lower()
                if agg_lower == "count":
                    grouped = df.groupby(x)[y].count().sort_values(ascending=False)
                else:
                    if pd.api.types.is_numeric_dtype(df[y]):
                        grouped = df.groupby(x)[y].agg(agg_lower).sort_values(ascending=False)
                    else:
                        grouped = None
                if grouped is not None:
                    top = grouped.head(3)
                    viz_summary_lines.append("top_categories: " + ", ".join(f"{str(ix)}={float(val):.4g}" for ix, val in top.items()))
        except Exception:
            pass

    def _truncate(s: str, n: int) -> str:
        return s if len(s) <= n else (s[:n] + "...")

    # Build prompt for the assistant
    cols_txt = ", ".join(f"{c['name']}({c['dtype']})" for c in analysis_payload.get("columns", [])[:30])
    num_txt_parts = []
    for col, st in (analysis_payload.get("numeric_stats") or {}).items():
        if st:
            num_txt_parts.append(f"{col}: min={st.get('min')}, median={st.get('median')}, mean={st.get('mean')}, max={st.get('max')}")
    num_txt = "; ".join(num_txt_parts[:20])

    prompt = (
        "你是一名资深数据分析顾问。基于以下数据摘要与可视化说明，生成中文洞察，要求：\n"
        "1) 先给出3-5条关键结论（面向业务），2) 补充3条可执行建议，3) 指出数据局限或注意事项1-2条。\n"
        "请避免过度解读，不要虚构。\n\n"
        f"样本行数: {analysis_payload.get('row_count')}\n"
        f"列信息: {cols_txt}\n"
        f"数值统计(部分): {num_txt}\n"
        f"可视化摘要: {' | '.join(viz_summary_lines) if viz_summary_lines else '无'}\n"
    )
    prompt = _truncate(prompt, max_chars)

    # Try MaaS API if configured (.env)
    cfg = load_maas_config(DEFAULT_BASE_URL)
    api_key = cfg.get("api_key") or ""
    model = cfg.get("model") or "Kimi-K2-instruct"
    if api_key:
        try:
            client = LanyunMaaSClient(api_key=api_key, base_url=cfg.get("base_url", DEFAULT_BASE_URL))
            content = client.chat_completion(
                messages=[
                    {"role": "system", "content": "你是专业的数据分析顾问，请用简洁专业的中文输出要点。"},
                    {"role": "user", "content": prompt},
                ],
                model=model,
                temperature=0.3,
                timeout=timeout_secs,
            )
            if isinstance(content, str) and content.strip():
                return {
                    "status": "ok",
                    "provider": "lanyun-maas",
                    "model": model,
                    "insights": content.strip(),
                    "used_fallback": False,
                }
        except Exception:
            # fall through to fallback
            pass

    # Fallback heuristic insights
    bullets = []
    # Numeric highlights
    try:
        stats = analysis_payload.get("numeric_stats") or {}
        for col, st in list(stats.items())[:3]:
            if st:
                bullets.append(f"{col} 平均值约为 {st.get('mean')}, 波动(Std) {st.get('std')}, 范围 [{st.get('min')}, {st.get('max')}]。")
    except Exception:
        pass
    # Viz-based highlight
    try:
        if isinstance(viz, dict):
            kind = str(viz.get("kind", ""))
            x = viz.get("x")
            y = viz.get("y")
            agg = (viz.get("agg") or "sum").lower()
            if kind == "barchart" and x in df.columns and y in df.columns:
                if agg == "count":
                    grouped = df.groupby(x)[y].count().sort_values(ascending=False)
                else:
                    if pd.api.types.is_numeric_dtype(df[y]):
                        grouped = df.groupby(x)[y].agg(agg).sort_values(ascending=False)
                    else:
                        grouped = None
                if grouped is not None and len(grouped) > 0:
                    top_cat, top_val = grouped.index[0], float(grouped.iloc[0])
                    bullets.append(f"{x}中表现最佳的是“{top_cat}”，指标值约 {top_val:.4g}。")
    except Exception:
        pass

    if not bullets:
        bullets.append("数据规模与字段已就绪，建议结合业务目标明确关键指标与切分维度。")

    advice = [
        "建议补充时间维度或关键分群字段，以获得更具可解释性的趋势与对比。",
        "设定统一的数据清洗规则（缺失值、异常值）以保证分析口径一致。",
        "引入交互式分析（筛选、联动）以支持业务决策讨论。",
    ]
    caveats = [
        "样本可能不具有统计代表性，请谨慎外推结论。",
        "字段含义与口径未统一时，指标对比可能失真。",
    ]

    text = "结论：\n- " + "\n- ".join(bullets[:4]) + "\n\n建议：\n- " + "\n- ".join(advice[:3]) + "\n\n注意：\n- " + "\n- ".join(caveats[:2])

    return {
        "status": "ok",
        "provider": "fallback",
        "insights": text,
        "used_fallback": True,
    }

@mcp.tool()
@tool_guard
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Demo dynamic greeting resource (kept)
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Example prompt (optional)
# @mcp.prompt()
# def greet_user(name: str, style: str = "friendly") -> str:
#     """Generate a greeting prompt"""
#     styles = {
#         "friendly": "Please write a warm, friendly greeting",
#         "formal": "Please write a formal, professional greeting",
#         "casual": "Please write a casual, relaxed greeting",
#     }
#     return f"{styles.get(style, styles['friendly'])} for someone named {name}."

if __name__ == "__main__":
    # Start the MCP server
    mcp.run(transport="sse")