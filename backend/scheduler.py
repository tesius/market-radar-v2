from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from zoneinfo import ZoneInfo
import logging
import asyncio

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

def update_all_data():
    """
    Background Task: Fetches data from all services and updates DATA_STORE.
    This function runs in a separate thread managed by APScheduler.
    """
    logger.info(f"🔄 [Scheduler] Starting data update at {datetime.now(ZoneInfo('Asia/Seoul'))}...")
    
    try:
        # 1. Market Pulse
        DATA_STORE["market_pulse"] = stock_service.get_market_pulse()
        logger.info("✅ [Scheduler] Market Pulse updated")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Market Pulse failed: {e}")

    try:
        # 2. Macro Data
        DATA_STORE["cpi"] = macro_service.get_macro_data("CPIAUCSL", "US CPI (Consumer Price Index)")
        DATA_STORE["unrate"] = macro_service.get_macro_data("UNRATE", "US Unemployment Rate")
        logger.info("✅ [Scheduler] Macro Data updated")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Macro Data failed: {e}")

    try:
        # 3. Risk Ratio
        DATA_STORE["risk_ratio"] = analysis_service.get_risk_ratio()
        logger.info("✅ [Scheduler] Risk Ratio updated")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Risk Ratio failed: {e}")

    try:
        # 4. Credit Spread
        DATA_STORE["credit_spread"] = bond_service.get_credit_spread_data()
        logger.info("✅ [Scheduler] Credit Spread updated")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Credit Spread failed: {e}")

    try:
        # 5. Yield Gap
        DATA_STORE["yield_gap"] = analysis_service.get_yield_gap_data()
        logger.info("✅ [Scheduler] Yield Gap updated")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Yield Gap failed: {e}")

    try:
        # 6. Rate Spread
        DATA_STORE["rate_spread"] = analysis_service.get_rate_spread_data()
        logger.info("✅ [Scheduler] Rate Spread updated")
    except Exception as e:
        logger.error(f"❌ [Scheduler] Rate Spread failed: {e}")

    try:
        # 7. US Rate Spread
        DATA_STORE["us_rate_spread"] = analysis_service.get_us_rate_spread_data()
        logger.info("✅ [Scheduler] US Rate Spread updated")
    except Exception as e:
        logger.error(f"❌ [Scheduler] US Rate Spread failed: {e}")
        
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
