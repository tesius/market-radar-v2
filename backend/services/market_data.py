# backend/services/market_data.py (수정 버전)

import yfinance as yf
from datetime import datetime, timedelta
from cachetools import TTLCache, cached
import pandas as pd
import numpy as np # 데이터 처리를 위해 필요
from dotenv import load_dotenv
import os
from fredapi import Fred
import requests    
from pykrx import stock

# 캐시 설정
stock_cache = TTLCache(maxsize=100, ttl=600)
macro_cache = TTLCache(maxsize=100, ttl=86400)
risk_cache = TTLCache(maxsize=100, ttl=600)
credit_cache = TTLCache(maxsize=100, ttl=86400) # 24시간 캐시 (장기 데이터)
yield_gap_cache = TTLCache(maxsize=100, ttl=3600) # 1시간 캐시

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

# 1. 환경 변수 로딩 (.env 파일 읽기)
load_dotenv()

# 2. API 키 설정
fred_key = os.getenv("FRED_API_KEY")
ecos_key = os.getenv("ECOS_API_KEY")
if fred_key:
    fred = Fred(api_key=fred_key)
else:
    print("⚠️ 경고: FRED API 키가 없습니다. 거시경제 데이터 기능이 제한됩니다.")
    fred = None

def get_fred_data(series_id, start, end):
    """
    FRED 데이터 가져오기 (fredapi 사용)
    """
    if fred is None:
        return pd.DataFrame()

    try:
        # 관측 시작일(observation_start) 지정으로 데이터량 조절
        series = fred.get_series(series_id, observation_start=start, end=end)
        
        # Series를 DataFrame으로 변환 및 정제
        df = pd.DataFrame(series, columns=[series_id])
        df.index.name = 'DATE'
        
        # 결측치 제거 (그래프 끊김 방지)
        return df.dropna()
        
    except Exception as e:
        print(f"FRED Error ({series_id}): {e}")
        return pd.DataFrame()


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
        df = get_fred_data(series_id, start, end)
        
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
        # 1. 데이터 다운로드
        # auto_adjust=True: 수정 주가 반영
        print("📥 Downloading Risk Data...")
        gold = yf.download("GC=F", period="2y", interval="1d", progress=False, auto_adjust=True)
        silver = yf.download("SI=F", period="2y", interval="1d", progress=False, auto_adjust=True)
        sp500 = yf.download("^GSPC", period="2y", interval="1d", progress=False, auto_adjust=True)

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
        today = datetime.now()
        mock_result = []
        for i in range(200):
            d = today - timedelta(days=200-i)
            mock_result.append({
                "date": d.strftime("%Y-%m-%d"),
                "ratio": round(base_ratio + (i % 10) * 0.5, 2),
                "sp500": round(base_sp + (i * 5), 2)
            })
        return mock_result



