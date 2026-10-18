# -*- coding: utf-8 -*-
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def get_dataset_analysis_v4():
    data_path = ROOT / "data" / "flood_data.csv"
    if not data_path.exists():
        return None, {}
    try:
        df = pd.read_csv(data_path)
        if "Risk" not in df.columns:
            return None, {}
        return df.head(10), df["Risk"].value_counts().to_dict()
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return None, {}
