import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def fetch_data(ticker, period="1y", interval="1d"):
    """
    Fetches historical market data for a given ticker.
    
    Args:
        ticker (str): The stock symbol (e.g., "AAPL") or crypto (e.g., "BTC-USD").
        period (str): The history period to download (default "1y").
        interval (str): The data interval (default "1d").
        
    Returns:
        pd.DataFrame: DataFrame containing the historical data.
    """
    try:
        data = yf.download(ticker, period=period, interval=interval, progress=False, multi_level_index=False)
        
        # Handle potential MultiIndex columns (common in newer yfinance versions)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        # Deduplicate columns if any (e.g. sometimes yfinance returns duplicate columns)
        data = data.loc[:, ~data.columns.duplicated()]
        
        if data.empty:
            print(f"[DataLoader] Warning: No data found for {ticker}")
            return None
        return data
    except Exception as e:
        print(f"[DataLoader] Error fetching data for {ticker}: {e}")
        return None


def fetch_batch_data(tickers, period="1y", interval="1d", max_workers=5):
    """
    Fetches data for multiple tickers using yfinance batch download.
    
    Args:
        tickers (list): List of ticker symbols
        period (str): History period
        interval (str): Data interval
        max_workers (int): Ignored (kept for compatibility)
        
    Returns:
        dict: Dictionary mapping ticker -> DataFrame
    """
    if not tickers:
        return {}
        
    results = {}
    try:
        # Use yfinance native batch download which is faster and more reliable
        data = yf.download(tickers, period=period, interval=interval, group_by='ticker', progress=False, threads=True)
        
        if data.empty:
            return {}
            
        # Check if we got a single level content (if only 1 ticker passed effectively) or MultiIndex
        if len(tickers) == 1:
            # Re-use fetch_data logic for single ticker consistency or wrap
            # But yf.download with list might return scalar columns if length is 1
            ticker = tickers[0]
            if not data.empty:
                 results[ticker] = data
            return results
            
        # If multiple tickers, columns should be MultiIndex (Ticker, Price) due to group_by='ticker'
        if isinstance(data.columns, pd.MultiIndex):
            # Iterate through the top level (Tickers)
            # Valid tickers will be in the top level
            # Note: yfinance might change levels based on auto_adjust. 
            # With group_by='ticker', level 0 is Ticker.
            
            # Get valid tickers present in columns
            downloaded_tickers = data.columns.levels[0]
            
            for ticker in downloaded_tickers:
                if ticker in tickers: # Ensure we only get what we asked for
                    ticker_df = data[ticker].copy()
                    if not ticker_df.empty:
                         # Drop NaNs if any (e.g. some days missing) - optional
                         # ticker_df.dropna(how='all', inplace=True) 
                         results[ticker] = ticker_df
        else:
            # Fallback if something weird happens or structure is different
            print("[DataLoader] Warning: Batch download returned unexpected structure.")
            
    except Exception as e:
        print(f"[DataLoader] Error in batch fetch: {e}")
            
    return results


def get_ticker_info(ticker):
    """
    Get basic info about a ticker (market cap, volume, etc.).
    
    Args:
        ticker (str): Ticker symbol
        
    Returns:
        dict: Ticker info or None if error
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract key metrics
        return {
            'ticker': ticker,
            'market_cap': info.get('marketCap', 0),
            'avg_volume': info.get('averageVolume', 0),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'name': info.get('shortName', ticker)
        }
    except Exception as e:
        # Silently fail for info (not critical)
        return {
            'ticker': ticker,
            'market_cap': 0,
            'avg_volume': 0,
            'sector': 'Unknown',
            'industry': 'Unknown',
            'name': ticker
        }


def passes_filters(ticker_info, min_market_cap=0, min_volume=0):
    """
    Check if ticker passes basic filters.
    
    Args:
        ticker_info (dict): Ticker info from get_ticker_info
        min_market_cap (int): Minimum market cap
        min_volume (int): Minimum average volume
        
    Returns:
        bool: True if passes filters
    """
    if min_market_cap > 0 and ticker_info.get('market_cap', 0) < min_market_cap:
        return False
    
    if min_volume > 0 and ticker_info.get('avg_volume', 0) < min_volume:
        return False
    
    return True

