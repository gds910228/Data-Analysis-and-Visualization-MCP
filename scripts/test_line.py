import sys
from pathlib import Path

# 确保可导入项目根模块
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main  # noqa: E402
from utils.interactive_line import generate_interactive_line  # noqa: E402


def run():
    csv = Path("data/sample_test_data.csv")
    if not csv.exists():
        print(f"[ERR] CSV not found: {csv}")
        return

    up = main.upload_csv(data=csv.read_text(encoding="utf-8"))
    if up.get("status") not in {"ok", "saved"}:
        print(f"[ERR] upload_csv failed: {up}")
        return
    file_id = up["file_id"]
    csv_path = up.get("path") or f"data/{file_id}.csv"

    # 示例列名（如需指定其它列请改为 --x/--y 的脚本模式）
    x = "Column1"
    y = "Column2"
    agg = "sum"

    res = generate_interactive_line(
        csv_path=csv_path,
        x=x,
        y=y,
        agg=agg,
        file_id=file_id,
    )
    print(f"file_id: {file_id}")
    print(f"kind: {res.get('kind')}")
    print(f"html_path: {res.get('html_path')}")
    print(f"points: {res.get('points')}  x={res.get('x')}  y={res.get('y')}  agg={res.get('agg')}  time_axis={res.get('is_time_axis')}")
    print("DONE.")


if __name__ == "__main__":
    run()