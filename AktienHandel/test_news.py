"""Quick test of news API with real key"""
from utils.news_fetcher import NewsFetcher
import config

print("Testing News API...")
nf = NewsFetcher(config.NEWS_API_KEY)

print(f"News API enabled: {nf.enabled}")

if nf.enabled:
    # Test market news
    print("\n=== Market News ===")
    news = nf.get_market_news(max_articles=3)
    print(f"Found {len(news)} articles")
    
    for article in news:
        print(f"\n- {article['title']}")
        print(f"  Source: {article['source']}")
        print(f"  Sentiment: {article['sentiment']}")
    
    # Test ticker-specific news
    print("\n\n=== Ticker-Specific News (AAPL) ===")
    aapl_news = nf.get_ticker_news('AAPL', max_articles=2)
    print(f"Found {len(aapl_news)} articles about Apple")
    
    for article in aapl_news:
        print(f"\n- {article['title']}")
        print(f"  Sentiment: {article['sentiment']}")
    
    # Test crypto news
    print("\n\n=== Crypto News (Bitcoin) ===")
    btc_news = nf.get_ticker_news('BTC-USD', max_articles=2)
    print(f"Found {len(btc_news)} articles about Bitcoin")
    
    for article in btc_news:
        print(f"\n- {article['title']}")
        print(f"  Sentiment: {article['sentiment']}")
    
    print("\n\n[SUCCESS] News API working correctly!")
else:
    print("[ERROR] News API not enabled")
