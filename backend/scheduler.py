from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Services
from services import stock_service, macro_service, bond_service, analysis_service

# Configure Logging
class PyKrxFilter(logging.Filter):
    def filter(self, record):
        # pykrx 라이브러리 내부에서 발생하는 로그는 무조건 차단 (포맷팅 버그 방지)
        # record.pathname이 'pykrx'를 포함하면 False 반환
        if record.pathname and "pykrx" in record.pathname:
            return False
        return True

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Root Logger에 필터 추가 (pykrx가 root logger를 쓰더라도 차단됨)
logging.getLogger().addFilter(PyKrxFilter())

# Global Data Store (In-Memory)
DATA_STORE = {
    "market_pulse": [],
    "cpi": {},
    "unrate": {},
    "risk_ratio": [],
    "credit_spread": [],
    "yield_gap": {},
    "rate_spread": [],
    "us_rate_spread": []
}

def _fetch_task(name, func, *args):
    """개별 서비스 호출을 래핑하여 (key, result) 튜플을 반환"""
    try:
        result = func(*args)
        logger.info(f"✅ [Scheduler] {name} updated")
        return (name, result)
    except Exception as e:
        logger.error(f"❌ [Scheduler] {name} failed: {e}")
        return (name, None)

def update_all_data():
    """
    Background Task: Fetches data from all services and updates DATA_STORE.
    ThreadPoolExecutor로 모든 서비스를 병렬 실행하여 전체 업데이트 시간을 단축.
    """
    logger.info(f"🔄 [Scheduler] Starting data update at {datetime.now(ZoneInfo('Asia/Seoul'))}...")

    tasks = {
        "market_pulse": (stock_service.get_market_pulse,),
        "cpi": (macro_service.get_macro_data, "CPIAUCSL", "US CPI (Consumer Price Index)"),
        "unrate": (macro_service.get_macro_data, "UNRATE", "US Unemployment Rate"),
        "risk_ratio": (analysis_service.get_risk_ratio,),
        "credit_spread": (bond_service.get_credit_spread_data,),
        "yield_gap": (analysis_service.get_yield_gap_data,),
        "rate_spread": (analysis_service.get_rate_spread_data,),
        "us_rate_spread": (analysis_service.get_us_rate_spread_data,),
    }

    with ThreadPoolExecutor(max_workers=len(tasks)) as executor:
        futures = {
            executor.submit(_fetch_task, key, *funcs): key
            for key, funcs in tasks.items()
        }
        for future in as_completed(futures):
            key, result = future.result()
            if result is not None:
                DATA_STORE[key] = result

    logger.info("✨ [Scheduler] All updates completed.")

def start_scheduler():
    """
    Initializes and starts the BackgroundScheduler.
    """
    scheduler = BackgroundScheduler(timezone=ZoneInfo("Asia/Seoul"))
    
    # Add job: Run every 20 minutes
    scheduler.add_job(update_all_data, 'interval', minutes=20, id='update_all')
    
    # Run immediately on startup (in a separate thread to avoid blocking startup)
    # or just let the scheduler pick it up. 
    # To have data immediately, we can run it once safely here or handle "Loading" in frontend.
    # Let's run it once synchronously for simplicity (or Threaded) to populate cache.
    # But for fast startup, purely async is better. Let's just create the scheduler.
    # We will trigger an initial update explicitly in main.py lifespan.
    
    scheduler.start()
    return scheduler
