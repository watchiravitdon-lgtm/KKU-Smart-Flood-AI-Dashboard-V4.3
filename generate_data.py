# -*- coding: utf-8 -*-
"""Generate synthetic data for software demonstration only, not real flood observations."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent

def generate_synthetic_data_v4(n_samples=1500, seed=2026):
    rng = np.random.default_rng(seed)
    rainfall = rng.uniform(0, 480, n_samples)
    water_level = rng.uniform(0.2, 9.8, n_samples)
    humidity = rng.uniform(35, 100, n_samples)
    temperature = rng.uniform(18, 40, n_samples)
    data = pd.DataFrame({"Rainfall_mm":rainfall,"Water_Level_m":water_level,"Humidity_percent":humidity,"Temperature_C":temperature})
    score = 0.45 * data["Rainfall_mm"] + 35 * data["Water_Level_m"] + 0.15 * data["Humidity_percent"]
    high = (score > 240) | (data["Rainfall_mm"] > 220) | (data["Water_Level_m"] > 7.2)
    medium = (~high) & ((score > 120) | (data["Rainfall_mm"] > 85) | (data["Water_Level_m"] > 4.0))
    data["Risk"] = np.select([high, medium], ["HIGH", "MEDIUM"], default="LOW")
    out = ROOT / "data" / "flood_data.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(out, index=False, encoding="utf-8")
    print(f"สร้างข้อมูลจำลอง {len(data)} แถวที่ {out}")
    print("คำเตือน: ข้อมูลนี้เป็นข้อมูลสังเคราะห์ ไม่ใช่ข้อมูลเหตุการณ์น้ำท่วมจริง")
    return out

if __name__ == "__main__":
    generate_synthetic_data_v4()
