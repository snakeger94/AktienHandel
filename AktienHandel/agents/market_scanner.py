from agents.base_agent import BaseAgent
from utils.data_loader import fetch_data, fetch_batch_data, get_ticker_info, passes_filters
from utils.universe_manager import UniverseManager
import config

class MarketScanner(BaseAgent):
    """
    Intelligent market scanner that efficiently scans large universes.
    Uses multi-stage filtering to identify best opportunities.
    """
    
    def __init__(self):
        super().__init__(name="Scanner", role="Market Scout")
        self.universe_mgr = UniverseManager()

    def run(self):
        """
        Scans the trading universe with intelligent filtering.
        
        Returns:
            list: Top candidates for deeper analysis
        """
        self.log("Starting market scan...")
        
        # Get universe based on config
        universe = self.universe_mgr.get_universe(
            mode=config.UNIVERSE_MODE,
            enable_crypto=config.ENABLE_CRYPTO,
            custom_list=config.CUSTOM_UNIVERSE if config.UNIVERSE_MODE == 'custom' else None
        )
        
        stocks = universe['stocks']
        crypto = universe['crypto']
        total_tickers = len(stocks) + len(crypto)
        
        self.log(f"Universe: {len(stocks)} stocks + {len(crypto)} crypto = {total_tickers} total")
        
        # Stage 1: Pre-filter by market cap and volume (stocks only)
        self.log("Stage 1: Pre-filtering by market cap and volume...")
        filtered_stocks = self._pre_filter_stocks(stocks)
        self.log(f"After pre-filtering: {len(filtered_stocks)} stocks remain")
        
        # All crypto passes pre-filter (different criteria)
        all_tickers = filtered_stocks + crypto
        self.log(f"Total to scan: {len(all_tickers)} tickers")
        
        # Stage 2: Technical screening
        self.log("Stage 2: Technical screening...")
        candidates = self._technical_screen(all_tickers)
        self.log(f"After technical screening: {len(candidates)} candidates")
        
        # Stage 3: Rank and select top N
        self.log("Stage 3: Ranking candidates...")
        top_candidates = self._rank_candidates(candidates)
        
        self.log(f"Scan complete. Returning top {len(top_candidates)} candidates for deep analysis.")
        return top_candidates
    
    def _pre_filter_stocks(self, stocks):
        """
        Pre-filter stocks by market cap and volume.
        This reduces the number of tickers to analyze.
        
        Args:
            stocks (list): List of stock tickers
            
        Returns:
            list: Filtered stock tickers
        """
        # Skip filtering if thresholds are 0
        if config.MIN_MARKET_CAP == 0 and config.MIN_AVG_VOLUME == 0:
            return stocks
        
        filtered = []
        
        # We don't want to fetch info for all stocks (too slow)
        # Instead, we'll just skip this filter for large universes
        # or sample a subset
        if len(stocks) > 50:
            self.log("Large universe detected - skipping market cap/volume pre-filter")
            return stocks
        
        for ticker in stocks:
            info = get_ticker_info(ticker)
            if passes_filters(info, config.MIN_MARKET_CAP, config.MIN_AVG_VOLUME):
                filtered.append(ticker)
        
        return filtered
    
    def _technical_screen(self, tickers):
        """
        Apply technical filters to identify interesting tickers.
        
        Args:
            tickers (list): List of tickers to screen
            
        Returns:
            list: Candidates with technical data
        """
        candidates = []
        stats = {'total': 0, 'insufficient_data': 0, 'low_momentum': 0, 'accepted': 0, 'fetch_failed': 0}
        
        # For large universes, batch fetch data
        if len(tickers) > 20:
            # Batch processing
            self.log(f"Batch fetching data for {len(tickers)} tickers...")
            data_dict = fetch_batch_data(tickers, period="6mo", max_workers=10)
            
            stats['total'] = len(tickers)
            stats['fetch_failed'] = len(tickers) - len(data_dict)
            
            for ticker in tickers:
                if ticker not in data_dict:
                    continue
                    
                df = data_dict[ticker]
                candidate, reason = self._analyze_ticker(ticker, df)
                if candidate:
                    candidates.append(candidate)
                    stats['accepted'] += 1
                else:
                    if reason == 'insufficient_data':
                        stats['insufficient_data'] += 1
                    else:
                        stats['low_momentum'] += 1
        else:
            # Sequential processing for small lists
            stats['total'] = len(tickers)
            for ticker in tickers:
                self.log(f"Checking {ticker}...")
                df = fetch_data(ticker, period="6mo")
                
                if df is None or df.empty:
                    stats['fetch_failed'] += 1
                    continue
                
                candidate, reason = self._analyze_ticker(ticker, df)
                if candidate:
                    candidates.append(candidate)
                    stats['accepted'] += 1
                else:
                    if reason == 'insufficient_data':
                        stats['insufficient_data'] += 1
                    else:
                        stats['low_momentum'] += 1
        
        self.log(f"Screening Stats: Checked {stats['total']} | Failed Fetch: {stats['fetch_failed']} | No Data: {stats['insufficient_data']} | Criteria Fail: {stats['low_momentum']} | Passed: {stats['accepted']}")
        return candidates
    
    def _analyze_ticker(self, ticker, df):
        """
        Analyze a single ticker for interesting signals.
        
        Args:
            ticker (str): Ticker symbol
            df (DataFrame): Price data
            
        Returns:
            dict: Candidate dict or None
        """
        try:
            # Ensure we have enough data (check for NON-NaN data)
            valid_closes = df['Close'].dropna()
            if len(valid_closes) < 50:
                return None, 'insufficient_data'

            current_price = valid_closes.iloc[-1]
            
            # Simple technical checks
            sma50 = valid_closes.rolling(window=50).mean().iloc[-1]
            sma20 = valid_closes.rolling(window=20).mean().iloc[-1]
            
            # Calculate momentum (20-day return)
            momentum = (current_price - valid_closes.iloc[-20]) / valid_closes.iloc[-20]
            
            # Calculate volume trend (fill info if volume missing)
            if 'Volume' in df.columns:
                avg_volume = df['Volume'].rolling(window=20).mean().iloc[-1]
                recent_volume = df['Volume'].iloc[-5:].mean()
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            else:
                volume_ratio = 1.0
            
            # Determine asset type
            asset_type = self.universe_mgr.get_asset_type(ticker)
            
            # Different criteria for stocks vs crypto
            if asset_type == 'crypto':
                # Crypto: Look for strong momentum and volume
                if momentum > 0.05 and volume_ratio > 1.0:  # 5% gain with volume
                    return {
                        'ticker': ticker,
                        'asset_type': 'crypto',
                        'reason': 'Crypto momentum with volume',
                        'price': float(current_price),
                        'sma50': float(sma50),
                        'sma20': float(sma20),
                        'momentum': float(momentum),
                        'volume_ratio': float(volume_ratio),
                        'score': float(momentum * 2 + volume_ratio)  # Prioritize momentum for crypto
                    }, None
            else:
                # Stocks: Traditional trend following
                # Price > SMA50 or strong recent momentum
                if current_price > sma50 or momentum > 0.03:
                    return {
                        'ticker': ticker,
                        'asset_type': 'stock',
                        'reason': 'Above SMA50' if current_price > sma50 else 'Positive momentum',
                        'price': float(current_price),
                        'sma50': float(sma50),
                        'sma20': float(sma20),
                        'momentum': float(momentum),
                        'volume_ratio': float(volume_ratio),
                        'score': float((current_price / sma50 - 1) + momentum)
                    }, None
            
            return None, 'criteria_fail'
            
        except Exception as e:
            self.log(f"Error analyzing {ticker}: {e}")
            return None, 'error'
            
        except Exception as e:
            self.log(f"Error analyzing {ticker}: {e}")
            return None
    
    def _rank_candidates(self, candidates):
        """
        Rank candidates and return top N.
        
        Args:
            candidates (list): List of candidate dicts
            
        Returns:
            list: Top N candidates
        """
        if not candidates:
            return []
        
        # Sort by score (higher is better)
        ranked = sorted(candidates, key=lambda x: x.get('score', 0), reverse=True)
        
        # Return top N
        top_n = config.TOP_CANDIDATES_COUNT
        return ranked[:top_n]
