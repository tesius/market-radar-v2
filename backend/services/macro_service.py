import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from cachetools import TTLCache, cached
from fredapi import Fred
from dotenv import load_dotenv
import os

load_dotenv()

# 캐시 설정
macro_cache = TTLCache(maxsize=100, ttl=86400)

# API 키 설정
fred_key = os.getenv("FRED_API_KEY")
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


# 2. Macro Health
@cached(cache=macro_cache)
def get_macro_data(series_id, label):
    data = []
    
    # 비상용 가짜 데이터 (서버 다운 방지)
    def generate_mock_data():
        print(f"⚠️ [Fallback] {label} - Mock Data Used")
        mock = []
        base = 3.5 if "Unemployment" in label else 3.0 # CPI도 이제 %니까 3.0 근처로
        for i in range(24):
            # KST 기준 오늘 날짜 (목 데이터 생성 시에도 일관성 유지)
            d = datetime.now(ZoneInfo("Asia/Seoul")) - timedelta(days=30 * (23 - i))
            val = base + (i % 5) * 0.1
            mock.append({"date": d.strftime("%Y-%m-%d"), "value": round(val, 2)})
        return mock

    try:
        # 데이터 넉넉하게 가져오기 (변동률 계산 위해 1년 더 필요)
        # KST 기준으로 '현재' 시점 설정
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        start = datetime(2014, 1, 1) 
        end = now_kst
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
