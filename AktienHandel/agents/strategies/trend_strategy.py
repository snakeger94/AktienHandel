from agents.base_agent import BaseAgent
from utils.data_loader import fetch_data
import pandas as pd

class TrendStrategy(BaseAgent):
    def __init__(self):
        super().__init__(name="TrendBot", role="Trend Strategy")

    def run(self, ticker):
        """
        Evaluates a ticker for a Trend signal.
        Returns: 'BUY', 'SELL', or 'HOLD', along with details.
        """
        self.log(f"Evaluating {ticker} for Trend Setup...")
        df = fetch_data(ticker, period="1y") # Need 200 days for SMA200
        
        if df is None or len(df) < 200:
            return {'signal': 'HOLD', 'reason': 'Insufficient Data', 'confidence': 0.0}

        # Calculate Indicators
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['SMA200'] = df['Close'].rolling(window=200).mean()
        
        current_price = df['Close'].iloc[-1]
        sma50 = df['SMA50'].iloc[-1]
        sma200 = df['SMA200'].iloc[-1]
        
        # Golden Cross checks (approximate current state)
        # Strong Buy: Price > SMA50 > SMA200
        if current_price > sma50 and sma50 > sma200:
            return {
                'signal': 'BUY',
                'reason': 'Uptrend: Price > SMA50 > SMA200',
                'confidence': 0.8,
                'price': float(current_price)
            }
        
        # Sell/Avoid: Price < SMA50
        elif current_price < sma50:
            return {
                'signal': 'SELL', # Or just don't buy
                'reason': 'Downtrend: Price < SMA50',
                'confidence': 0.6,
                'price': float(current_price)
            }
            
        return {'signal': 'HOLD', 'reason': 'Choppy/Neutral', 'confidence': 0.5, 'price': float(current_price)}
