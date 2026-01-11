from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services import market_data # 방금 만든 모듈 import

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Market Radar v2.0 API Ready"}

# 1. 상단 8개 지표 (Market Pulse)
@app.get("/api/market/pulse")
def get_pulse():
    return market_data.get_market_pulse()

# 2. CPI 데이터 (거시경제)
@app.get("/api/macro/cpi")
def get_cpi():
    return market_data.get_macro_data("CPIAUCSL", "US CPI (Consumer Price Index)")

# 3. 실업률 데이터 (거시경제)
@app.get("/api/macro/unrate")
def get_unrate():
    return market_data.get_macro_data("UNRATE", "US Unemployment Rate")

# 4. 위험 신호 (금/은 비율)
@app.get("/api/macro/risk-ratio")
def get_risk_radar():
    return market_data.get_risk_ratio()