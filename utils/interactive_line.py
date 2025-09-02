import os
from pathlib import Path
from datetime import datetime
import re
import pandas as pd
import plotly.express as px
import pandas.api.types as ptypes


def _looks_like_datestr(val: str) -> bool:
    if not isinstance(val, str):
        return False
    s = val.strip()
    # 常见日期格式：YYYY-MM-DD、YYYY/MM/DD、DD/MM/YYYY、含时间的 ISO 等
    patterns = [
        r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}",     # 2025-09-02 or 2025/09/02
        r"^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",   # 02/09/2025
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}",   # 2025-09-02T12:34
    ]
    return any(re.match(p, s) for p in patterns)


def _detect_time_axis(series: pd.Series):
    """
    返回 (is_time_axis: bool, parsed_series or None)
    规则：
    - 字符串/对象列：若大多数值像日期字符串，则尝试解析为 datetime
    - 数值列：若像 Unix 时间戳（秒>1e9 或 毫秒>1e12），按对应单位解析
    - 其他：返回 False
    """
    s = series.dropna()
    if s.empty:
        return False, None

    # 对象/字符串列：基于样本判断
    if ptypes.is_object_dtype(series) or ptypes.is_string_dtype(series):
        sample = s.head(30).astype(str)
        hits = sum(_looks_like_datestr(v) for v in sample)
        if hits >= max(3, int(len(sample) * 0.6)):  # 60% 以上匹配视为日期
            try:
                parsed = pd.to_datetime(series, errors="raise")
                return True, parsed
            except Exception:
                return False, None
        return False, None

    # 数值列：判断是否像时间戳
    if ptypes.is_integer_dtype(series) or ptypes.is_float_dtype(series):
        q50 = s.quantile(0.5)
        try:
            if q50 > 1e12:  # 毫秒级
                parsed = pd.to_datetime(series, unit="ms", errors="raise")
                return True, parsed
            if q50 > 1e9:   # 秒级
                parsed = pd.to_datetime(series, unit="s", errors="raise")
                return True, parsed
        except Exception:
            return False, None
        return False, None

    return False, None


def generate_interactive_line(
    csv_path: str,
    x: str,
    y: str,
    agg: str = "sum",
    delimiter: str = ",",
    encoding: str = "utf-8",
    out_dir: str = "outputs/interactive",
    file_id: str | None = None,
) -> dict:
    """
    读取 CSV，按 x 分组聚合 y，生成交互式折线图 HTML。
    返回: {"status":"ok","kind":"linechart","html_path": "...", "points": N}
    """
    agg = (agg or "sum").lower()
    if agg not in {"sum", "mean", "median", "min", "max", "count"}:
        raise ValueError(f"Unsupported agg: {agg}")

    p = Path(csv_path)
    if not p.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(p, delimiter=delimiter, encoding=encoding)

    if x not in df.columns or y not in df.columns:
        raise ValueError(f"Columns not found. x={x}, y={y}, columns={list(df.columns)}")

    # 时间轴智能检测（仅在像日期/时间戳时转为 datetime）
    is_time, parsed = _detect_time_axis(df[x])
    if is_time:
        df = df.copy()
        df[x] = parsed

    # 聚合
    if agg == "count":
        grouped = df.groupby(x, dropna=False)[y].count().reset_index(name=y)
    else:
        grouped = df.groupby(x, dropna=False)[y].agg(agg).reset_index()

    # 对时间轴/数值轴按 x 排序，类别轴保持原序
    if is_time or ptypes.is_numeric_dtype(grouped[x]):
        grouped = grouped.sort_values(by=x, kind="mergesort")

    # 画图
    fig = px.line(grouped, x=x, y=y, markers=True)
    fig.update_layout(
        title=f"{y} by {x} ({agg})",
        template="plotly_white",
        hovermode="x unified",
        legend_title_text="",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    # 轴类型
    if is_time:
        fig.update_xaxes(title=x, showgrid=True)
    elif ptypes.is_numeric_dtype(grouped[x]):
        fig.update_xaxes(title=x, type="linear", showgrid=True)
    else:
        fig.update_xaxes(title=x, type="category", showgrid=True)
    fig.update_yaxes(title=f"{y} ({agg})", showgrid=True)

    # 输出
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    stem = (file_id or p.stem)
    def safe(s): return str(s).replace(os.sep, "_")
    fname = f"{safe(stem)}_line_{safe(x)}_{safe(y)}_{agg}_{ts}.html"
    out_path = str(Path(out_dir) / fname)
    fig.write_html(out_path, include_plotlyjs="cdn", full_html=True)

    return {
        "status": "ok",
        "kind": "linechart",
        "html_path": out_path,
        "points": int(grouped.shape[0]),
        "x": x,
        "y": y,
        "agg": agg,
        "is_time_axis": is_time,
    }