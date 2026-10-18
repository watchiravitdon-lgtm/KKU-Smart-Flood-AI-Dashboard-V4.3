# -*- coding: utf-8 -*-
"""Weather APIs and geographic lookup. No synthetic station data is returned as live data."""
from functools import lru_cache
from urllib.parse import quote
import requests

# Approximate city-centre coordinates for common provinces; other provinces use Open-Meteo geocoding.
PROVINCE_COORDINATES = {
    "กรุงเทพมหานคร": {"lat": 13.7563, "lon": 100.5018}, "กระบี่": {"lat": 8.0863, "lon": 98.9063},
    "กาญจนบุรี": {"lat": 14.0228, "lon": 99.5328}, "กาฬสินธุ์": {"lat": 16.4322, "lon": 103.5061},
    "กำแพงเพชร": {"lat": 16.4828, "lon": 99.5227}, "ขอนแก่น": {"lat": 16.4322, "lon": 102.8236},
    "จันทบุรี": {"lat": 12.6113, "lon": 102.1039}, "ฉะเชิงเทรา": {"lat": 13.6904, "lon": 101.0779},
    "ชลบุรี": {"lat": 13.3611, "lon": 100.9847}, "ชัยนาท": {"lat": 15.1852, "lon": 100.1251},
    "ชัยภูมิ": {"lat": 15.8068, "lon": 102.0315}, "ชุมพร": {"lat": 10.4930, "lon": 99.1800},
    "เชียงราย": {"lat": 19.9072, "lon": 99.8309}, "เชียงใหม่": {"lat": 18.7883, "lon": 98.9853},
    "ตรัง": {"lat": 7.5594, "lon": 99.6114}, "ตราด": {"lat": 12.2428, "lon": 102.5175},
    "ตาก": {"lat": 16.8839, "lon": 99.1258}, "นครนายก": {"lat": 14.2069, "lon": 101.2131},
    "นครปฐม": {"lat": 13.8199, "lon": 100.0622}, "นครพนม": {"lat": 17.3920, "lon": 104.7696},
    "นครราชสีมา": {"lat": 14.9799, "lon": 102.0978}, "นครศรีธรรมราช": {"lat": 8.4304, "lon": 99.9631},
    "นครสวรรค์": {"lat": 15.7047, "lon": 100.1372}, "นนทบุรี": {"lat": 13.8621, "lon": 100.5144},
    "นราธิวาส": {"lat": 6.4255, "lon": 101.8253}, "น่าน": {"lat": 18.7756, "lon": 100.7730},
    "บึงกาฬ": {"lat": 18.3609, "lon": 103.6464}, "บุรีรัมย์": {"lat": 14.9930, "lon": 103.1029},
    "ปทุมธานี": {"lat": 14.0208, "lon": 100.5250}, "ประจวบคีรีขันธ์": {"lat": 11.8126, "lon": 99.7970},
    "ปราจีนบุรี": {"lat": 14.0500, "lon": 101.3728}, "ปัตตานี": {"lat": 6.8681, "lon": 101.2505},
    "พระนครศรีอยุธยา": {"lat": 14.3532, "lon": 100.5689}, "พะเยา": {"lat": 19.1664, "lon": 99.9019},
    "พังงา": {"lat": 8.4509, "lon": 98.5253}, "พัทลุง": {"lat": 7.6167, "lon": 100.0740},
    "พิจิตร": {"lat": 16.4419, "lon": 100.3488}, "พิษณุโลก": {"lat": 16.8211, "lon": 100.2659},
    "เพชรบุรี": {"lat": 13.1119, "lon": 99.9447}, "เพชรบูรณ์": {"lat": 16.4189, "lon": 101.1550},
    "แพร่": {"lat": 18.1446, "lon": 100.1403}, "ภูเก็ต": {"lat": 7.8804, "lon": 98.3922},
    "มหาสารคาม": {"lat": 16.1840, "lon": 103.3007}, "มุกดาหาร": {"lat": 16.5424, "lon": 104.7235},
    "แม่ฮ่องสอน": {"lat": 19.3013, "lon": 97.9654}, "ยโสธร": {"lat": 15.7926, "lon": 104.1453},
    "ยะลา": {"lat": 6.5411, "lon": 101.2804}, "ร้อยเอ็ด": {"lat": 16.0567, "lon": 103.6531},
    "ระนอง": {"lat": 9.9658, "lon": 98.6348}, "ระยอง": {"lat": 12.6814, "lon": 101.2816},
    "ราชบุรี": {"lat": 13.5283, "lon": 99.8134}, "ลพบุรี": {"lat": 14.7995, "lon": 100.6534},
    "ลำปาง": {"lat": 18.2888, "lon": 99.4909}, "ลำพูน": {"lat": 18.5745, "lon": 99.0087},
    "เลย": {"lat": 17.4860, "lon": 101.7223}, "ศรีสะเกษ": {"lat": 15.1186, "lon": 104.3220},
    "สกลนคร": {"lat": 17.1546, "lon": 104.1348}, "สงขลา": {"lat": 7.1898, "lon": 100.5954},
    "สตูล": {"lat": 6.6238, "lon": 100.0674}, "สมุทรปราการ": {"lat": 13.5991, "lon": 100.5998},
    "สมุทรสงคราม": {"lat": 13.4098, "lon": 100.0023}, "สมุทรสาคร": {"lat": 13.5475, "lon": 100.2744},
    "สระแก้ว": {"lat": 13.8240, "lon": 102.0646}, "สระบุรี": {"lat": 14.5289, "lon": 100.9101},
    "สิงห์บุรี": {"lat": 14.8936, "lon": 100.3967}, "สุโขทัย": {"lat": 17.0078, "lon": 99.8230},
    "สุพรรณบุรี": {"lat": 14.4745, "lon": 100.1177}, "สุราษฎร์ธานี": {"lat": 9.1382, "lon": 99.3217},
    "สุรินทร์": {"lat": 14.8829, "lon": 103.4937}, "หนองคาย": {"lat": 17.8783, "lon": 102.7413},
    "หนองบัวลำภู": {"lat": 17.2041, "lon": 102.4407}, "อ่างทอง": {"lat": 14.5896, "lon": 100.4551},
    "อุดรธานี": {"lat": 17.4138, "lon": 102.7872}, "อุทัยธานี": {"lat": 15.3794, "lon": 100.0245},
    "อุตรดิตถ์": {"lat": 17.6201, "lon": 100.0993}, "อุบลราชธานี": {"lat": 15.2287, "lon": 104.8564},
    "อำนาจเจริญ": {"lat": 15.8657, "lon": 104.6258},
}

