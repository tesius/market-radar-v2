import requests
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

ECOS_API_KEY = os.getenv("ECOS_API_KEY")

def check_ecos():
    if not ECOS_API_KEY:
        print("❌ ECOS_API_KEY is not set in .env")
        return

    print(f"🔑 Using API KEY: {ECOS_API_KEY[:4]}****")
    
    # Test Config: Base Rate (Last 10 Days)
    url = f"http://ecos.bok.or.kr/api/StatisticSearch/{ECOS_API_KEY}/json/kr/1/10/722Y001/D/20250101/20260120/0101000"
    
    print(f"📡 Requesting: {url.replace(ECOS_API_KEY, 'API_KEY')}")
    
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        
        if 'StatisticSearch' in data:
            row_count = data['StatisticSearch']['list_total_count']
            rows = data['StatisticSearch']['row']
            print(f"✅ Success! Found {row_count} total records.")
            print(f"📊 Recent Data (Top 5):")
            for r in rows[:5]:
                print(f"   - {r['TIME']}: {r['DATA_VALUE']}")
        else:
            print(f"⚠️ Error Response: {data}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    check_ecos()
