import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from cachetools import TTLCache, cached
import requests
from pykrx import stock
from dotenv import load_dotenv
import os

from .macro_service import get_fred_data

load_dotenv()

# 캐시 설정
risk_cache = TTLCache(maxsize=100, ttl=600)
yield_gap_cache = TTLCache(maxsize=100, ttl=3600) # 1시간 캐시

# API 키 설정
ecos_key = os.getenv("ECOS_API_KEY")

# 3. Risk Radar (수정: 데이터 병합 로직 개선)
@cached(cache=risk_cache) 
def get_risk_ratio():
    try:
        # 1. 데이터 다운로드
        # auto_adjust=True: 수정 주가 반영
        print("📥 Downloading Risk Data...")
        gold = yf.download("GC=F", period="15y", interval="1d", progress=False, auto_adjust=True)
        silver = yf.download("SI=F", period="15y", interval="1d", progress=False, auto_adjust=True)
        sp500 = yf.download("^GSPC", period="15y", interval="1d", progress=False, auto_adjust=True)

        # 2. 안전한 종가 추출 헬퍼 (yfinance 버전 호환성 확보)
        def get_safe_close(df, name):
            if df is None or df.empty:
                print(f"❌ {name}: Empty DataFrame")
                return None
            
            # [중요] Timezone 제거 및 00:00:00 정규화 (병합 전 필수)
            if isinstance(df.index, pd.DatetimeIndex):
                if df.index.tz is not None:
                    # tz_localize(None)은 UTC -> Local 시간 변환이 아니라 그냥 tz 정보만 제거함
                    df.index = df.index.tz_localize(None)
                # 날짜만 남기고 시간 제거 (서로 다른 거래소 마감 시간 차이 무시)
                df.index = df.index.normalize()

            # 1) MultiIndex 처리
            if isinstance(df.columns, pd.MultiIndex):
                # 'Close' 레벨이 있으면 가져오기
                if 'Close' in df.columns.get_level_values(0):
                    series = df.xs('Close', axis=1, level=0)
                    # 만약 series가 또 DataFrame이면 (Ticker가 컬럼인 경우)
                    if isinstance(series, pd.DataFrame):
                        return series.iloc[:, 0]
                    return series
            
            # 2) 일반 Index ('Close' or 'Price')
            if 'Close' in df.columns:
                return df['Close']
            if 'Price' in df.columns:
                return df['Price']
                
            # 3) 1차원 Series인 경우
            if isinstance(df, pd.Series):
                 return df

            # 4) 정 안되면 첫 번째 컬럼
            print(f"⚠️ {name}: 'Close' not found. Using {df.columns[0]}")
            return df.iloc[:, 0]

        g_series = get_safe_close(gold, "Gold")
        s_series = get_safe_close(silver, "Silver")
        sp_series = get_safe_close(sp500, "S&P500")

        if g_series is None or s_series is None or sp_series is None:
            raise ValueError("데이터 다운로드 실패 (Empty Data)")

        # 이름 부여 (concat시 컬럼명으로 사용됨)
        g_series.name = 'gold'
        s_series.name = 'silver'
        sp_series.name = 'sp500'

        # 3. 데이터 병합
        # axis=1 (Outer Join) -> 결측치는 NaN으로 들어감
        df = pd.concat([g_series, s_series, sp_series], axis=1)
        
        # 4. 전처리
        # ffill()로 하루이틀 차이나는 데이터 채움 (휴장일, 시차 등)
        df = df.ffill().dropna()

        # 5. 비율 계산
        df['ratio'] = df['gold'] / df['silver']
        
        # 무한대/NaN 제거
        df = df.replace([np.inf, -np.inf], np.nan).dropna()
        
        # 6. 결과 포맷팅
        df = df.reset_index()
        # index 이름이 다를 수 있으므로 정규화
        if 'Date' in df.columns:
            df.rename(columns={'Date': 'date'}, inplace=True)
        elif 'index' in df.columns:
            df.rename(columns={'index': 'date'}, inplace=True)

        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        df['ratio'] = df['ratio'].round(2)
        df['sp500'] = df['sp500'].round(2)

        final_data = df[['date', 'ratio', 'sp500']].to_dict('records')

        if len(final_data) < 10:
            raise ValueError(f"유효한 데이터가 너무 적음: {len(final_data)} rows")

        print(f"✅ Risk Data Loaded: {len(final_data)} rows")
        return final_data

    except Exception as e:
        print(f"❌ [Risk Logic Error]: {e}")
        import traceback
        traceback.print_exc()
        
        # --- Mock Data 생성 로직 (비상용) ---
        print("⚠️ Risk 데이터 부족으로 Mock Data 생성")
        base_sp = 4500
        base_ratio = 80
        # KST 기준 오늘
        today = datetime.now(ZoneInfo("Asia/Seoul"))
        mock_result = []
        for i in range(200):
            d = today - timedelta(days=200-i)
            mock_result.append({
                "date": d.strftime("%Y-%m-%d"),
                "ratio": round(base_ratio + (i % 10) * 0.5, 2),
                "sp500": round(base_sp + (i * 5), 2)
            })
        return mock_result



