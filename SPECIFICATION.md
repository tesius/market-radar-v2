# Market Radar v2.0 - Project Specification

## 1. Overview
**Market Radar v2.0** is a real-time financial dashboard designed to monitor global market trends, macroeconomic indicators, and risk signals. It provides a consolidated view of key asset classes, economic health, and potential market risks using a modern React frontend and a robust FastAPI backend powered by APScheduler for background data synchronization.

## 2. System Architecture
- **Frontend**: React (Vite), Tailwind CSS (Dark Mode), Recharts, Lucide React icons.
- **Backend**: FastAPI (Python), APScheduler (Background Tasks), Pandas, NumPy.
- **Data Sources**: yfinance, pykrx, FRED API, ECOS API (Bank of Korea).
- **Persistence**: In-Memory Data Store (periodically updated by scheduler).
- **Communication**: REST API (Axios).

## 3. Backend Specification
### 3.1. Architecture Pattern
- **Service Layer**: Business logic separated by domain (`stock_service.py`, `macro_service.py`, `bond_service.py`, `analysis_service.py`).
- **Scheduler**: `APScheduler` runs background jobs every 20 minutes to fetch new data and update the global `DATA_STORE`.
- **API endpoints**: Read directly from `DATA_STORE` for < 10ms response times.

### 3.2. API Endpoints
Base URL: `http://localhost:8000`

#### **1. Market Pulse**
- **GET** `/api/market/pulse`
- **Data**: Global assets (S&P 500, KOSPI, Nikkei, Rates, VIX, etc.)
- **Fields**: Price, Change, Change %, Sparkline (3mo).

#### **2. Macro Indicators**
- **GET** `/api/macro/cpi`
  - US CPI YoY % Change (Target: 2%).
- **GET** `/api/macro/unrate`
  - US Unemployment Rate (Natural Rate check).
- **GET** `/api/macro/risk-ratio`
  - Gold/Silver Ratio vs S&P 500 correlation.

#### **3. Credit & Rates**
- **GET** `/api/market/credit-spread`
  - **KR Credit Spread**: Corp Bond AA- (3Y) minus Gov Bond (3Y). Provides insight into corporate credit risk.
- **GET** `/api/market/yield-gap`
  - **US**: S&P 500 Earnings Yield vs US 10Y Treasury.
  - **KR**: KOSPI Earnings Yield vs KR 10Y Treasury.
  - **Interpretation**: Current gap vs 5-Year Average (Undervalued/Overvalued).
- **GET** `/api/macro/rate-spread`
  - **KR Call-Base**: Call Rate (1D) vs Base Rate.
- **GET** `/api/macro/us-rate-spread`
  - **US Spread**: EFFR vs 3M Treasury.

### 3.3. Data Providers
- **yfinance**: Global tickers (`^GSPC`, `^TNX`, `KRW=X`).
- **pykrx**: Korean market fundamentals (KOSPI PER/PBR).
- **FRED**: US Macro data (`CPIAUCSL`, `UNRATE`, `DGS10`, `EFFR`, `DTB3`).
- **ECOS (Bank of Korea)**: KR Treasury Bonds (3Y, 10Y), Base Rate, Call Rate.

## 4. Frontend Specification
### 4.1. Core Components
- **MetricCard**: Reusable card for Market Pulse items with sparklines.
- **MacroChart**: Area charts for economic indicators with target references.
- **RiskChart**: Composite chart (Line + Area) for Gold/Silver ratio.
- **CreditSpreadChart**: Visualization of credit risk over time.
- **MarketGauge**: Custom gauge component for Yield Gap valuation judgment.
- **RateSpreadChart**: Bar/Line chart for short-term liquidity monitoring.

### 4.2. Features
- **Dark/Light Mode**: Fully supported via Tailwind `dark:` classes.
- **Responsive Design**: Mobile-first grid layouts.
- **Auto-Refresh**: Data re-fetched on user request or page reload.
- **Resilient UI**: Skeleton loaders during data fetch; Error states for missing data.

## 5. Technology Stack Details
- **Python**: 3.11+
- **Backend Libs**: `fastapi`, `uvicorn`, `apscheduler`, `yfinance`, `pykrx`, `fredapi`, `requests`, `pandas`.
- **Frontend Libs**: `react`, `recharts`, `tailwindcss`, `axios`, `lucide-react`.
