# backend/services/market_data.py (수정 버전)

import yfinance as yf
import pandas_datareader.data as web
from datetime import datetime, timedelta
from cachetools import TTLCache, cached
import pandas as pd
import numpy as np # 데이터 처리를 위해 필요

# 캐시 설정
stock_cache = TTLCache(maxsize=100, ttl=600)
macro_cache = TTLCache(maxsize=100, ttl=86400)
risk_cache = TTLCache(maxsize=100, ttl=600)

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

# 1. Market Pulse (기존과 동일 - 잘 됨)
@cached(cache=stock_cache)
def get_market_pulse():
    results = []
    tickers_str = " ".join(TICKERS.keys())
    # yfinance v0.2 이상 대응 (auto_adjust=True 권장)
    data = yf.download(tickers_str, period="3mo", interval="1d", progress=False, auto_adjust=True)
    
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

# 2. Macro Health (수정: 실패 시 Mock Data 반환)
@cached(cache=macro_cache)
def get_macro_data(series_id, label):
    data = []
    
    # 비상용 가짜 데이터 (서버 다운 방지)
    def generate_mock_data():
        print(f"⚠️ [Fallback] {label} - Mock Data Used")
        mock = []
        base = 3.5 if "Unemployment" in label else 3.0 # CPI도 이제 %니까 3.0 근처로
        for i in range(24):
            d = datetime.now() - timedelta(days=30 * (23 - i))
            val = base + (i % 5) * 0.1
            mock.append({"date": d.strftime("%Y-%m-%d"), "value": round(val, 2)})
        return mock

    try:
        # 데이터 넉넉하게 가져오기 (변동률 계산 위해 1년 더 필요)
        start = datetime(2014, 1, 1) 
        end = datetime.now()
        df = web.DataReader(series_id, "fred", start, end)
        
        if df.empty: raise ValueError("Empty Data")

        # ✅ [핵심 수정] CPI인 경우 -> 전년 대비 증감율(YoY %) 계산
        if series_id == "CPIAUCSL":
            # pct_change(12): 12개월 전과 비교
            # * 100: 퍼센트 단위로 변환
            df['calculated_value'] = df[series_id].pct_change(periods=12) * 100
        else:
            # 실업률(UNRATE)은 이미 % 단위이므로 그대로 사용
            df['calculated_value'] = df[series_id]

        # 계산하느라 앞쪽 12개월은 비게 되므로 제거 (dropna)
        df = df.dropna()

        for date, row in df.iterrows():
            val = row['calculated_value']
            if pd.isna(val): continue
            
            data.append({
                "date": date.strftime("%Y-%m-%d"), 
                "value": round(float(val), 2)
            })
            
        return {"title": label, "data": data}

    except Exception as e:
        print(f"❌ [Macro Error] {series_id}: {e}")
        return {"title": label, "data": generate_mock_data()}


# 3. Risk Radar (수정: 데이터 병합 로직 개선)
@cached(cache=risk_cache)
def get_risk_ratio():
    try:
        # 1. 각각 다운로드 (안전하게 따로 받기)
        # auto_adjust=True로 수정주가(Adj Close) 자동 반영
        gold = yf.download("GC=F", period="max", interval="1d", progress=False, auto_adjust=True)
        silver = yf.download("SI=F", period="max", interval="1d", progress=False, auto_adjust=True)
        sp500 = yf.download("^GSPC", period="max", interval="1d", progress=False, auto_adjust=True)

        # 2. 종가(Close)만 안전하게 추출하는 헬퍼 함수
        def extract_close(df):
            if df.empty: return pd.Series(dtype=float)
            # MultiIndex 처리 ('Close', 'GC=F')
            if isinstance(df.columns, pd.MultiIndex):
                try: return df['Close'].iloc[:, 0] # 첫 번째 종가 컬럼
                except: return df.iloc[:, 0]       # 안되면 그냥 첫 번째 데이터
            # 일반 컬럼 처리
            if 'Close' in df.columns: return df['Close']
            return df.iloc[:, 0]

        g_series = extract_close(gold)
        s_series = extract_close(silver)
        sp_series = extract_close(sp500)

        # 3. 데이터프레임 병합 (Outer Join)
        df = pd.DataFrame({'gold': g_series, 'silver': s_series, 'sp500': sp_series})
        
        # 4. 결측치 채우기 (가장 중요!)
        # ffill: 어제 데이터로 오늘을 채움 (주말/휴일 방어)
        df = df.ffill().dropna()

        result = []
        for date, row in df.iterrows():
            g_val = float(row['gold'])
            s_val = float(row['silver'])
            sp_val = float(row['sp500'])

            # 5. [핵심] 나눗셈 안전장치
            if s_val == 0 or pd.isna(s_val) or pd.isna(g_val):
                continue # 분모가 0이거나 데이터 없으면 패스

            ratio = g_val / s_val
            
            result.append({
                "date": date.strftime("%Y-%m-%d"),
                "ratio": round(ratio, 2),
                "sp500": round(sp_val, 2)
            })
            
        # 데이터가 너무 없으면(API 실패 등) 가짜 데이터라도 반환 (화면 테스트용)
        if len(result) < 10:
            print("⚠️ Risk 데이터 부족으로 Mock Data 생성")
            base_sp = 4500
            base_ratio = 80
            today = datetime.now()
            result = []
            for i in range(100):
                d = today - timedelta(days=100-i)
                result.append({
                    "date": d.strftime("%Y-%m-%d"),
                    "ratio": round(base_ratio + (i%10), 2),
                    "sp500": round(base_sp + (i*10), 2)
                })

        return result

    except Exception as e:
        print(f"❌ [Risk Logic Error]: {e}")
        return []