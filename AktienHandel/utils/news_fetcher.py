"""
News Fetcher - Fetches market news and sentiment for trading decisions.
Supports NewsAPI and basic web scraping as fallback.
"""

import requests
from datetime import datetime, timedelta
import time


class NewsFetcher:
    """
    Fetches financial news and market sentiment.
    """
    
    def __init__(self, api_key=None):
        """
        Initialize news fetcher.
        
        Args:
            api_key (str): NewsAPI key (optional, falls back to free sources)
        """
        self.api_key = api_key
        self.enabled = api_key is not None and len(api_key) > 0
        self.cache = {}
        self.cache_duration = 3600  # Cache for 1 hour
        
    def get_market_news(self, max_articles=5):
        """
        Get general market news and sentiment.
        
        Args:
            max_articles (int): Maximum number of articles to fetch
            
        Returns:
            list: List of news articles with title, description, sentiment
        """
        if not self.enabled:
            return self._get_fallback_news()
        
        # Check cache
        cache_key = 'market_news'
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                return cached_data
        
        try:
            # NewsAPI endpoint for business/financial news
            url = 'https://newsapi.org/v2/top-headlines'
            params = {
                'apiKey': self.api_key,
                'category': 'business',
                'language': 'en',
                'pageSize': max_articles
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for article in data.get('articles', [])[:max_articles]:
                    articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'publishedAt': article.get('publishedAt', ''),
                        'sentiment': self._analyze_sentiment(
                            article.get('title', '') + ' ' + article.get('description', '')
                        )
                    })
                
                # Cache the results
                self.cache[cache_key] = (time.time(), articles)
                return articles
            else:
                return self._get_fallback_news()
                
        except Exception as e:
            print(f"[NewsFetcher] Error fetching news: {e}")
            return self._get_fallback_news()
    
    def get_ticker_news(self, ticker, max_articles=3):
        """
        Get news specific to a ticker/company.
        
        Args:
            ticker (str): Stock ticker symbol
            max_articles (int): Maximum number of articles
            
        Returns:
            list: List of news articles related to the ticker
        """
        if not self.enabled:
            return []
        
        # Check cache
        cache_key = f'ticker_{ticker}'
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                return cached_data
        
        try:
            # Convert ticker to company name query (simplified)
            query = self._ticker_to_query(ticker)
            
            # NewsAPI everything endpoint
            url = 'https://newsapi.org/v2/everything'
            params = {
                'apiKey': self.api_key,
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': max_articles,
                'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for article in data.get('articles', [])[:max_articles]:
                    articles.append({
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'publishedAt': article.get('publishedAt', ''),
                        'sentiment': self._analyze_sentiment(
                            article.get('title', '') + ' ' + article.get('description', '')
                        )
                    })
                
                # Cache the results
                self.cache[cache_key] = (time.time(), articles)
                return articles
            else:
                return []
                
        except Exception as e:
            print(f"[NewsFetcher] Error fetching ticker news for {ticker}: {e}")
            return []
    
    def _ticker_to_query(self, ticker):
        """
        Convert ticker to search query.
        Simple mapping for common tickers.
        """
        # Handle crypto
        if ticker.endswith('-USD'):
            crypto_name = ticker.replace('-USD', '')
            crypto_map = {
                'BTC': 'Bitcoin',
                'ETH': 'Ethereum',
                'BNB': 'Binance',
                'XRP': 'Ripple',
                'ADA': 'Cardano',
                'SOL': 'Solana',
                'DOGE': 'Dogecoin',
                'MATIC': 'Polygon',
                'DOT': 'Polkadot',
                'AVAX': 'Avalanche',
                'LINK': 'Chainlink',
                'UNI': 'Uniswap',
                'ATOM': 'Cosmos',
                'LTC': 'Litecoin',
                'XLM': 'Stellar'
            }
            return crypto_map.get(crypto_name, crypto_name)
        
        # Common stock ticker mappings
        ticker_map = {
            'AAPL': 'Apple',
            'MSFT': 'Microsoft',
            'GOOGL': 'Google',
            'AMZN': 'Amazon',
            'TSLA': 'Tesla',
            'META': 'Meta Facebook',
            'NVDA': 'Nvidia',
            'AMD': 'AMD',
            'INTC': 'Intel',
            'NFLX': 'Netflix',
            'JPM': 'JPMorgan',
            'BAC': 'Bank of America',
            'WMT': 'Walmart',
            'V': 'Visa',
            'MA': 'Mastercard'
        }
        
        return ticker_map.get(ticker, ticker)
    
    def _analyze_sentiment(self, text):
        """
        Basic sentiment analysis using keyword matching.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            str: 'positive', 'negative', or 'neutral'
        """
        if not text:
            return 'neutral'
        
        text = text.lower()
        
        # Positive keywords
        positive_words = [
            'surge', 'rally', 'gain', 'profit', 'growth', 'rise', 'soar',
            'bullish', 'outperform', 'beat', 'strong', 'record', 'high',
            'success', 'breakthrough', 'innovation', 'expansion', 'upgrade'
        ]
        
        # Negative keywords
        negative_words = [
            'plunge', 'fall', 'loss', 'decline', 'drop', 'crash', 'bear',
            'bearish', 'underperform', 'miss', 'weak', 'concern', 'risk',
            'failure', 'scandal', 'lawsuit', 'downgrade', 'warning', 'cut'
        ]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _get_fallback_news(self):
        """
        Fallback news when API is not available.
        Returns generic market sentiment.
        """
        return [{
            'title': 'Market News Unavailable',
            'description': 'News API not configured. Configure NEWS_API_KEY in config.py',
            'source': 'System',
            'publishedAt': datetime.now().isoformat(),
            'sentiment': 'neutral'
        }]
    
    def get_market_summary(self):
        """
        Get a text summary of current market sentiment.
        
        Returns:
            str: Market summary text
        """
        news = self.get_market_news(max_articles=5)
        
        if not news or news[0]['title'] == 'Market News Unavailable':
            return "No market news available."
        
        # Count sentiment
        sentiments = [article['sentiment'] for article in news]
        positive = sentiments.count('positive')
        negative = sentiments.count('negative')
        neutral = sentiments.count('neutral')
        
        # Generate summary
        if positive > negative:
            overall = "POSITIVE"
        elif negative > positive:
            overall = "NEGATIVE"
        else:
            overall = "NEUTRAL"
        
        headlines = [article['title'] for article in news[:3]]
        
        summary = f"Market Sentiment: {overall}\n"
        summary += f"Recent Headlines:\n"
        for i, headline in enumerate(headlines, 1):
            summary += f"{i}. {headline}\n"
        
        return summary
