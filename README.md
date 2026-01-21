# 📡 Market Radar v2.0

**Market Radar v2.0**은 글로벌 금융 시장의 핵심 트렌드, 거시 경제 지표, 그리고 잠재적 리스크 신호를 실시간으로 모니터링하는 전문적인 금융 대시보드입니다.

FastAPI 기반의 강력한 백엔드는 **APScheduler**를 통해 주기적으로 데이터를 수집·가공하여 인메모리 스토어에 최신 상태를 유지하며, React 프론트엔드는 이를 바탕으로 직관적이고 반응성 높은 시각화를 제공합니다.

---

## ✨ 주요 기능 (Key Features)

### 1. 실시간 마켓 펄스 (Market Pulse)
- **글로벌 핵심 자산 모니터링:**
  - 🇺🇸 미국: S&P 500, 나스닥 100, 10년물 국채 금리 (`^TNX`)
  - 🇰🇷 한국: 코스피, 원/달러 환율 (`KRW=X`)
  - 🇯🇵 일본: 니케이 225
  - 🌐 기타: 신흥국 ETF (`EEM`), 변동성 지수 (`^VIX`)
- **스파크라인(Sparkline):** 최근 3개월 가격 흐름을 미니 차트로 시각화.

### 2. 시장 밸류에이션 (Yield Gap)
주식 기대수익률(1/PER)과 무위험 채권 금리를 비교하여 시장의 고평가/저평가 여부를 판독합니다.
- **🇺🇸 US Market:** S&P 500 Earnings Yield vs US 10Y Treasury
  - 판정: 저평가 / 적정 / 고평가(과열)
- **🇰🇷 KR Market:** KOSPI Earnings Yield vs KR 10Y Treasury
  - 판정: 적극 매수 / 관망 / 매도
- **Visual:** 현재 위치를 최근 5년 평균 범위와 비교하는 Gauge Chart 제공.

### 3. 거시 경제 지표 (Macro Health)
- **🇺🇸 CPI (소비자 물가 지수):** 전년 대비 물가 상승률(YoY) 및 연준 타겟(2%) 비교.
- **🇺🇸 Unemployment Rate (실업률):** 고용 시장 건전성 모니터링 (3.5%~4.0% 자연 실업률 레벨 체크).

### 4. 리스크 레이더 (Risk Radar)
- **Gold/Silver Ratio:** 전통적인 안전자산 선호 심리 지표.
- **Ratio vs S&P 500:** 실물 자산 비율과 주식 시장 간의 괴리를 분석하여 잠재적 위기 신호 탐지.

### 5. 크레딧 마켓 (Credit Spread)
- **High Yield Spread:** 기업의 자금 조달 리스크 측정.
- **KR Spread:** 회사채(AA-, 3년) - 국고채(3년) 금리 차이 추적 (ECOS API 활용).

### 6. 단기 자금 동향 (Rate Spread)
단기 시장의 유동성 경색 여부를 파악합니다.
- **🇰🇷 Call vs Base:** 한국 콜금리(1일물)와 한국은행 기준금리 스프레드.
- **🇺🇸 Fed Funds vs 3M:** 미국 실효연방기금금리(EFFR)와 3개월 국채 금리 스프레드.

---

## 🛠 기술 스택 (Tech Stack)

### Frontend
- **Core:** React 18, Vite
- **Styling:** Tailwind CSS (Dark Mode 지원)
- **Visualization:** Recharts (Responsive Charts)
- **Icons:** Lucide React
- **HTTP Client:** Axios

### Backend
- **Core:** FastAPI (Python 3.11+)
- **Scheduler:** APScheduler (Background Task Management)
- **Data Sources:**
  - `yfinance`: 글로벌 주식, 채권, 환율 데이터
  - `pykrx`: 한국 주식 시장 펀더멘털 (PER/PBR)
  - `fredapi`: 미국 거시 경제 데이터 (FRED)
  - `requests`: 한국은행 경제통계시스템 (ECOS) 직접 호출
- **Data Processing:** Pandas, NumPy
- **Caching:** In-Memory Data Store with periodic updates

---

## 📂 프로젝트 구조

```text
market-radar/
├── backend/
│   ├── services/           # 데이터 소스별 로직 분리
│   │   ├── stock_service.py    # yfinance 관련
│   │   ├── macro_service.py    # FRED, ECOS 거시 지표
│   │   ├── bond_service.py     # 채권 및 스프레드
│   │   └── analysis_service.py # 복합 분석 (Yield Gap, Risk 등)
│   ├── scheduler.py        # APScheduler 설정 및 데이터 갱신 로직
│   ├── main.py             # FastAPI 앱 및 엔드포인트
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # 각종 차트 및 카드 컴포넌트
│   │   ├── App.jsx         # 메인 대시보드 레이아웃
│   │   └── api.js          # API 호출 모듈
│   └── tailwind.config.js
└── README.md
```

---

## 🚀 설치 및 실행 (Getting Started)

### 사전 준비 요구사항
- Python 3.9 이상
- Node.js 18 이상
- **API Keys 준비:**
  - `FRED_API_KEY`: [FRED Website](https://fred.stlouisfed.org/docs/api/api_key.html)
  - `ECOS_API_KEY`: [한국은행 ECOS](https://ecos.bok.or.kr/jsp/openapi/OpenApiController.jsp)

### 1. 백엔드 실행
```bash
cd backend

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일 생성)
echo "FRED_API_KEY=your_key" > .env
echo "ECOS_API_KEY=your_key" >> .env

# 서버 실행 (자동으로 스케줄러가 시작되어 데이터를 수집합니다)
uvicorn main:app --reload --port 8000
```

### 2. 프론트엔드 실행
```bash
cd frontend

# 패키지 설치
npm install

# 개발 서버 시작
npm run dev
```

### 3. Docker 실행 (Optional)
```bash
# 백엔드 빌드 및 실행
docker build -t market-radar-backend ./backend
docker run -p 8080:8080 --env-file ./backend/.env market-radar-backend
```

---

## 📝 License
This project is licensed under the MIT License.
