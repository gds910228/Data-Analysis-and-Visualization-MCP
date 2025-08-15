import json
from pathlib import Path

# Directly import tool functions from main.py (decorated with @tool_guard)
from main import upload_csv, analyze_summary, visualize_barchart, report


def pretty(title: str, obj):
    print(f"\n=== {title} ===")
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main():
    sample_path = Path("samples/sales_small.csv")
    if not sample_path.exists():
        raise FileNotFoundError("samples/sales_small.csv not found. Make sure the sample file exists.")

    data = sample_path.read_text(encoding="utf-8")

    # 1) Upload CSV
    res_upload = upload_csv(data=data, delimiter=",", encoding="utf-8")
    pretty("upload_csv", res_upload)
    if res_upload.get("status") != "saved":
        print("Upload failed, aborting.")
        return
    file_id = res_upload["file_id"]

    # 2) Analyze summary
    res_summary = analyze_summary(file_id=file_id, delimiter=",", encoding="utf-8")
    pretty("analyze_summary", res_summary)

    # 3) Visualize bar chart
    res_chart = visualize_barchart(
        file_id=file_id,
        x="city",
        y="sales",
        agg="sum",
        delimiter=",",
        encoding="utf-8",
        figsize=(6.0, 4.0),
    )
    pretty("visualize_barchart", res_chart)

    # 4) Combined report
    res_report = report(
        file_id=file_id,
        analysis="summary",
        viz={"kind": "barchart", "x": "city", "y": "sales", "agg": "sum", "figsize": [6, 4]},
        delimiter=",",
        encoding="utf-8",
    )
    pretty("report", res_report)

    print("\nSmoke test finished.")


if __name__ == "__main__":
    main()