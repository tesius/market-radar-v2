# Market Radar v2.0 - Project Specification

## 1. Overview
**Market Radar v2.0** is a real-time financial dashboard designed to monitor global market trends, macroeconomic indicators, and risk signals. It provides a consolidated view of key asset classes, economic health, and potential market risks using a modern React frontend and a robust FastAPI backend.

## 2. System Architecture
- **Frontend**: React (Vite), Tailwind CSS, Recharts, Lucide React icons.
- **Backend**: FastAPI (Python), Pandas, yfinance, cachetools.
- **Communication**: REST API (Axios).
- **Deployment**: Localhost (Dev mode).

## 3. Backend Specification
### 3.1. API Endpoints
Base URL: `http://localhost:8000`

#### **GET /api/market/pulse**
- **Purpose**: Retrieves current data for 8 key market indicators.
- **Source**: `yfinance` (Real-time/Delayed).
- **Indicators**:
  - `^TNX` (US 10Y Treasury)
  - `KRW=X` (USD/KRW)
  - `^VIX` (Volatility Index)
  - `^NDX` (Nasdaq 100)
  - `^GSPC` (S&P 500)
  - `^N225` (Nikkei 225)
  - `EEM` (Emerging Markets)
  - `^KS11` (KOSPI)
- **Response Structure**:
  ```json
  [
    {
      "ticker": "^TNX",
      "name": "미국 10년물 금리",
      "price": 4.12,
      "change": 0.05,
      "change_percent": 1.23,
      "display_change": "+0.05 (+1.23%)",
      "history": [{"date": "2024-01-01", "value": 4.0}, ...]
    },
    ...
  ]
  ```

#### **GET /api/macro/cpi**
- **Purpose**: Retrieves US CPI (Consumer Price Index) Year-over-Year (YoY) change.
- **Source**: FRED (`CPIAUCSL`) via `pandas_datareader` (Fallback: Mock Data).
- **Logic**: Calculates YoY % change from index values.
- **Response Structure**:
  ```json
  {
    "title": "US CPI (Consumer Price Index)",
    "data": [{"date": "2024-01-01", "value": 3.4}, ...]
  }
  ```

#### **GET /api/macro/unrate**
- **Purpose**: Retrieves US Unemployment Rate.
- **Source**: FRED (`UNRATE`) via `pandas_datareader` (Fallback: Mock Data).
- **Response Structure**: Similar to CPI.

#### **GET /api/macro/risk-ratio**
- **Purpose**: Analyzes market risk by comparing Gold/Silver ratio with S&P 500.
- **Source**: `yfinance` (`GC=F`, `SI=F`, `^GSPC`).
- **Logic**: 
  - Fetches 1-year history.
  - Merges dataframes on Date.
  - Calculates `Ratio = Gold / Silver`.
  - Returns `Ratio` and `S&P 500` price for correlation analysis.
- **Response Structure**:
  ```json
  [
    {
      "date": "2024-01-01",
      "ratio": 85.4,
      "sp500": 4700.5
    },
    ...
  ]
  ```

### 3.2. Caching Strategy
- **Stock Data (Pulse)**: TTL 600s (10 mins).
- **Risk Data**: TTL 600s (10 mins).
- **Macro Data**: TTL 86400s (24 hours).
- **Implementation**: `cachetools.TTLCache`.

### 3.3. Fallback Mechanisms
- **Market Data**: Skips individual tickers on failure.
- **Macro Data**: Generates synthetic mock data if FRED API fails or data is empty.
- **Risk Data**: Generates synthetic mock data if insufficient history (< 10 points).

## 4. Frontend Specification
### 4.1. Components
#### **App.jsx** (Main Container)
- Fetches all data on mount (`useEffect`).
- Manages state: `pulseData`, `cpiData`, `unrateData`, `riskData`.
- Handles loading states and "Refresh" button.
- Uses `Promise.allSettled` to ensure partial failures (e.g., Macro failing) don't block the UI.

#### **MetricCard.jsx**
- Displays single indicator: Name, Value, Change (Abs/%), Sparkline (AreaChart).
- Dynamic styling: Green (Positive), Red (Negative), Gray (Neutral).

#### **MacroChart.jsx**
- Displays Macro indicators (CPI, Unemployment).
- Feature: Time range filtering (1Y, 5Y, 10Y, MAX).
- Visual: Gradient AreaChart with Reference Line (Target 2% for CPI).

#### **RiskChart.jsx**
- Composed Chart (Line + Area) to show correlation/divergence.
- Dual Y-Axis: Left (S&P 500), Right (Gold/Silver Ratio).

## 5. Technology Stack Details
- **Python Version**: 3.9+ recommended.
- **Key Libraries**:
  - `fastapi`, `uvicorn`: Web Server.
  - `yfinance`: Market Data.
  - `pandas`, `pandas_datareader`: Data manipulation.
  - `cachetools`: Caching.
- **React**:
  - `recharts`: Visualization.
  - `tailwindcss`: Styling.
  - `axios`: API Client.
