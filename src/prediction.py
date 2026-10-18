# -*- coding: utf-8 -*-
"""Flood-risk prediction helpers. Prototype only; not an official warning service."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "flood_model.pkl"
FEATURES = ["Rainfall_mm", "Water_Level_m", "Humidity_percent", "Temperature_C"]
CLASSES = ["LOW", "MEDIUM", "HIGH"]


def _rule_based_prediction(rainfall, water_level, humidity, temperature):
    """Transparent fallback when no trained model is available; not a probability model."""
    score = 0.45 * rainfall + 35 * water_level + 0.15 * humidity
    if score > 240 or rainfall > 220 or water_level > 7.2:
        label = "HIGH"
    elif score > 120 or rainfall > 85 or water_level > 4.0:
        label = "MEDIUM"
    else:
        label = "LOW"
    # One-hot values are deliberately not presented as probabilities.
    return label, None, "rule_based_fallback"


def predict_risk_v4(rainfall, water_level, humidity, temperature):
    values = np.asarray([rainfall, water_level, humidity, temperature], dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("ค่าที่ป้อนต้องเป็นตัวเลขที่ถูกต้องและไม่ใช่ NaN/Infinity")
    if rainfall < 0 or water_level < 0 or not 0 <= humidity <= 100:
        raise ValueError("ค่าฝน/ระดับน้ำต้องไม่ติดลบ และความชื้นต้องอยู่ระหว่าง 0–100")
    if not -10 <= temperature <= 60:
        raise ValueError("อุณหภูมิต้องอยู่ระหว่าง -10 ถึง 60 °C")

    if not MODEL_PATH.exists():
        return _rule_based_prediction(*values)

    try:
        model = joblib.load(MODEL_PATH)
        features = pd.DataFrame([values], columns=FEATURES)
        prediction = str(model.predict(features)[0])
        probabilities = None
        if hasattr(model, "predict_proba"):
            raw = model.predict_proba(features)[0]
            probabilities = {str(label): float(prob) for label, prob in zip(model.classes_, raw)}
        return prediction, probabilities, "random_forest"
    except Exception as exc:
        # Do not silently disguise model-load errors as valid AI predictions.
        raise RuntimeError(f"โหลดหรือเรียกใช้โมเดลไม่สำเร็จ: {exc}") from exc


def apply_realtime_safety_layer_v4(model_pred, api_data):
    """Only adjust risk using verified station observations supplied by caller."""
    final_pred = str(model_pred)
    reasons = []
    stations = api_data.get("stations_list") or []
    overbank = int(api_data.get("overbank_count", 0) or 0)
    critical = int(api_data.get("warning_critical_count", 0) or 0)
    max_level = api_data.get("max_water_level")

    if overbank > 0 or (max_level is not None and float(max_level) > 7.5):
        final_pred = "HIGH"
        reasons.append("ข้อมูลสถานีที่ได้รับระบุระดับน้ำล้นตลิ่งหรือสูงกว่าเกณฑ์ 7.5 เมตร")
    elif critical > 0 and final_pred == "LOW":
        final_pred = "MEDIUM"
        reasons.append("ข้อมูลสถานีที่ได้รับมีสถานะเตือนภัยระดับ Warning/Critical")

    if not stations:
        reasons.append("ไม่มีข้อมูลสถานีวัดระดับน้ำที่ยืนยันได้ จึงไม่ได้ใช้ข้อมูลสถานีปรับระดับความเสี่ยง")
    if not reasons:
        reasons.append("ไม่มีเงื่อนไขสถานีที่ทำให้ต้องปรับระดับผลประเมิน")
    return final_pred, " ".join(reasons)
