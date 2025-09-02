from __future__ import annotations
import os, sys
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import main

def run():
    with open("data/sample_test_data.csv", "r", encoding="utf-8") as f:
        data = f.read()
    up = main.upload_csv(data=data)
    if up.get("status") != "saved":
        print("[ERR] upload_csv failed:", up); return
    fid = up["file_id"]
    res = main.export_report_html(file_id=fid, x="Column1", y="Column2", agg="sum", ai=True)
    print(res.get("report_path"))

if __name__ == "__main__":
    run()