from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import scheduler # 스케줄러 모듈 임포트
import threading

# Lifespan: 앱 시작/종료 시 실행될 로직
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 스케줄러 시작
    sched_obj = scheduler.start_scheduler()
    
    # 2. 초기 데이터 적재 (비동기적으로는 너무 늦을 수 있으므로, 스레드 돌려서 백그라운드 즉시 실행)
    # 이렇게 하면 앱 시작은 막지 않으면서(FastAPI 뜸) 곧 데이터가 채워짐
    update_thread = threading.Thread(target=scheduler.update_all_data)
    update_thread.start()
    
    yield # 앱 실행 중...
    
    # 3. 종료 시 스케줄러 셧다운
    sched_obj.shutdown()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://tesius.github.io", 
]

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

# --- Endpoints now read from Memory (DATA_STORE) ---

# 1. 상단 8개 지표 (Market Pulse)
@app.get("/api/market/pulse")
def get_pulse():
    return scheduler.DATA_STORE["market_pulse"]

# 2. CPI 데이터 (거시경제)
@app.get("/api/macro/cpi")
def get_cpi():
    return scheduler.DATA_STORE["cpi"]

# 3. 실업률 데이터 (거시경제)
@app.get("/api/macro/unrate")
def get_unrate():
    return scheduler.DATA_STORE["unrate"]

# 4. 위험 신호 (금/은 비율)
@app.get("/api/macro/risk-ratio")
def get_risk_radar():
    return scheduler.DATA_STORE["risk_ratio"]

# 5. 크레딧 스프레드 (Credit Spread)
@app.get("/api/market/credit-spread")
def get_credit_spread():
    return scheduler.DATA_STORE["credit_spread"]

# 6. 일드갭 (Yield Gap)
@app.get("/api/market/yield-gap")
def get_yield_gap():
    return scheduler.DATA_STORE["yield_gap"]