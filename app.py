# -*- coding: utf-8 -*-
"""KKU Smart Flood AI V3.3 — educational flood-risk dashboard."""
from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

from src.weather_api import (
    ALL_PROVINCES, fetch_thaiwater_data_v4, fetch_openmeteo_current,
    fetch_openmeteo_forecast, get_province_coords
)
from src.prediction import predict_risk_v4, apply_realtime_safety_layer_v4
from src.data_analysis import get_dataset_analysis_v4

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="KKU Smart Flood AI V3.3", page_icon="🌊", layout="wide")

st.markdown("""
<style>
.stApp { background:#0e1117; color:#f4f6fb; }
.block-container { padding-top:1.6rem; max-width:1500px; }
div[data-testid="stMetric"] { background:#171b24; border:1px solid #292f3b; padding:14px; border-radius:12px; }
div[data-testid="stAlert"] { border-radius:10px; }
h1,h2,h3 { letter-spacing:-.3px; }
.small-muted { color:#9ca3af; font-size:.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("🌊 KKU Smart Flood AI")
st.markdown("ระบบ AI สำหรับประเมินความเสี่ยงน้ำท่วมจากข้อมูลฝน ระดับน้ำ และสถานีตรวจวัด")
st.info("V3 เชื่อมข้อมูล ThaiWater + Open-Meteo และแสดง Weather Forecast 7 วันตามจังหวัดที่เลือก พร้อม Real-time Water Safety Layer")

if "history_v4" not in st.session_state:
    st.session_state.history_v4 = []

# 1) Province and data refresh
st.header("1. เลือกจังหวัดและอัปเดตข้อมูล API")
selected_province = st.selectbox("จังหวัดของพื้นที่ที่ต้องการวิเคราะห์ (77 จังหวัด)", ALL_PROVINCES,
                                 index=ALL_PROVINCES.index("กรุงเทพมหานคร") if "กรุงเทพมหานคร" in ALL_PROVINCES else 0)
if st.button("🔄 อัปเดตข้อมูล ThaiWater + สภาพอากาศ", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

with st.spinner("กำลังโหลดข้อมูลจาก ThaiWater และ Open-Meteo..."):
    water = fetch_thaiwater_data_v4(selected_province)
    weather = fetch_openmeteo_current(selected_province)
    forecast = fetch_openmeteo_forecast(selected_province)

def metric_value(value, unit="", digits=1):
    return "ไม่มีข้อมูล" if value is None else f"{value:.{digits}f}{unit}"

m1,m2,m3,m4 = st.columns(4)
m1.metric("ฝน 1 ชม.", metric_value(water.get("rain_1h"), " mm"))
m2.metric("ฝน 24 ชม.", metric_value(water.get("rain_24h"), " mm"))
m3.metric("ฝนสะสม 3 วัน", metric_value(water.get("rain_3d"), " mm"))
m4.metric("ฝนสะสม 7 วัน", metric_value(water.get("rain_7d"), " mm"))
m5,m6,m7,m8 = st.columns(4)
m5.metric("ระดับน้ำสูงสุด", metric_value(water.get("max_water_level"), " m"))
trend = water.get("water_trend")
m6.metric("แนวโน้มระดับน้ำ", trend if isinstance(trend,str) else metric_value(trend, " m"))
m7.metric("สถานีล้นตลิ่ง", int(water.get("overbank_count",0)))
m8.metric("สถานีเตือน/วิกฤต", int(water.get("warning_critical_count",0)))

if water.get("updated_at"):
    st.caption(f"ThaiWater: {water.get('station_count',0)} สถานีระดับน้ำ | อัปเดตข้อมูลเมื่อ {water['updated_at']}")
else:
    st.caption(f"แหล่งข้อมูลสถานี: {water.get('source','ThaiWater')} | ไม่มีเวลารายงานจาก API")
if water.get("overbank_count",0) > 0:
    st.warning(f"⚠️ พบสถานีระดับน้ำล้นตลิ่ง {water['overbank_count']} สถานี")
elif water.get("warning_critical_count",0) > 0:
    st.warning(f"⚠️ พบสถานีเตือน/วิกฤต {water['warning_critical_count']} สถานี")
if water.get("error"):
    st.warning(f"ไม่สามารถโหลดข้อมูลสถานีบางส่วนได้: {water['error']}")

st.subheader("สถานีระดับน้ำล่าสุด")
stations = water.get("stations_list", [])
if stations:
    dfst = pd.DataFrame(stations)
    showcols = [c for c in ["station_name","province","water_level","situation","rain_1h","rain_24h","updated_at","source_url"] if c in dfst.columns]
    st.dataframe(dfst[showcols], use_container_width=True, hide_index=True,
                 column_config={
                     "source_url": st.column_config.LinkColumn(
                         "รายละเอียดสถานี",
                         display_text="ค้นหาสถานีบน THDATA ↗",
                         help="เปิดผลค้นหาชื่อสถานีและจังหวัดบน THDATA เพื่อหลีกเลี่ยงการเปิด JSON API ดิบหรือใช้รหัสสถานีผิด"
                     )
                 })
    st.caption("ลิงก์อ้างอิงจะค้นหาด้วยชื่อสถานีและจังหวัดบน THDATA เพราะรหัสสถานีของ THDATA ไม่ใช่รหัสเดียวกับ ThaiWater API")
else:
    st.info("ไม่พบข้อมูลสถานีสำหรับจังหวัดนี้จาก API หรือ API ยังไม่พร้อมให้บริการ ระบบจะไม่สร้างข้อมูลสถานีปลอม")
st.caption("แหล่งข้อมูลสถานี: ThaiWater National Hydroinformatics Data Center")
st.markdown("[เปิดเว็บไซต์ ThaiWater](https://www.thaiwater.net/) · [API ระดับน้ำสาธารณะ](https://api-v3.thaiwater.net/api/v1/thaiwater30/public/waterlevel_load) · [API ฝน 24 ชั่วโมง](https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_24h)")

# 2) Forecast
st.header("🌤️ Weather Forecast 7 วัน")
st.caption(f"เริ่มจากวันนี้ • จังหวัด {selected_province} • ข้อมูลพยากรณ์จาก Open-Meteo")
if forecast:
    days = st.columns(min(7,len(forecast)))
    for i, day in enumerate(forecast[:7]):
        with days[i]:
            st.markdown(f"**{day['date']}**")
            st.markdown(f"### {day['weather_desc']}")
            if day.get("temp_max") is not None and day.get("temp_min") is not None:
                st.metric("อุณหภูมิ", f"{day['temp_max']}° / {day['temp_min']}°C")
            if day.get("precip_sum") is not None:
                st.write(f"🌧️ ฝน {day['precip_sum']} mm")
            if day.get("precip_prob") is not None:
                st.write(f"โอกาสฝน {day['precip_prob']}%")
else:
    st.warning("ไม่สามารถโหลดพยากรณ์ 7 วันจาก Open-Meteo ได้ในขณะนี้")

# 3) Rain map
st.header("🗺️ แผนที่สถานีฝนและระดับน้ำ")
coords = get_province_coords(selected_province)
map_obj = folium.Map(location=[coords["lat"],coords["lon"]], zoom_start=7, tiles="OpenStreetMap")
for row in stations:
    if row.get("lat") is None or row.get("lon") is None:
        continue
    color = "red" if row.get("overbank") else ("orange" if row.get("critical") else "blue")
    popup = f"{row.get('station_name','สถานี')}<br>ระดับน้ำ: {row.get('water_level','ไม่มีข้อมูล')} m<br>สถานะ: {row.get('situation','ไม่ระบุ')}"
    folium.CircleMarker([row["lat"],row["lon"]], radius=7, color=color, fill=True, fill_opacity=.8,
                        popup=folium.Popup(popup, max_width=300)).add_to(map_obj)
folium.Marker([coords["lat"],coords["lon"]], tooltip=f"พิกัดอ้างอิงจังหวัด {selected_province}",
              icon=folium.Icon(color="cadetblue",icon="info-sign")).add_to(map_obj)
st_folium(map_obj, use_container_width=True, height=430, returned_objects=[])
st.caption(f"แสดงสถานี ThaiWater ที่มีพิกัดในจังหวัด {selected_province} เท่านั้น จุดอ้างอิงจังหวัดใช้พิกัดโดยประมาณ")

# 4) Risk model
st.header("2. AI Flood Risk Analysis")
st.caption(f"จังหวัดที่วิเคราะห์: {selected_province} | อ้างอิงข้อมูลล่าสุด: {water.get('updated_at') or 'ไม่ระบุ'}")
default_rain = float(weather.get("precipitation") or water.get("rain_24h") or 0)
default_humidity = float(weather.get("humidity") or 60)
default_temp = float(weather.get("temperature") or 30)
default_level = float(water.get("max_water_level") or 0)
with st.expander("ปรับค่าตัวแปรสำหรับวิเคราะห์", expanded=False):
    c1,c2,c3,c4 = st.columns(4)
    rain_in = c1.number_input("ฝน (mm)", min_value=0.0, max_value=1000.0, value=default_rain, step=1.0)
    level_in = c2.number_input("ระดับน้ำ (m)", min_value=0.0, max_value=30.0, value=default_level, step=.1)
    humid_in = c3.number_input("ความชื้น (%)", min_value=0.0, max_value=100.0, value=default_humidity, step=1.0)
    temp_in = c4.number_input("อุณหภูมิ (°C)", min_value=-10.0, max_value=60.0, value=default_temp, step=1.0)
if st.button("🔎 วิเคราะห์ซ้ำจากข้อมูลจังหวัดนี้", type="primary"):
    try:
        model_pred, probs, model_source = predict_risk_v4(rain_in, level_in, humid_in, temp_in)
        final_pred, safety_reason = apply_realtime_safety_layer_v4(model_pred, water)
        reasons = [safety_reason] if safety_reason else []
        st.session_state.last_analysis = {"province":selected_province,"model_pred":model_pred,"final_pred":final_pred,
            "probs":probs,"model_source":model_source,"reasons":reasons,"time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rain":rain_in,"level":level_in,"humidity":humid_in,"temperature":temp_in}
        st.session_state.history_v4.insert(0, st.session_state.last_analysis.copy())
    except Exception as exc:
        st.error(f"วิเคราะห์ไม่สำเร็จ: {exc}")

result = st.session_state.get("last_analysis")
if result:
    label = result["final_pred"]
    if label == "HIGH":
        st.error(f"ผลการประเมินจังหวัด{result['province']}: 🔴 ความเสี่ยงสูง")
    elif label == "MEDIUM":
        st.warning(f"ผลการประเมินจังหวัด{result['province']}: 🟠 ความเสี่ยงปานกลาง")
    else:
        st.success(f"ผลการประเมินจังหวัด{result['province']}: 🟢 ความเสี่ยงต่ำ")
    if result["model_pred"] != label:
        st.info(f"AI Model เดิมประเมิน {result['model_pred']} แต่ Real-time Water Safety Layer ปรับเป็น {label} จากข้อมูลสถานี")
    if result.get("reasons"):
        st.markdown("**เหตุผลจากข้อมูลปัจจุบัน:**")
        for reason in result["reasons"]:
            st.write(f"• {reason}")
    if result.get("probs"):
        p = result["probs"]
        st.subheader("ความน่าจะเป็นจากโมเดล (ก่อน Safety Layer)")
        pc = st.columns(3)
        for col, key in zip(pc, ["LOW","MEDIUM","HIGH"]):
            col.metric(key, f"{100*p.get(key,0):.2f}%")
else:
    st.info("กดปุ่มวิเคราะห์เพื่อประเมินความเสี่ยง ระบบจะไม่สรุปผลโดยไม่มีการเรียกวิเคราะห์")

# 5) model performance and importance
st.header("3. AI Model Performance")
metrics_path = ROOT / "models" / "model_metrics.json"
metrics = {}
if metrics_path.exists():
    try:
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        metrics = {}
if metrics:
    a,b,c = st.columns(3)
    accuracy = metrics.get("accuracy")
    a.metric("Model Accuracy", f"{accuracy*100:.2f}%" if isinstance(accuracy,(int,float)) else "ไม่มีข้อมูล")
    b.metric("Decision Trees", metrics.get("n_estimators","ไม่มีข้อมูล"))
    c.metric("Training Dataset", metrics.get("total_rows","ไม่มีข้อมูล"))
else:
    st.info("ยังไม่มีไฟล์ metrics จากการฝึกโมเดล จึงไม่แสดงค่าความแม่นยำที่คาดเดา")
st.caption("Accuracy มาจาก Synthetic Prototype Dataset ไม่ใช่ความแม่นยำที่ผ่านการรับรองจากข้อมูลน้ำท่วมจริง")

st.header("4. AI Feature Importance")
try:
    img = ROOT / "images" / "feature_importance.png"
    if img.exists():
        st.image(str(img), use_container_width=True)
    else:
        st.info("ยังไม่มีกราฟ Feature Importance — รัน python train_model.py เพื่อสร้าง")
except Exception:
    st.info("ไม่สามารถอ่านกราฟ Feature Importance ได้")

# 6) Dataset analysis
st.header("5. วิเคราะห์ข้อมูล")
sample, counts = get_dataset_analysis_v4()
left,right = st.columns([1,1])
with left:
    st.subheader("จำนวนข้อมูลแต่ละระดับ")
    if counts:
        st.bar_chart(pd.Series(counts, name="จำนวนข้อมูล"))
    else:
        st.info("ไม่พบชุดข้อมูลฝึก")
with right:
    st.subheader("ตัวอย่าง Training Dataset")
    if sample is not None:
        st.dataframe(sample, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีไฟล์ data/flood_data.csv")

# 7) History
st.header("6. ประวัติการวิเคราะห์")
if st.button("🗑️ ล้างประวัติ"):
    st.session_state.history_v4 = []
    st.rerun()
if st.session_state.history_v4:
    hist = pd.DataFrame(st.session_state.history_v4)
    keep = [c for c in ["time","province","rain","level","humidity","temperature","model_pred","final_pred","model_source"] if c in hist.columns]
    st.dataframe(hist[keep], use_container_width=True, hide_index=True)
else:
    st.caption("ยังไม่มีประวัติการวิเคราะห์ใน Session นี้")

# 8) Sources and limits
st.header("7. แหล่งข้อมูลและข้อจำกัด")
st.markdown("""
- **ThaiWater** — ข้อมูลฝนและระดับน้ำจากสถานีตรวจวัดของคลังข้อมูลน้ำแห่งชาติ
- **Open-Meteo** — อุณหภูมิ ความชื้น สภาพอากาศปัจจุบัน และพยากรณ์ 7 วัน ณ พิกัดตัวแทนจังหวัด
- **AI Model** — Random Forest ที่ฝึกด้วย Synthetic Prototype Dataset
- **Real-time Water Safety Layer** — ตรวจสอบข้อมูลสถานี เช่น น้ำล้นตลิ่ง ระดับเตือน/วิกฤต และแนวโน้มระดับน้ำ

ข้อจำกัด: โปรเจกต์นี้เป็นต้นแบบเพื่อการศึกษา โมเดลยังไม่ได้รับการตรวจสอบความแม่นยำด้วยข้อมูลน้ำท่วมจริงในระยะยาว จึงไม่ควรใช้แทนประกาศเตือนภัยจากหน่วยงานรัฐ
""")
st.warning("⚠️ ใช้เพื่อการศึกษาและพัฒนา Portfolio ไม่ใช่ระบบตัดสินใจด้านความปลอดภัยในสถานการณ์จริง")
with st.expander("📊 สถิติการใช้งานเว็บไซต์"):
    st.metric("จำนวนครั้งที่วิเคราะห์ใน Session นี้", len(st.session_state.history_v4))
st.divider()
st.caption("ผู้พัฒนา: นาย วชิรวิทย์ ดอนซุยแป · โรงเรียนพุทธิรังสีพิบูล · จังหวัดฉะเชิงเทรา · KKU Smart Flood AI V3.3")
