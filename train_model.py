# -*- coding: utf-8 -*-
"""Train prototype classifier. Metrics apply only to synthetic data."""
from pathlib import Path
import json
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent
FEATURES = ["Rainfall_mm", "Water_Level_m", "Humidity_percent", "Temperature_C"]

def train_flood_model_v4():
    data_path = ROOT / "data" / "flood_data.csv"
    if not data_path.exists():
        from generate_data import generate_synthetic_data_v4
        generate_synthetic_data_v4()
    df = pd.read_csv(data_path)
    required = FEATURES + ["Risk"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"ชุดข้อมูลขาดคอลัมน์: {', '.join(missing)}")
    df = df[required].dropna()
    if len(df) < 30 or df["Risk"].nunique() < 2:
        raise ValueError("ข้อมูลไม่เพียงพอสำหรับฝึก/ทดสอบโมเดล (ต้องมีอย่างน้อย 30 แถวและ 2 คลาส)")
    X, y = df[FEATURES], df["Risk"].astype(str)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=2026, stratify=y)
    model = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, class_weight="balanced", n_jobs=-1)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    out_model = ROOT / "models" / "flood_model.pkl"
    out_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out_model)
    metrics = {"accuracy":float(acc),"n_estimators":150,"max_depth":8,"total_rows":int(len(df)),"train_rows":int(len(X_train)),
               "test_rows":int(len(X_test)),"dataset_type":"synthetic","warning":"Metrics are not evidence of real-world flood prediction accuracy.",
               "classes":list(model.classes_),"classification_report":classification_report(y_test,pred,output_dict=True,zero_division=0),
               "confusion_matrix":confusion_matrix(y_test,pred,labels=model.classes_).tolist()}
    (ROOT / "models" / "model_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    names = ["Rainfall", "Water level", "Humidity", "Temperature"]
    order = np.argsort(model.feature_importances_)[::-1]
    (ROOT / "images").mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8,5))
    plt.bar([names[i] for i in order], model.feature_importances_[order], edgecolor="black")
    plt.title("Feature Importance (Synthetic Prototype Data)")
    plt.ylabel("Importance")
    plt.tight_layout()
    plt.savefig(ROOT / "images" / "feature_importance.png", dpi=150)
    plt.close()
    print(f"Accuracy บนชุดทดสอบจำลอง: {acc:.4f} ({len(X_test)} rows)")
    print("สำเร็จ: บันทึกโมเดลและ metrics แล้ว; ห้ามตีความผลนี้เป็นความแม่นยำต่อเหตุการณ์จริง")
    return metrics

if __name__ == "__main__":
    train_flood_model_v4()
