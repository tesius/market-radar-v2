# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Market Radar v2.0 is a real-time financial dashboard monitoring global markets, macroeconomic indicators, and risk signals. It has a Python FastAPI backend and a React (Vite) frontend deployed separately.

## Development Commands

### Backend (in `backend/`)
```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run dev server
uvicorn main:app --reload --port 8000

# Run with Docker
docker build -t market-radar-backend . && docker run -p 8080:8080 --env-file .env market-radar-backend
```

### Frontend (in `frontend/`)
```bash
npm install
npm run dev        # Dev server at localhost:5173
npm run build      # Production build to dist/
npm run lint       # ESLint
npm run preview    # Preview production build
```

No test framework is configured for either backend or frontend.

## Architecture

### Data Flow
External APIs (yfinance, FRED, ECOS, pykrx) → APScheduler (20-min interval) → In-memory `DATA_STORE` dict → FastAPI endpoints → Axios client → React components

### Backend (`backend/`)
- **`main.py`** — FastAPI app with lifespan hooks, CORS config, and all API route definitions
- **`scheduler.py`** — APScheduler setup, the global `DATA_STORE` dictionary, and the `update_all_data()` orchestrator that calls each service
- **`services/`** — Domain-separated modules:
  - `stock_service.py` — yfinance market data (stocks, indices, rates, VIX)
  - `macro_service.py` — FRED API for US macro indicators (CPI, unemployment)
  - `bond_service.py` — ECOS API for Korean bond/rate data
  - `analysis_service.py` — Composite analysis (Risk Ratio, Yield Gap, Rate Spreads)

Key patterns:
- All endpoints read from the in-memory `DATA_STORE` for sub-10ms responses; no database
- Services use `@cached` decorators with TTL (60s market, 1h analysis, 24h macro)
- Services include fallback mock data generation when API calls fail
- pykrx logging noise is suppressed via log filters

### Frontend (`frontend/src/`)
- **`App.jsx`** — Main dashboard component with all state management (useState/useEffect)
- **`api.js`** — Axios instance configured with base URL from `VITE_API_URL` env var
- **`components/`** — Each chart/card type is a separate component using Recharts for visualization
- Tailwind CSS with dark mode via `class` strategy

### API Endpoints
| Endpoint | Description |
|---|---|
| `/api/market/pulse` | 8 key market indicators with sparklines |
| `/api/macro/cpi` | US CPI YoY % |
| `/api/macro/unrate` | US unemployment rate |
| `/api/macro/risk-ratio` | Gold/Silver ratio vs S&P 500 |
| `/api/market/credit-spread` | KR corp-govt bond spread |
| `/api/market/yield-gap` | Earnings yield vs bond yield (US+KR) |
| `/api/macro/rate-spread` | KR Call Rate vs Base Rate |
| `/api/macro/us-rate-spread` | US EFFR vs 3M Treasury |

## Environment Variables

Backend requires `.env` in `backend/` with:
- `FRED_API_KEY` — Federal Reserve Economic Data API key
- `ECOS_API_KEY` — Bank of Korea Economic Statistics API key

Frontend uses `VITE_API_URL` (defaults to `http://127.0.0.1:8080` in dev, set in `.env.production` for prod).

## Deployment

- **Backend**: Fly.io (`fly.toml` in `backend/`, Tokyo/nrt region, 1GB RAM)
- **Frontend**: GitHub Pages via `.github/workflows/deploy-frontend.yml` (triggers on push to `main` affecting `frontend/**`)
- Base path for frontend is `/market-radar-v2/` (configured in `vite.config.js`)