ALL_PROVINCES = sorted(PROVINCE_COORDINATES.keys())

@lru_cache(maxsize=128)
def get_province_coords(province_name):
    if province_name in PROVINCE_COORDINATES:
        return PROVINCE_COORDINATES[province_name]
    # Fail explicitly rather than silently using the same incorrect coordinates for every province.
    raise ValueError(f"ไม่มีพิกัดจังหวัด {province_name!r} ในฐานข้อมูลพิกัด")


def get_wmo_weather_desc(code):
    mapping = {0:"ท้องฟ้าแจ่มใส",1:"ท้องฟ้าโปร่ง",2:"ครึ้มบางส่วน",3:"ท้องฟ้าครึ้ม",45:"มีหมอก",48:"มีหมอกน้ำค้างแข็ง",51:"ฝนละอองเบาบาง",53:"ฝนละอองปานกลาง",55:"ฝนละอองหนาแน่น",61:"ฝนตกเล็กน้อย",63:"ฝนตกปานกลาง",65:"ฝนตกหนัก",80:"ฝนซู่เล็กน้อย",81:"ฝนซู่ปานกลาง",82:"ฝนซู่รุนแรง",95:"พายุฝนฟ้าคะนอง",96:"พายุฝนฟ้าคะนองและลูกเห็บ",99:"พายุฝนฟ้าคะนองรุนแรง"}
    return mapping.get(code, "ไม่ทราบสภาพอากาศ")


THAIWATER_BASE = "https://api-v3.thaiwater.net/api/v1/thaiwater30"
THAIWATER_WATER_URL = f"{THAIWATER_BASE}/public/waterlevel_load"
THAIWATER_RAIN_URL = f"{THAIWATER_BASE}/public/rain_24h"


