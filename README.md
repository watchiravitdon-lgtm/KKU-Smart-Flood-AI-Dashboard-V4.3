# KKU Smart Flood AI V3.3

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data sources
- ThaiWater public water-level endpoint: https://api-v3.thaiwater.net/api/v1/thaiwater30/public/waterlevel_load
- ThaiWater public 24-hour rainfall endpoint: https://api-v3.thaiwater.net/api/v1/thaiwater30/public/rain_24h
- Open-Meteo forecast API: https://open-meteo.com/

The app only displays ThaiWater station records when the public endpoint returns records that can be matched to the selected province. Three-day and seven-day observed rainfall are shown as unavailable unless supported by the API response; no synthetic live station values are generated.

This is an educational prototype, not an official flood-warning service. The ML model uses synthetic training data and is not validated for real-world flood prediction.
