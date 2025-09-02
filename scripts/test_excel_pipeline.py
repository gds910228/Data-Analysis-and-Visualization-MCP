import base64
from pathlib import Path
import sys
import pandas as pd
import random

# 确保项目根目录在 sys.path 中，便于导入 main.py
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main

SAMPLE_XLSX = Path("data/sample_sales.xlsx")

def ensure_sample_excel():
    if SAMPLE_XLSX.exists():
        return
    # 兜底：未运行生成脚本时，内联生成一份
    from datetime import datetime
    rng = random.Random(42)
    regions = ["East", "West", "North", "South"]
    products = ["A", "B", "C"]
    months = pd.date_range("2025-01-01", periods=6, freq="MS")
    base_price = {"A": 100, "B": 120, "C": 80}
    region_factor = {"East": 10, "West": -5, "North": 5, "South": 0}
    rows = []
    for m_idx, m in enumerate(months):
        for r in regions:
            for p in products:
                qty = rng.randint(10, 50)
                unit_price = base_price[p] + region_factor[r] + (m_idx * 2) + rng.randint(-3, 3)
                sales = unit_price * qty
                rows.append({
                    "Region": r,
                    "Product": p,
                    "Month": m.strftime("%Y-%m-%d"),
                    "Quantity": qty,
                    "Sales": float(sales),
                })
    SAMPLE_XLSX.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_excel(SAMPLE_XLSX, index=False, engine="openpyxl")

def main_run():
    ensure_sample_excel()

    b64 = base64.b64encode(SAMPLE_XLSX.read_bytes()).decode("ascii")
    up = main.upload_excel(data_base64=b64)
    assert up.get("status") == "saved", f"upload_excel failed: {up}"
    file_id = up["file_id"]
    print(f"上传完成 file_id: {file_id}")
    print(f"保存路径: {up.get('path')}")

    summary = main.analyze_summary(file_id=file_id)
    print("分析摘要: rows =", summary.get("row_count"), "; columns =", [c["name"] for c in summary.get("columns", [])])

    bar = main.visualize_interactive(file_id=file_id, x="Region", y="Sales", agg="sum")
    print("交互式柱状图:", bar.get("html_path"))

    line = main.visualize_interactive_line(file_id=file_id, x="Month", y="Sales", agg="sum")
    print("交互式折线图:", line.get("html_path"))

    rep = main.export_report_html(file_id=file_id, x="Region", y="Sales", agg="sum", kind="interactive_barchart", ai={"timeout_secs": 12})
    print("报告导出:", rep.get("report_path"))

if __name__ == "__main__":
    main_run()