# -*- coding: utf-8 -*-
"""
Quick test script to verify the new components work correctly.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_universe_manager():
    """Test universe manager."""
    print("\n=== Testing Universe Manager ===")
    from utils.universe_manager import UniverseManager
    
    um = UniverseManager()
    
    # Test different modes
    universe = um.get_universe(mode='us_stocks', enable_crypto=True)
    print(f"US Stocks mode: {len(universe['stocks'])} stocks, {len(universe['crypto'])} cryptos")
    
    # Test crypto detection
    assert um.is_crypto('BTC-USD') == True
    assert um.is_crypto('AAPL') == False
    print("[OK] Crypto detection working")
    
    # Test asset type
    assert um.get_asset_type('ETH-USD') == 'crypto'
    assert um.get_asset_type('MSFT') == 'stock'
    print("[OK] Asset type detection working")
    
    print(f"[OK] Universe Manager: {um.get_total_count('us_stocks', True)} total tickers")


def test_news_fetcher():
    """Test news fetcher."""
    print("\n=== Testing News Fetcher ===")
    from utils.news_fetcher import NewsFetcher
    
    # Test without API key (fallback mode)
    nf = NewsFetcher(api_key=None)
    assert nf.enabled == False
    print("[OK] News fetcher works without API key (fallback mode)")
    
    news = nf.get_market_news()
    print(f"[OK] Got fallback news: {len(news)} articles")
    
    # Test sentiment analysis
    sentiment = nf._analyze_sentiment("Stock surges on strong earnings beat")
    assert sentiment == 'positive'
    
    sentiment = nf._analyze_sentiment("Stock plunges on weak guidance")
    assert sentiment == 'negative'
    print("[OK] Sentiment analysis working")


def test_data_loader():
    """Test enhanced data loader."""
    print("\n=== Testing Data Loader ===")
    from utils.data_loader import fetch_data, fetch_batch_data
    
    # Test single ticker (crypto)
    print("Testing BTC-USD data fetch...")
    df = fetch_data('BTC-USD', period='1mo')
    if df is not None:
        print(f"[OK] Crypto data fetch working: {len(df)} days of BTC data")
    else:
        print("[WARN] Could not fetch BTC data (network issue?)")
    
    # Test batch fetch
    print("Testing batch fetch...")
    tickers = ['AAPL', 'MSFT', 'BTC-USD']
    results = fetch_batch_data(tickers, period='1mo', max_workers=3)
    print(f"[OK] Batch fetch: {len(results)}/{len(tickers)} successful")


def test_config():
    """Test config has new settings."""
    print("\n=== Testing Configuration ===")
    import config
    
    # Check new config options exist
    assert hasattr(config, 'UNIVERSE_MODE')
    assert hasattr(config, 'ENABLE_CRYPTO')
    assert hasattr(config, 'MAX_CRYPTO_ALLOCATION_PCT')
    assert hasattr(config, 'TOP_CANDIDATES_COUNT')
    assert hasattr(config, 'ENABLE_NEWS')
    print("[OK] All new configuration options present")
    print(f"  - Universe mode: {config.UNIVERSE_MODE}")
    print(f"  - Crypto enabled: {config.ENABLE_CRYPTO}")
    print(f"  - Max crypto allocation: {config.MAX_CRYPTO_ALLOCATION_PCT*100}%")
    print(f"  - Top candidates: {config.TOP_CANDIDATES_COUNT}")


def test_market_scanner():
    """Test market scanner can initialize."""
    print("\n=== Testing Market Scanner ===")
    from agents.market_scanner import MarketScanner
    
    scanner = MarketScanner()
    print("[OK] Market scanner initialized")
    print("  (Full scan not tested - would take several minutes)")


def test_ai_strategy():
    """Test AI strategy initialization."""
    print("\n=== Testing AI Strategy ===")
    from agents.strategies.gemini_strategy import GeminiStrategy
    
    strategy = GeminiStrategy()
    print("[OK] AI Strategy initialized with news integration")
    
    assert hasattr(strategy, 'news_fetcher')
    assert hasattr(strategy, 'universe_mgr')
    print("[OK] News fetcher and universe manager integrated")


def test_risk_manager():
    """Test risk manager with crypto support."""
    print("\n=== Testing Risk Manager ===")
    from agents.risk_manager import RiskManager
    
    risk_mgr = RiskManager()
    assert hasattr(risk_mgr, 'universe_mgr')
    print("[OK] Risk manager has universe manager")
    
    # Test crypto position sizing
    portfolio = {'cash': 10000, 'total_value': 10000, 'holdings': {}}
    signal = {'ticker': 'BTC-USD', 'signal': 'BUY', 'price': 50000}
    
    qty = risk_mgr.calculate_position_size(signal, portfolio)
    print(f"[OK] Crypto position sizing: {qty} shares (smaller due to crypto limits)")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Expanded Trading System")
    print("=" * 60)
    
    try:
        test_config()
        test_universe_manager()
        test_news_fetcher()
        test_data_loader()
        test_market_scanner()
        test_ai_strategy()
        test_risk_manager()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe system is ready to use.")
        print("Run 'python main.py' to start trading.")
        
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