def _records_from_payload(payload):
    """Extract station-like records from ThaiWater JSON without assuming one envelope."""
    found = []
    def walk(node):
        if isinstance(node, dict):
            station = node.get("station")
            geocode = node.get("geocode")
            if isinstance(station, dict) and (isinstance(geocode, dict) or any(k in node for k in ("waterlevel_m", "waterlevel_msl", "rain_24h", "rain_1h"))):
                found.append(node)
            for value in node.values():
                if isinstance(value, (dict, list)):
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
    walk(payload)
    # avoid duplicate object references
    unique = []
    seen = set()
    for row in found:
        key = id(row)
        if key not in seen:
            seen.add(key); unique.append(row)
    return unique


def _th(value):
    if isinstance(value, dict):
        return value.get("th") or value.get("en") or ""
    return value if isinstance(value, str) else ""


def _province(row):
    geo = row.get("geocode") or {}
    return _th(geo.get("province_name")) or _th(row.get("province_name"))


def _station_name(row):
    station = row.get("station") or {}
    return _th(station.get("tele_station_name")) or _th(row.get("station_name")) or "ไม่ระบุชื่อสถานี"


def _number(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


# THDATA provides human-readable station pages, unlike the raw ThaiWater JSON API.
# Its station IDs are independent of ThaiWater station IDs, so do not construct
# /station/{ThaiWater id} (that would open the wrong station). Use a station-name
# search scoped to THDATA as a safe reference link when IDs cannot be cross-mapped.
def _station_reference_url(station_name, province_name):
    query = quote(f'site:water.thdata.co/station "{station_name}" "{province_name}"')
    return f"https://www.google.com/search?q={query}"


def fetch_thaiwater_data_v4(province_name):
    """Fetch public ThaiWater water-level and 24h rainfall endpoints; never fabricate readings."""
    result = {"source": "ThaiWater API", "source_url": THAIWATER_WATER_URL,
              "rain_1h": None, "rain_24h": None, "rain_3d": None, "rain_7d": None,
              "max_water_level": None, "water_trend": "ไม่มีข้อมูลสถานี",
              "overbank_count": 0, "warning_critical_count": 0, "stations_list": [],
              "station_count": 0, "updated_at": None, "error": None}
    errors = []
    water_rows, rain_rows = [], []
    try:
        response = requests.get(THAIWATER_WATER_URL, headers={"Accept":"application/json","User-Agent":"KKU-Smart-Flood-AI/3.3"}, timeout=15)
        response.raise_for_status()
        water_rows = _records_from_payload(response.json())
    except (requests.RequestException, ValueError, TypeError) as exc:
        errors.append(f"ระดับน้ำ: {exc}")
    try:
        response = requests.get(THAIWATER_RAIN_URL, headers={"Accept":"application/json","User-Agent":"KKU-Smart-Flood-AI/3.3"}, timeout=15)
        response.raise_for_status()
        rain_rows = _records_from_payload(response.json())
    except (requests.RequestException, ValueError, TypeError) as exc:
        errors.append(f"ฝน 24 ชม.: {exc}")

    def province_match(row):
        name = _province(row).replace("จังหวัด","").strip()
        return name == province_name or (province_name == "กรุงเทพมหานคร" and name in ("กรุงเทพมหานคร","กรุงเทพ"))

    water_rows = [r for r in water_rows if province_match(r)]
    rain_rows = [r for r in rain_rows if province_match(r)]

    rain_by_station = {}
    for row in rain_rows:
        rain_by_station[_station_name(row)] = row

    stations = []
    for row in water_rows:
        station = row.get("station") or {}
        level = _number(row.get("waterlevel_msl"))
        if level is None:
            level = _number(row.get("waterlevel_m"))
        situation_level = _number(row.get("situation_level"))
        bank_text = str(row.get("diff_wl_bank_text") or "")
        overbank = bank_text.startswith("ล้นตลิ่ง") or situation_level == 5
        critical = situation_level in (3,4,5)
        rainrow = rain_by_station.get(_station_name(row), {})
        lat = _number(station.get("latitude") or station.get("lat") or row.get("latitude"))
        lon = _number(station.get("longitude") or station.get("lon") or row.get("longitude"))
        measured = row.get("waterlevel_datetime") or row.get("datetime") or row.get("updated_at") or row.get("data_datetime")
        stations.append({
            "station_name": _station_name(row), "province": _province(row),
            "water_level": level, "situation": {1:"ปกติ",2:"เฝ้าระวัง",3:"เตือนภัย",4:"วิกฤต",5:"ล้นตลิ่ง"}.get(int(situation_level) if situation_level is not None else -1, "ไม่ระบุ"),
            "rain_1h": _number(rainrow.get("rain_1h")), "rain_24h": _number(rainrow.get("rain_24h")),
            "updated_at": measured, "lat": lat, "lon": lon, "overbank": overbank, "critical": critical,
            "source_url": _station_reference_url(_station_name(row), _province(row)),
            "api_source_url": THAIWATER_WATER_URL,
            "station_id": station.get("id"),
            "station_code": station.get("tele_station_oldcode")
        })
    result["stations_list"] = stations
    result["station_count"] = len(stations)
    levels = [r["water_level"] for r in stations if r["water_level"] is not None]
    result["max_water_level"] = max(levels) if levels else None
    result["overbank_count"] = sum(bool(r["overbank"]) for r in stations)
    result["warning_critical_count"] = sum(bool(r["critical"]) for r in stations)
    timestamps = [r["updated_at"] for r in stations if r.get("updated_at")]
    result["updated_at"] = max(timestamps) if timestamps else None
    rainfall_values = [r.get("rain_24h") for r in rain_rows if _number(r.get("rain_24h")) is not None]
    rain1_values = [r.get("rain_1h") for r in rain_rows if _number(r.get("rain_1h")) is not None]
    result["rain_24h"] = max(map(float, rainfall_values)) if rainfall_values else None
    result["rain_1h"] = max(map(float, rain1_values)) if rain1_values else None
    if len(levels) >= 2:
        deltas = [_number(r.get("waterlevel_msl_previous")) for r in water_rows]
        deltas = [v for v in deltas if v is not None]
        result["water_trend"] = f"{sum(deltas)/len(deltas):+.2f} m" if deltas else "ไม่มีข้อมูลแนวโน้ม"
    elif levels:
        result["water_trend"] = "มีข้อมูลระดับน้ำ 1 สถานี"
    if errors:
        result["error"] = "; ".join(errors)
    return result

def fetch_openmeteo_current(province_name):
    coords = get_province_coords(province_name)
    url = "https://api.open-meteo.com/v1/forecast"
    try:
        res = requests.get(url, params={"latitude":coords["lat"], "longitude":coords["lon"],
            "current":"temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m", "timezone":"Asia/Bangkok"}, timeout=10)
        res.raise_for_status()
        current = res.json().get("current", {})
        required = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"]
        if any(current.get(k) is None for k in required):
            raise ValueError("API ไม่ส่งค่าปัจจุบันครบถ้วน")
        return {"available": True, "source":"Open-Meteo", "time":current.get("time"), "temperature":float(current["temperature_2m"]),
                "humidity":float(current["relative_humidity_2m"]), "precipitation":float(current["precipitation"]), "wind_speed":float(current["wind_speed_10m"])}
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        return {"available":False, "source":"Open-Meteo", "error":str(exc), "time":None, "temperature":None, "humidity":None, "precipitation":None, "wind_speed":None}


def fetch_openmeteo_forecast(province_name):
    coords = get_province_coords(province_name)
    try:
        res = requests.get("https://api.open-meteo.com/v1/forecast", params={"latitude":coords["lat"], "longitude":coords["lon"],
            "daily":"weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max", "timezone":"Asia/Bangkok", "forecast_days":7}, timeout=10)
        res.raise_for_status()
        daily = res.json().get("daily", {})
        rows=[]
        for i, date in enumerate(daily.get("time", [])):
            def val(key):
                values=daily.get(key, [])
                return values[i] if i < len(values) else None
            rows.append({"date":date,"weather_desc":get_wmo_weather_desc(val("weather_code")),"temp_max":val("temperature_2m_max"),
                "temp_min":val("temperature_2m_min"),"precip_sum":val("precipitation_sum"),"precip_prob":val("precipitation_probability_max"),"wind_speed_max":val("wind_speed_10m_max")})
        return rows
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return []
