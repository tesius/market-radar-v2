# 📡 Market Radar v2.0

**Market Radar v2.0**은 글로벌 시장 트렌드, 거시 경제 지표, 그리고 시장 리스크 신호를 실시간으로 모니터링하는 전문적인 금융 대시보드입니다. 현대적인 React 프론트엔드와 강력한 FastAPI 백엔드를 결합하여 자산 클래스별 동향과 경제 건강 상태를 한눈에 파악할 수 있도록 돕습니다.

---

## ✨ 주요 기능

### 1. 실시간 마켓 펄스 (Market Pulse)
- 8가지 핵심 시장 지표 실시간 추적:
  - 미국 10년물 국채 금리 (`^TNX`)
  - 원/달러 환율 (`KRW=X`)
  - 변동성 지수 (`^VIX`)
  - 나스닥 100 (`^NDX`)
  - S&P 500 (`^GSPC`)
  - 니케이 225 (`^N225`)
  - 신흥국 시장 (`EEM`)
  - 코스피 (`^KS11`)
- 변동률 시각화 및 개별 자산 히스토리 스파크라인 제공.

### 2. 거시 경제 지표 분석 (Macro Indicators)
- **US CPI (소비자 물가 지수):** 물가 상승 추이 및 연준의 타겟 금리 대비 현황 시각화.
- **Unemployment Rate (실업률):** 고용 시장의 건강 상태 모니터링.
- 1년, 5년, 10년 및 전체 기간 필터링 기능 제공.

### 3. 리스크 레이더 (Risk Radar)
- **금/은 비율(Gold/Silver Ratio) vs S&P 500:** 실물 자산 간의 비율과 주식 시장의 상관관계 및 괴리율 분석을 통한 위험 신호 포착.
- 이중 Y축 차트를 활용한 직관적인 데이터 비교.

---

## 🛠 기술 스택

### Frontend
- **Framework:** React (Vite)
- **Styling:** Tailwind CSS
- **Visualization:** Recharts
- **Icons:** Lucide React
- **API Client:** Axios

### Backend
- **Framework:** FastAPI (Python 3.9+)
- **Data Source:** `yfinance` (금융 데이터), FRED (거시 지표)
- **Data Processing:** Pandas, NumPy
- **Caching:** `cachetools` (API 호출 최적화 및 속도 향상)

---

## 🚀 시작하기

### 사전 준비 사항
- Python 3.9 이상
- Node.js 18 이상
- (선택 사항) FRED API Key (지표 데이터 백업용)

### 1. 백엔드 설정 (Backend)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
`.env` 파일을 생성하고 필요한 환경 변수를 설정합니다.
```env
FRED_API_KEY=your_api_key_here
```
서버 실행:
```bash
python main.py
# 또는
uvicorn main:app --reload --port 8000
```

### 2. 프론트엔드 설정 (Frontend)
```bash
cd frontend
npm install
npm run dev
```

### 3. Docker 사용 (선택 사항)
```bash
docker build -t market-radar-backend ./backend
docker run -p 8080:8080 market-radar-backend
```

---

## 📂 프로젝트 구조

```text
market-radar/
├── backend/            # FastAPI 기반 서버
│   ├── services/       # 데이터 수집 및 가공 로직
│   ├── main.py         # API 엔트리 엔드포인트
│   └── requirements.txt
├── frontend/           # React 기반 대시보드
│   ├── src/
│   │   ├── components/ # UI 컴포넌트 (Chart, Card 등)
│   │   └── api.js      # 백엔드 API 라이브러리
│   └── package.json
└── SPECIFICATION.md     # 프로젝트 상세 명세서
```

---

## 📝 라이선스
이 프로젝트는 MIT 라이선스 하에 배포됩니다.
