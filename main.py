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

# Prepare directories for later tools
os.makedirs("data", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

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