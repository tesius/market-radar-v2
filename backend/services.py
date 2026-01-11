import yfinance as yf
import pandas as pd
from cachetools import cached, TTLCache
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caches
# Stock data: 10 minutes cache
stock_cache = TTLCache(maxsize=100, ttl=600)
# Macro data: 24 hours cache
macro_cache = TTLCache(maxsize=100, ttl=86400)

@cached(stock_cache)
def fetch_daily_data(ticker: str):
    """
    Fetches current price, change, and 90-day history for a given ticker.
    Handles fallback for specific tickers like ^TNX utilizing FRED data logic if needed.
    """
    try:
        # Special handling for TNX fallback logic
        if ticker == "^TNX":
            data = _fetch_yfinance_data(ticker)
            if data is None:
                logger.warning(f"Failed to fetch {ticker} from yfinance, attempting fallback to FRED DGS10")
                return _fetch_fred_series("DGS10", "10-Year Treasury Constant Maturity Rate")
            return data
        
        return _fetch_yfinance_data(ticker)
    except Exception as e:
        logger.error(f"Error fetching data for {ticker}: {e}")
        return None

def _fetch_yfinance_data(ticker: str):
    """Helper to fetch data from yfinance"""
    try:
        stock = yf.Ticker(ticker)
        # Get 90 day history
        hist = stock.history(period="3mo")
        
        if hist.empty:
            return None
            
        # Get current data
        # Use simple fallback if regularMarketPrice is missing, or use the last close
        current_price =  hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close != 0 else 0
        
        # Prepare history for chart
        history_data = []
        for date, row in hist.iterrows():
            history_data.append({
                "date": date.strftime('%Y-%m-%d'),
                "close": round(row['Close'], 2)
            })
            
        return {
            "symbol": ticker,
            "current_price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "history": history_data
        }
    except Exception as e:
        logger.error(f"Internal yfinance error for {ticker}: {e}")
        return None

def _fetch_fred_series(series_id: str, title: str):
    """
    Fetches data from FRED via direct CSV download since fredapi is potentially not installed.
    URL: https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}
    """
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        df = pd.read_csv(url, index_col='DATE', parse_dates=True)
        
        if df.empty:
            return None
            
        # Sort just in case
        df = df.sort_index()
        
        # FRED CSVs often use '.' for missing data
        df = df.replace('.', pd.NA).dropna()
        df[series_id] = pd.to_numeric(df[series_id])
        
        # Last 90 days roughly (or last 60 points)
        # FRED data might be monthly or daily depending on series.
        # DGS10 is daily. CPI/UNRATE are monthly.
        
        latest_date = df.index[-1]
        latest_val = df[series_id].iloc[-1]
        
        prev_val = df[series_id].iloc[-2] if len(df) > 1 else latest_val
        change = latest_val - prev_val
        change_percent = (change / prev_val) * 100 if prev_val != 0 else 0
        
        # Get last 90 days of data for history
        cutoff_date = latest_date - timedelta(days=90)
        hist_df = df[df.index >= cutoff_date]
        
        history_data = []
        for date, row in hist_df.iterrows():
            history_data.append({
                "date": date.strftime('%Y-%m-%d'),
                "value": round(row[series_id], 2)
            })
            
        return {
            "symbol": series_id,
            "name": title,
            "current_price": round(latest_val, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "history": history_data,
            "last_updated": latest_date.strftime('%Y-%m-%d')
        }

    except Exception as e:
        logger.error(f"Error fetching FRED series {series_id}: {e}")
        return None

@cached(macro_cache)
def fetch_macro_data_from_fred(indicator_type: str):
    """
    Fetches macro data.
    indicator_type: 'cpi' (CPIAUCSL) or 'unemployment' (UNRATE)
    """
    series_map = {
        'cpi': ('CPIAUCSL', 'Consumer Price Index'), # CPI for All Urban Consumers: All Items in U.S. City Average
        'unrate': ('UNRATE', 'Unemployment Rate')
    }
    
    if indicator_type not in series_map:
        return {"error": "Invalid indicator type"}
        
    series_id, title = series_map[indicator_type]
    
    try:
        data = _fetch_fred_series(series_id, title)
        if data:
            # Macro data often needs YoY calculation for CPI context
            # CPI is usually an index, user might want inflation rate (YoY change).
            # The prompt asks for "CPI YoY data".
            # If it's CPI, we should calculate YoY change from the index.
            if indicator_type == 'cpi':
                return _calculate_cpi_yoy(series_id)
            return data
        return None
    except Exception as e:
        logger.error(f"Error fetching macro data {indicator_type}: {e}")
        return None

def _calculate_cpi_yoy(series_id="CPIAUCSL"):
    """
    Calculates YoY Change for CPI.
    Formula: ((Current CPI - CPI 1 year ago) / CPI 1 year ago) * 100
    """
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        df = pd.read_csv(url, index_col='DATE', parse_dates=True)
        df = df.sort_index()
        
        if df.empty:
            return None
            
        latest_date = df.index[-1]
        latest_cpi = df[series_id].iloc[-1]
        
        # Get date 1 year ago
        year_ago_date = latest_date - pd.DateOffset(years=1)
        
        # Find closest date
        try:
            # asof is good for finding closest prior match, but index must be sorted
            # truncate to year ago month for simple lookup if exact match missing?
            # FRED CPI is monthly (1st of month).
            
            # Simple approach: filter df for dates <= year_ago_date and take last
            # Or simplified: iloc[-13] if monthly data is strictly continuous
            
            if len(df) > 12:
                prev_year_cpi = df[series_id].iloc[-13]
                prev_year_date = df.index[-13]
                
                # Verify it's roughly 1 year diff
                days_diff = (latest_date - prev_year_date).days
                if not (360 <= days_diff <= 370):
                     # fallback to time based search
                     mask = df.index <= year_ago_date
                     if mask.any():
                         prev_year_cpi = df[mask][series_id].iloc[-1]
                     else:
                         return None
            else:
                return None
            
            yoy_inflation = ((latest_cpi - prev_year_cpi) / prev_year_cpi) * 100
            
            # Calculate history of YoY for the last 13 months (to show trend)
            history_yoy = []
            # We need at least 25 months of data to calculate 13 months of YoY
            if len(df) >= 25:
                # subsets for the last 13 months
                target_months = df.iloc[-13:]
                
                for date, row in target_months.iterrows():
                    current_cpi = row[series_id]
                    # Find exactly 1 year ago from this month
                    year_ago_date = date - pd.DateOffset(years=1)
                    
                    # Fuzzy match for 1 year ago (same month, previous year)
                    # Since FRED dates are usually 1st of month
                    mask = (df.index.year == year_ago_date.year) & (df.index.month == year_ago_date.month)
                    prev_df = df[mask]
                    
                    if not prev_df.empty:
                        prev_cpi = prev_df[series_id].iloc[0]
                        rate = ((current_cpi - prev_cpi) / prev_cpi) * 100
                        history_yoy.append({
                            "date": date.strftime('%Y-%m-%d'),
                            "value": round(rate, 2)
                        })

            return {
                "symbol": "CPI",
                "name": "US CPI (YoY)",
                "current_rate": round(yoy_inflation, 2),
                "last_updated": latest_date.strftime('%Y-%m-%d'),
                "history": history_yoy
            }

        except Exception as e:
            logger.error(f"Error calculating YoY: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error in _calculate_cpi_yoy: {e}")
        return None
