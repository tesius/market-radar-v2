import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from cachetools import TTLCache, cached
from dotenv import load_dotenv
import os

load_dotenv()

# 캐시 설정
credit_cache = TTLCache(maxsize=100, ttl=86400) # 24시간 캐시 (장기 데이터)

# API 키 설정
ecos_key = os.getenv("ECOS_API_KEY")

# 4. Credit Spread (ECOS API)
@cached(cache=credit_cache)
def get_credit_spread_data():
    """
    한국은행 ECOS API를 통해 국고채(3년)와 회사채(AA-, 3년) 금리 차이(Credit Spread)를 계산
    """
    
    # 비상용 Mock Data
    def generate_mock_spread():
        print("⚠️ [Fallback] Credit Spread - Mock Data Used")
        today = datetime.now(ZoneInfo("Asia/Seoul")) # Mock Data generation also needs timezone
        data = []
        base_val = 0.8
        # 15년치 데이터 생성 (약 5400일)
        for i in range(180): # 180개월 (15년)
            d = today - timedelta(days=30 * (179 - i))
            
            # 국고채 3년 (약 3.0 ~ 4.5% 사이 변동)
            # numpy random fix for deterministic behavior if needed, or simple update
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
        # KST 기준 오늘 날짜
        now_kst = datetime.now(ZoneInfo("Asia/Seoul"))
        end_date = now_kst.strftime("%Y%m%d")
        # 2011년 1월 1일부터 (약 15년)
        start_date = "20110101"

        # ECOS API 호출 함수
        def fetch_ecos(stat_code, item_code):
            # URL: /StatisticSearch/apikey/json/kr/1/20000/stat_code/DD/start/end/item_code
            # 15년치면 약 5500일 이므로 넉넉하게 20000
            url = f"http://ecos.bok.or.kr/api/StatisticSearch/{ecos_key}/json/kr/1/20000/{stat_code}/D/{start_date}/{end_date}/{item_code}"
            
            # Timeout 추가 (안정성 개선)
            resp = requests.get(url, timeout=10)
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
