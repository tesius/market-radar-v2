import yfinance as yf
from cachetools import TTLCache, cached
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

# 캐시 설정
stock_cache = TTLCache(maxsize=100, ttl=600)

TICKERS = {
    "^TNX": "미국 10년물 금리",    # 1. US 10Y Treasury
    "KRW=X": "원/달러 환율",       # 2. USD/KRW
    "^VIX": "VIX (공포지수)",      # 3. Volatility Index
    "^NDX": "나스닥 100",          # 4. NASDAQ 100 (종합지수 ^IXIC 아님)
    "^GSPC": "S&P 500",           # 5. S&P 500
    "^N225": "닛케이 225",         # 6. Nikkei 225 (일본)
    "EEM": "신흥국 ETF (EEM)",     # 7. Emerging Markets
    "^KS11": "코스피 지수"         # 8. KOSPI (한국)
}

# 1. Market Pulse
@cached(cache=stock_cache)
def get_market_pulse():
    results = []
    tickers_str = " ".join(TICKERS.keys())
    # yfinance v0.2 이상 대응 (auto_adjust=True 권장)
    try:
        data = yf.download(tickers_str, period="3mo", interval="1d", progress=False, auto_adjust=True)
    except Exception as e:
        print(f"[Pulse Error] Download failed: {e}")
        return []
    
    # 컬럼 구조 처리 (MultiIndex 대응)
    if isinstance(data.columns, pd.MultiIndex):
        try:
            closes = data['Close']
        except KeyError:
            # auto_adjust=True면 'Close'가 주가일 수 있음
            closes = data
    else:
        closes = data

    for ticker, name in TICKERS.items():
        try:
            if ticker not in closes: continue
            
            series = closes[ticker].dropna()
            if series.empty: continue

            current = series.iloc[-1]
            prev = series.iloc[-2]
            change = current - prev
            change_pct = (change / prev) * 100
            
            display_change = f"{change:+.2f} ({change_pct:+.2f}%)"
            if ticker == "^VIX":
                display_change = f"±{(current/16):.2f}% Expectation"

            sparkline = [{"date": d.strftime("%Y-%m-%d"), "value": v} for d, v in series.tail(90).items()]

            results.append({
                "ticker": ticker, "name": name, "price": current,
                "change": change, "change_percent": change_pct,
                "display_change": display_change, "history": sparkline
            })
        except Exception as e:
            print(f"[Pulse Error] {ticker}: {e}")
            continue
    return results
