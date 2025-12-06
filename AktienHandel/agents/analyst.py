from agents.base_agent import BaseAgent
from utils.data_loader import fetch_data
from utils.llm_client import LLMClient
from utils.news_fetcher import NewsFetcher
import numpy as np
import config

class Analyst(BaseAgent):
    def __init__(self):
        super().__init__(name="Analyst", role="Research Analyst")
        self.llm = LLMClient() if config.USE_AI else None
        self.news_fetcher = NewsFetcher(config.NEWS_API_KEY) if config.ENABLE_NEWS else None

    def run(self, ticker):
        """
        Analyzes a specific ticker in depth.
        Returns a dictionary with metrics and AI analysis.
        """
        self.log(f"Analyzing {ticker}...")
        df = fetch_data(ticker, period="1y")
        
        if df is None or df.empty:
            return None

        # Calculate technical metrics
        volatility = self.calculate_volatility(df)
        max_drawdown = self.calculate_max_drawdown(df)
        trend_strength = self.calculate_trend_strength(df)
        
        # Get current price and moving averages
        current_price = float(df['Close'].iloc[-1])
        sma50 = float(df['Close'].rolling(window=50).mean().iloc[-1]) if len(df) >= 50 else current_price
        sma200 = float(df['Close'].rolling(window=200).mean().iloc[-1]) if len(df) >= 200 else current_price
        
        analysis_result = {
            'ticker': ticker,
            'current_price': current_price,
            'sma50': sma50,
            'sma200': sma200,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'trend_strength': trend_strength,
            'ai_outlook': None,
            'news_sentiment': 'neutral'
        }
        
        # AI Enhancement: Get qualitative analysis
        if self.llm and self.llm.enabled:
            prompt = f"""You are a financial data analyst. Analyze the following stock metrics:

Ticker: {ticker}
Price: ${current_price:.2f}
50-day Average: ${sma50:.2f}
200-day Average: ${sma200:.2f}
Annual Volatility: {volatility*100:.1f}%
1-Year Max Drawdown: {max_drawdown*100:.1f}%
1-Year Return: {trend_strength*100:.1f}%

Provide a brief 2-sentence technical summary of the current market position and trend."""
            
            ai_response = self.llm.generate(prompt, max_tokens=150)
            if ai_response:
                analysis_result['ai_outlook'] = ai_response
                self.log(f"AI Outlook: {ai_response[:80]}...")
            else:
                self.log("AI analysis blocked or unavailable")
        
        return analysis_result

    def calculate_volatility(self, df):
        # Annualized volatility
        returns = df['Close'].pct_change().dropna()
        vol = returns.std() * np.sqrt(252)
        return float(vol)

    def calculate_max_drawdown(self, df):
        # Max percentage drop from peak
        prices = df['Close']
        rolling_max = prices.cummax()
        drawdown = (prices - rolling_max) / rolling_max
        return float(drawdown.min())

    def calculate_trend_strength(self, df):
        # A simple metric: returns over the period
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        return float((end_price - start_price) / start_price)
