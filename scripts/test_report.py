from __future__ import annotations
import os, sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import main

CSV = "data/sample_test_data.csv"

def run():
    with open(CSV, "r", encoding="utf-8") as f:
        data = f.read()
    up = main.upload_csv(data=data)
    if up.get("status") != "saved":
        print("[ERR] upload_csv failed:", up); sys.exit(2)
    fid = up["file_id"]
    print("file_id:", fid)

    rpt = main.report(
        file_id=fid,
        analysis="summary",
        viz={"kind": "interactive_barchart", "x": "Column1", "y": "Column2", "agg": "sum"},
        ai={"timeout_secs": 50.0},  # 增大超时以避免网络波动导致的超时
    )
    print("report.status:", rpt.get("status"))
    viz = rpt.get("viz") or {}
    print("viz.kind:", viz.get("kind"))
    print("viz.html_path:", viz.get("html_path"))
    ai = rpt.get("ai_insights") or {}
    print("ai.provider:", ai.get("provider"))
    print("ai.fallback:", ai.get("used_fallback"))
    print("ai.model:", ai.get("model"))
    if ai.get("maas_error"):
        print("ai.maas_error:", ai.get("maas_error"))
    print("DONE.")

if __name__ == "__main__":
    run()