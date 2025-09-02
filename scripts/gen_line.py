import argparse
import sys
from pathlib import Path

# 确保可导入项目根模块
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main  # noqa: E402
from utils.interactive_line import generate_interactive_line  # noqa: E402


def main_cli():
    parser = argparse.ArgumentParser(description="Generate interactive line chart (Plotly) from CSV/file_id.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--csv", type=str, help="Path to CSV file")
    src.add_argument("--file-id", type=str, help="Existing file_id persisted by upload_csv")
    parser.add_argument("--x", type=str, required=True, help="X column (time/number/category)")
    parser.add_argument("--y", type=str, required=True, help="Y column (numeric)")
    parser.add_argument("--agg", type=str, default="sum", help="Aggregation: sum|mean|median|min|max|count")
    parser.add_argument("--delimiter", type=str, default=",")
    parser.add_argument("--encoding", type=str, default="utf-8")
    args = parser.parse_args()

    if args.csv:
        # 通过服务上传，获取标准化路径与 file_id
        data = Path(args.csv).read_text(encoding=args.encoding)
        up = main.upload_csv(data=data, delimiter=args.delimiter, encoding=args.encoding)
        if up.get("status") not in {"ok", "saved"}:
            print(f"[ERR] upload_csv failed: {up}")
            sys.exit(2)
        file_id = up["file_id"]
        csv_path = up.get("path") or f"data/{file_id}.csv"
    else:
        # 已知 file_id
        file_id = args.file_id
        csv_path = f"data/{file_id}.csv"
        if not Path(csv_path).exists():
            print(f"[ERR] CSV not found for file_id: {csv_path}")
            sys.exit(2)

    res = generate_interactive_line(
        csv_path=csv_path,
        x=args.x,
        y=args.y,
        agg=args.agg,
        delimiter=args.delimiter,
        encoding=args.encoding,
        file_id=file_id,
    )
    print(f"status: {res.get('status')}")
    print(f"kind: {res.get('kind')}")
    print(f"html_path: {res.get('html_path')}")
    print(f"points: {res.get('points')}  x={res.get('x')}  y={res.get('y')}  agg={res.get('agg')}  time_axis={res.get('is_time_axis')}")


if __name__ == "__main__":
    main_cli()