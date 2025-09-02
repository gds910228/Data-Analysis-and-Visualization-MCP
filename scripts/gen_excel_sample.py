import os
from pathlib import Path
import pandas as pd
import random

def generate_sample_excel(path: str = "data/sample_sales.xlsx") -> str:
    # 确保目录
    Path("data").mkdir(parents=True, exist_ok=True)

    rng = random.Random(42)
    regions = ["East", "West", "North", "South"]
    products = ["A", "B", "C"]
    months = pd.date_range("2025-01-01", periods=6, freq="MS")  # 每月首日

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
                    "Month": m.strftime("%Y-%m-%d"),  # 形如 2025-01-01，便于时间轴识别
                    "Quantity": qty,
                    "Sales": float(sales),
                })

    df = pd.DataFrame(rows)
    out_path = Path(path)
    df.to_excel(out_path, index=False, engine="openpyxl")
    return str(out_path)

if __name__ == "__main__":
    out = generate_sample_excel()
    print(f"Excel 测试数据已生成: {out}")