# 5. Yield Gap (Market Gauge)
@cached(cache=yield_gap_cache)
def get_yield_gap_data():
    """
    미국 및 한국 시장의 일드갭(Yield Gap) 정보를 가져옴
    미국: S&P 500 PER 역수 - US 10Y Yield
    한국: KOSPI PER 역수 - KR 10Y Yield
    """
    
    def calculate_judgment(current, avg, market_type="US"):
        diff = current - avg
        if market_type == "US":
            # US Judgment: "저평가" / "적정" / "고평가(과열)"
            if diff > 0.5: return "저평가"
            if diff < -0.5: return "고평가(과열)"
            return "적정"
        else:
            # KR Judgment: "적극 매수" / "관망" / "매도"
            if diff > 1.0: return "적극 매수"
            if diff < -0.5: return "매도"
            return "관망"

    # --- 1. US Market (S&P 500) ---
    us_data = {"current": 0, "avg": 0, "status": "데이터 없음", "pe": 0, "yield": 0}
    try:
        # yfinance로 SPY(S&P 500 Proxy) 정보 가져오기
        spy = yf.Ticker("SPY")
        
        # PER 구하기 (trailingPE 우선, 없으면 forwardPE)
        try:
            current_pe = spy.info.get('trailingPE')
            if not current_pe:
                current_pe = spy.info.get('forwardPE')
        except:
            current_pe = 25.0 # Fallback
            
        if not current_pe: current_pe = 25.0
        
        # 10년물 국채 금리
        current_yield_10y = 0
        # 10년물 국채 금리
        current_yield_10y = 0
        # auto_adjust=True로 통일하여 데이터 구조 단순화
        tnx = yf.download("^TNX", period="5d", progress=False, auto_adjust=True)
        
        if not tnx.empty:
            # Robust extraction logic
            val = None
            # 1. MultiIndex handling
            if isinstance(tnx.columns, pd.MultiIndex):
                if 'Close' in tnx.columns.get_level_values(0):
                    val = tnx.xs('Close', axis=1, level=0).iloc[-1]
                    if isinstance(val, pd.Series): val = val.iloc[0]
            # 2. Single Index
            elif 'Close' in tnx.columns:
                val = tnx['Close'].iloc[-1]
            # 3. Fallback
            else:
                 val = tnx.iloc[-1, 0]
            
            if val is not None:
                current_yield_10y = float(val)
        
        # 일드갭 계산
        current_gap = (1 / current_pe) * 100 - current_yield_10y
        
        # 5년 평균 (FRED 데이터 활용)
        # KST 기준 오늘
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        start_5y = (now_kst - timedelta(days=1825)).strftime('%Y-%m-%d')
        end_now = now_kst.strftime('%Y-%m-%d')
        
        # 10년물 금리 히스토리
        yield_10y_hist = get_fred_data("DGS10", start_5y, end_now)
        avg_yield_5y = 0.0
        if not yield_10y_hist.empty and "DGS10" in yield_10y_hist:
             avg_yield_5y = yield_10y_hist["DGS10"].mean()
        else:
             avg_yield_5y = 3.0 # Fallback
        
        # S&P 500 5년 평균 PER (정확한 히스토리는 유료 데이터인 경우가 많아 상수 근사 또는 계산)
        # S&P 500 평균 PER은 약 20~25 사이
        avg_pe_5y = 22.0
        avg_gap_5y = (1 / avg_pe_5y) * 100 - avg_yield_5y
        
        us_data = {
            "current": round(current_gap, 2),
            "avg": round(avg_gap_5y, 2),
            "status": calculate_judgment(current_gap, avg_gap_5y, "US"),
            "pe": round(current_pe, 1),
            "yield": round(current_yield_10y, 2)
        }
    except Exception as e:
        print(f"❌ [US Yield Gap Error]: {e}")
        import traceback
        traceback.print_exc()

    # --- 2. KR Market (KOSPI) ---
    kr_data = {"current": 0, "avg": 0, "status": "데이터 없음", "pe": 0, "yield": 0}
    try:
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        today_str = now_kst.strftime("%Y%m%d")
        
        # 1) KOSPI PER (pykrx)
        curr_pe_kr = 0
        # 최근 5일 중 데이터 있는 날 찾기
        for i in range(5):
            target_date = (now_kst - timedelta(days=i)).strftime("%Y%m%d")
            try:
                # 1001 = 코스피
                # [Fix] PyKrx API 불안정 및 로깅 버그에 대한 방어 코드
                try:
                    df_fund = stock.get_index_fundamental(target_date, target_date, "1001")
                    if not df_fund.empty:
                        # pykrx 버전에 따라 컬럼명이 다를 수 있음. 보통 'PER'
                        if 'PER' in df_fund.columns:
                            curr_pe_kr = df_fund['PER'].iloc[-1]
                            break
                except Exception as e:
                    # JSONDecodeError, Logging Error 등 무시하고 넘어감
                    print(f"⚠️ PyKrx Fetch Warning ({target_date}): {e}")
                    continue
            except:
                continue
        
        if curr_pe_kr == 0: curr_pe_kr = 12.0 # Fallback
        
        # 2) KR 10Y Yield (ECOS API)
        kr_yield = 3.5 # Fallback
        if ecos_key:
            # 817Y002(시장금리 일별), 010210000(국고채 10년)
            # 최근 데이터만 필요하므로 시작일을 7일 전으로 설정
            start_recent = (now_kst - timedelta(days=7)).strftime("%Y%m%d")
            url = f"http://ecos.bok.or.kr/api/StatisticSearch/{ecos_key}/json/kr/1/10/817Y002/D/{start_recent}/{today_str}/010210000"
            resp = requests.get(url, timeout=10) # Timeout added
            if resp.status_code == 200:
                data = resp.json()
                if 'StatisticSearch' in data:
                    kr_yield = float(data['StatisticSearch']['row'][-1]['DATA_VALUE'])
        
        current_gap_kr = (1 / curr_pe_kr) * 100 - kr_yield
        
        # 3) 5년 평균
        # KOSPI 5년 PER 평균
        avg_pe_kr_5y = 11.0 # Fallback
        start_5y_kr = (now_kst - timedelta(days=1825)).strftime('%Y%m%d')
        try:
             # [Fix] PyKrx API 불안정 및 로깅 버그에 대한 방어 코드
             try:
                df_hist_pe = stock.get_index_fundamental(start_5y_kr, today_str, "1001")
                if not df_hist_pe.empty and 'PER' in df_hist_pe.columns:
                    avg_pe_kr_5y = df_hist_pe['PER'].replace(0, np.nan).dropna().mean()
             except Exception as e:
                 print(f"⚠️ PyKrx History Warning: {e}")
        except Exception as e:
             print(f"PyKrx Hist Error: {e}")
             
        # KR 10Y 5년 금리 평균 (ECOS)
        avg_yield_kr_5y = 2.5 # Fallback
        if ecos_key:
            url_avg = f"http://ecos.bok.or.kr/api/StatisticSearch/{ecos_key}/json/kr/1/2000/817Y002/D/{start_5y_kr}/{today_str}/010210000"
            resp_avg = requests.get(url_avg, timeout=10) # Timeout added
            if resp_avg.status_code == 200:
                data = resp_avg.json()
                if 'StatisticSearch' in data:
                    vals = [float(r['DATA_VALUE']) for r in data['StatisticSearch']['row']]
                    if vals:
                        avg_yield_kr_5y = sum(vals) / len(vals)
        
        avg_gap_kr_5y = (1 / avg_pe_kr_5y) * 100 - avg_yield_kr_5y
        
        kr_data = {
            "current": round(current_gap_kr, 2),
            "avg": round(avg_gap_kr_5y, 2),
            "status": calculate_judgment(current_gap_kr, avg_gap_kr_5y, "KR"),
            "pe": round(curr_pe_kr, 1),
            "yield": round(kr_yield, 2)
        }
    except Exception as e:
        print(f"❌ [KR Yield Gap Error]: {e}")

    return {
        "us": us_data,
        "kr": kr_data
    }