# 4. Credit Spread (ECOS API)
@cached(cache=credit_cache)
def get_credit_spread_data():
    """
    한국은행 ECOS API를 통해 국고채(3년)와 회사채(AA-, 3년) 금리 차이(Credit Spread)를 계산
    """
    
    # 비상용 Mock Data
    def generate_mock_spread():
        print("⚠️ [Fallback] Credit Spread - Mock Data Used")
        today = datetime.now()
        data = []
        base_val = 0.8
        # 15년치 데이터 생성 (약 5400일)
        for i in range(180): # 180개월 (15년)
            d = today - timedelta(days=30 * (179 - i))
            
            # 국고채 3년 (약 3.0 ~ 4.5% 사이 변동)
            gov_val = 3.5 + (np.sin(i / 20) * 1.0) + (np.random.normal(0, 0.05))
            if gov_val < 1.0: gov_val = 1.0
            
            # 스프레드 (0.4 ~ 1.5% 사이)
            spread_val = base_val + (i * 0.002) + (np.sin(i / 10) * 0.3)
            if spread_val < 0.3: spread_val = 0.3
            
            # 회사채 = 국고채 + 스프레드
            corp_val = gov_val + spread_val
            
            data.append({
                "date": d.strftime("%Y-%m-%d"), 
                "gov": round(gov_val, 2),
                "corp": round(corp_val, 2),
                "spread": round(spread_val, 2)
            })
        return data

    if not ecos_key:
        print("⚠️ 경고: ECOS API 키가 없습니다. Credit Spread 기능이 제한됩니다.")
        return generate_mock_spread()

    try:
        # 오늘 날짜와 15년 전 날짜 구하기
        end_date = datetime.now().strftime("%Y%m%d")
        # 2011년 1월 1일부터 (약 15년)
        start_date = "20110101"

        # ECOS API 호출 함수
        def fetch_ecos(stat_code, item_code):
            # URL: /StatisticSearch/apikey/json/kr/1/20000/stat_code/DD/start/end/item_code
            # 15년치면 약 5500일 이므로 넉넉하게 20000
            url = f"http://ecos.bok.or.kr/api/StatisticSearch/{ecos_key}/json/kr/1/20000/{stat_code}/D/{start_date}/{end_date}/{item_code}"
            
            resp = requests.get(url)
            data = resp.json()
            
            if 'StatisticSearch' not in data:
                return None
                
            rows = data['StatisticSearch']['row']
            df = pd.DataFrame(rows)
            # 필요한 컬럼만
            df = df[['TIME', 'DATA_VALUE']]
            df.columns = ['date', 'value']
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df['value'] = pd.to_numeric(df['value'])
            return df.set_index('date')

        # 1. 국고채 3년 (Stat: 817Y002, Item: 010200000)
        gov_df = fetch_ecos("817Y002", "010200000")
        
        # 2. 회사채 3년 AA- (Stat: 817Y002, Item: 010300000 ?)
        corp_df = fetch_ecos("817Y002", "010300000") 
        
        # fallback for Corp if first try fails (Try code for Corp AA-)
        if corp_df is None or corp_df.empty:
             # Try alternate code if known, or fail
             pass

        if gov_df is None or corp_df is None:
            raise ValueError("ECOS 데이터 수신 실패 (데이터 없음))")

        # 3. Spread 계산 (회사채 - 국고채)
        # 인덱스 기준으로 join
        merged = corp_df.join(gov_df, lsuffix='_corp', rsuffix='_gov').dropna()
        merged['spread'] = merged['value_corp'] - merged['value_gov']
        
        # 4. 포맷팅
        result = []
        for date, row in merged.iterrows():
            result.append({
                "date": date.strftime("%Y-%m-%d"),
                "gov": round(row['value_gov'], 2),
                "corp": round(row['value_corp'], 2),
                "spread": round(row['spread'], 2)
            })
        
        print(f"✅ 데이터 처리 완료: {len(result)}건")

        return result

    except Exception as e:
        print(f"❌ [ECOS Error]: {e}")
        return generate_mock_spread()
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
        start_5y = (datetime.now() - timedelta(days=1825)).strftime('%Y-%m-%d')
        end_now = datetime.now().strftime('%Y-%m-%d')
        
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
        today_str = datetime.now().strftime("%Y%m%d")
        
        # 1) KOSPI PER (pykrx)
        curr_pe_kr = 0
        # 최근 5일 중 데이터 있는 날 찾기
        for i in range(5):
            target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
            try:
                # 1001 = 코스피
                df_fund = stock.get_index_fundamental(target_date, target_date, "1001")
                if not df_fund.empty:
                    # pykrx 버전에 따라 컬럼명이 다를 수 있음. 보통 'PER'
                    if 'PER' in df_fund.columns:
                        curr_pe_kr = df_fund['PER'].iloc[-1]
                        break
            except:
                continue
        
        if curr_pe_kr == 0: curr_pe_kr = 12.0 # Fallback
        
        # 2) KR 10Y Yield (ECOS API)
        kr_yield = 3.5 # Fallback
        if ecos_key:
            # 817Y002(시장금리 일별), 010210000(국고채 10년)
            # 최근 데이터만 필요하므로 시작일을 7일 전으로 설정
            start_recent = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
            url = f"http://ecos.bok.or.kr/api/StatisticSearch/{ecos_key}/json/kr/1/10/817Y002/D/{start_recent}/{today_str}/010210000"
            resp = requests.get(url).json()
            if 'StatisticSearch' in resp:
                kr_yield = float(resp['StatisticSearch']['row'][-1]['DATA_VALUE'])
        
        current_gap_kr = (1 / curr_pe_kr) * 100 - kr_yield
        
        # 3) 5년 평균
        # KOSPI 5년 PER 평균
        avg_pe_kr_5y = 11.0 # Fallback
        start_5y_kr = (datetime.now() - timedelta(days=1825)).strftime('%Y%m%d')
        try:
             df_hist_pe = stock.get_index_fundamental(start_5y_kr, today_str, "1001")
             if not df_hist_pe.empty and 'PER' in df_hist_pe.columns:
                 avg_pe_kr_5y = df_hist_pe['PER'].replace(0, np.nan).dropna().mean()
        except Exception as e:
             print(f"PyKrx Hist Error: {e}")
             
        # KR 10Y 5년 금리 평균 (ECOS)
        avg_yield_kr_5y = 2.5 # Fallback
        if ecos_key:
            url_avg = f"http://ecos.bok.or.kr/api/StatisticSearch/{ecos_key}/json/kr/1/2000/817Y002/D/{start_5y_kr}/{today_str}/010210000"
            resp_avg = requests.get(url_avg).json()
            if 'StatisticSearch' in resp_avg:
                vals = [float(r['DATA_VALUE']) for r in resp_avg['StatisticSearch']['row']]
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
