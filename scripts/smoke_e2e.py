from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional, Tuple

# Ensure project root on sys.path, then import main
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import project main which defines MCP tools as plain functions
import main  # noqa: F401


def choose_xy(summary: dict) -> Tuple[Optional[str], Optional[str]]:
    cols = summary.get("columns") or []
    num_stats = summary.get("numeric_stats") or {}
    all_cols = [str(c.get("name")) for c in cols if c.get("name")]
    numeric_cols = [c for c in all_cols if c in (num_stats.keys() if isinstance(num_stats, dict) else [])]

    x: Optional[str] = None
    y: Optional[str] = None

    # 1) 优先选择非数值列作为 x（分类型/文本）
    for c in cols:
        name = str(c.get("name"))
        dtype = str(c.get("dtype", "")).lower()
        if not name:
            continue
        if not (dtype.startswith("int") or dtype.startswith("uint") or dtype.startswith("float")):
            x = name
            break

    # 2) 如果没有分类型列，使用前两列数值列：x = 第1列，y = 第2列
    if x is None:
        if len(all_cols) >= 1:
            x = all_cols[0]
        if len(numeric_cols) >= 1:
            # 选第一个数值列作为 y；若与 x 相同且存在第二个数值列，则用第二个
            y = numeric_cols[0]
            if x == y and len(numeric_cols) >= 2:
                y = numeric_cols[1]
        # 如果还没有 y，且总列数>=2，则尝试用第二列作为 y（可能也是数值列）
        if y is None and len(all_cols) >= 2:
            y = all_cols[1]

    # 3) 常规情况：若找到分类型 x，则 y 取第一数值列
    if x is not None and y is None and len(numeric_cols) >= 1:
        y = numeric_cols[0]
        if x == y and len(numeric_cols) >= 2:
            y = numeric_cols[1]

    return x, y


def main_entry():
    ap = argparse.ArgumentParser(description="Smoke test: upload -> interactive chart -> AI insights")
    ap.add_argument("--csv", required=True, help="Path to CSV file, e.g., data/sample_test_data.csv")
    ap.add_argument("--x", help="X column (categorical); if omitted, auto-pick")
    ap.add_argument("--y", help="Y column (numeric); if omitted, auto-pick")
    ap.add_argument("--agg", default="sum", help="Aggregation for barchart (sum|mean|median|min|max|count)")
    args = ap.parse_args()

    csv_path = args.csv
    if not os.path.exists(csv_path):
        print(f"[ERR] CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(2)

    # Read CSV content
    with open(csv_path, "r", encoding="utf-8") as f:
        data = f.read()

    print("[1/4] Uploading CSV ...")
    up = main.upload_csv(data=data)
    if up.get("status") != "saved":
        print(f"[ERR] upload_csv failed: {up}", file=sys.stderr)
        sys.exit(3)
    file_id = up["file_id"]
    print(f"  file_id={file_id}  path={up.get('path')}  size={up.get('size_bytes')} bytes")

    print("[2/4] Analyzing summary ...")
    summary = main.analyze_summary(file_id=file_id)
    if summary.get("status") != "ok":
        print(f"[ERR] analyze_summary failed: {summary}", file=sys.stderr)
        sys.exit(4)
    print(f"  rows={summary.get('row_count')}  columns={len(summary.get('columns') or [])}")

    x = args.x
    y = args.y
    if not x or not y:
        auto_x, auto_y = choose_xy(summary)
        x = x or auto_x
        y = y or auto_y
    if not x or not y:
        print(f"[ERR] Unable to determine x/y automatically. Provide --x and --y. columns={summary.get('columns')}", file=sys.stderr)
        sys.exit(5)
    print(f"  chosen x={x}  y={y}  agg={args.agg}")

    print("[3/4] Generating interactive barchart ...")
    viz = main.visualize_interactive(
        file_id=file_id,
        kind="barchart",
        x=x,
        y=y,
        agg=args.agg,
    )
    if viz.get("status") != "ok":
        print(f"[ERR] visualize_interactive failed: {viz}", file=sys.stderr)
        sys.exit(6)
    html_path = viz.get("html_path")
    print(f"  html={html_path}  categories={viz.get('categories')}")

    print("[4/4] Generating AI insights ...")
    insights = main.generate_ai_insights(
        file_id=file_id,
        analysis={
            "row_count": summary.get("row_count"),
            "columns": summary.get("columns"),
            "numeric_stats": summary.get("numeric_stats"),
        },
        viz={"kind": "barchart", "x": x, "y": y, "agg": args.agg},
    )
    if insights.get("status") != "ok":
        print(f"[ERR] generate_ai_insights failed: {insights}", file=sys.stderr)
        sys.exit(7)

    provider = insights.get("provider")
    used_fallback = insights.get("used_fallback")
    model = insights.get("model")
    err = insights.get("maas_error")
    text = insights.get("insights") or ""
    print(f"  provider={provider}  fallback={used_fallback}  model={model or '-'}")
    if err:
        print(f"  maas_error={err}")
    print("\n=== Insights (first 800 chars) ===")
    print((text[:800] + ("..." if len(text) > 800 else "")))

    print("\nDONE.")

if __name__ == "__main__":
    main_entry()