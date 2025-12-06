from agents.base_agent import BaseAgent
from utils.llm_client import LLMClient
from utils.news_fetcher import NewsFetcher
from utils.universe_manager import UniverseManager
import config

class GeminiStrategy(BaseAgent):
    """
    AI-powered trading strategy using Gemini.
    Makes intelligent buy/sell decisions based on analysis.
    """
    def __init__(self):
        super().__init__(name="GeminiAI", role="AI Strategy")
        self.llm = LLMClient() if config.USE_AI else None
        self.news_fetcher = NewsFetcher(config.NEWS_API_KEY) if config.ENABLE_NEWS else None
        self.universe_mgr = UniverseManager()

    def run(self, ticker, analysis, portfolio_context=None):
        """
        Evaluates a ticker using AI.
        
        Args:
            ticker (str): Stock ticker
            analysis (dict): Analysis data from Analyst agent
            portfolio_context (dict): Current portfolio state for context-aware decisions
            
        Returns:
            dict: Signal with 'signal', 'reason', 'confidence', 'price'
        """
        if not self.llm or not self.llm.enabled:
            return {'signal': 'HOLD', 'reason': 'AI disabled', 'confidence': 0.0}
        
        self.log(f"AI evaluating {ticker}...")
        
        # Build portfolio context
        portfolio_text = ""
        if portfolio_context:
            holdings = portfolio_context.get('holdings', {})
            recent_trades = portfolio_context.get('recent_trades', [])
            
            # Check if we recently sold this stock
            recently_sold = False
            for trade in recent_trades[-3:]:
                if trade.get('Ticker') == ticker and trade.get('Action') == 'SELL':
                    recently_sold = True
                    break
            
            if recently_sold:
                # Discourage buying recently sold stocks
                return {
                    'signal': 'HOLD',
                    'reason': 'Recently sold, avoid churning',
                    'confidence': 0.5,
                    'price': analysis.get('current_price', 0),
                    'ticker': ticker
                }
            
            # Add holdings context
            current_position = holdings.get(ticker, 0)
            portfolio_text = f"\nCurrent Holdings: {len(holdings)} stocks"
            if current_position > 0:
                portfolio_text += f"\nAlready own {current_position} shares of {ticker}"
        
        # Get news/sentiment if available
        news_text = ""
        if self.news_fetcher and self.news_fetcher.enabled:
            news = self.news_fetcher.get_ticker_news(ticker, max_articles=2)
            if news:
                news_text = "\n\nRecent News:\n"
                for article in news:
                    news_text += f"- {article['title']} (Sentiment: {article['sentiment']})\n"
        
        # Determine asset type
        asset_type = self.universe_mgr.get_asset_type(ticker)
        
        # Build prompt based on asset type
        if asset_type == 'crypto':
            prompt = self._build_crypto_prompt(ticker, analysis, portfolio_text, news_text)
        else:
            prompt = self._build_stock_prompt(ticker, analysis, portfolio_text, news_text)

        response = self.llm.generate(prompt, max_tokens=100)
        
        if not response:
            # Fallback to simple rule-based decision if AI is blocked
            self.log("AI blocked - using fallback logic")
            return self._fallback_decision(analysis)
        
        # Parse response
        signal = self._parse_decision(response)
        signal['price'] = analysis.get('current_price', 0)
        signal['ticker'] = ticker
        
        self.log(f"AI Decision: {signal['signal']} (Confidence: {signal['confidence']*100:.0f}%)")
        return signal
    
    def _parse_decision(self, response):
        """Parse the LLM response into structured signal."""
        lines = response.strip().split('\n')
        
        decision = 'HOLD'
        confidence = 0.5
        reason = 'AI analysis complete'
        
        for line in lines:
            line = line.strip()
            if line.startswith('DECISION:'):
                decision = line.split(':', 1)[1].strip().upper()
                if decision not in ['BUY', 'SELL', 'HOLD']:
                    decision = 'HOLD'
            elif line.startswith('CONFIDENCE:'):
                try:
                    conf_str = line.split(':', 1)[1].strip()
                    confidence = float(conf_str) / 100.0
                except:
                    confidence = 0.5
            elif line.startswith('REASON:'):
                reason = line.split(':', 1)[1].strip()
        
        return {
            'signal': decision,
            'confidence': confidence,
            'reason': reason
        }
    
    def _build_stock_prompt(self, ticker, analysis, portfolio_text, news_text):
        """Build prompt for stock analysis."""
        return f"""Based on this stock analysis data, provide a trading signal.

Stock: {ticker}
Current Price: ${analysis.get('current_price', 0):.2f}
50-day Moving Average: ${analysis.get('sma50', 0):.2f}
200-day Moving Average: ${analysis.get('sma200', 0):.2f}
Volatility: {analysis.get('volatility', 0)*100:.1f}%
1-Year Return: {analysis.get('trend_strength', 0)*100:.1f}%{portfolio_text}{news_text}

Goal: Outperform MSCI World index

Respond with:
DECISION: BUY or SELL or HOLD
CONFIDENCE: number from 0 to 100
REASON: One brief sentence

Example:
DECISION: BUY
CONFIDENCE: 75
REASON: Strong uptrend with positive news sentiment"""
    
    def _build_crypto_prompt(self, ticker, analysis, portfolio_text, news_text):
        """Build prompt for cryptocurrency analysis."""
        return f"""Based on this cryptocurrency analysis, provide a trading signal.

Crypto: {ticker}
Current Price: ${analysis.get('current_price', 0):.2f}
50-day Moving Average: ${analysis.get('sma50', 0):.2f}
200-day Moving Average: ${analysis.get('sma200', 0):.2f}
Volatility: {analysis.get('volatility', 0)*100:.1f}%
1-Year Return: {analysis.get('trend_strength', 0)*100:.1f}%{portfolio_text}{news_text}

Note: Cryptocurrencies are high-risk, high-reward. Consider higher volatility.
Goal: Identify strong momentum plays while managing risk

Respond with:
DECISION: BUY or SELL or HOLD
CONFIDENCE: number from 0 to 100
REASON: One brief sentence

Example:
DECISION: BUY
CONFIDENCE: 65
REASON: Strong momentum with positive community sentiment"""
    
    def _fallback_decision(self, analysis):
        """Simple rule-based fallback when AI is unavailable."""
        price = analysis.get('current_price', 0)
        sma50 = analysis.get('sma50', 0)
        sma200 = analysis.get('sma200', 0)
        
        # Simple trend following logic
        if price > sma50 > sma200:
            return {
                'signal': 'BUY',
                'confidence': 0.6,
                'reason': 'Uptrend (fallback logic)',
                'price': price
            }
        elif price < sma50:
            return {
                'signal': 'SELL',
                'confidence': 0.5,
                'reason': 'Downtrend (fallback logic)',
                'price': price
            }
        else:
            return {
                'signal': 'HOLD',
                'confidence': 0.5,
                'reason': 'Neutral (fallback logic)',
                'price': price
            }
