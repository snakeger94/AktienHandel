"""
Benchmark tracking utility for comparing portfolio performance
against MSCI World index.
"""

import json
import os
from datetime import datetime
from utils.data_loader import fetch_data
import config
import pandas as pd


class BenchmarkTracker:
    """Tracks and compares portfolio performance against MSCI World."""
    
    def __init__(self):
        self.benchmark_file = config.BENCHMARK_FILE
        self.benchmark_ticker = config.BENCHMARK_TICKER
        self._ensure_initialized()
    
    def _ensure_initialized(self):
        """Initialize benchmark tracking if not exists."""
        if not os.path.exists(self.benchmark_file):
            # Fetch initial benchmark price
            df = fetch_data(self.benchmark_ticker, period="1d")
            if df is not None and not df.empty:
                close_val = df['Close'].iloc[-1]
                if isinstance(close_val, pd.Series):
                    close_val = close_val.iloc[0]
                initial_price = float(close_val)
            else:
                initial_price = 100.0  # Fallback
            
            initial_data = {
                'ticker': self.benchmark_ticker,
                'start_date': datetime.now().strftime("%Y-%m-%d"),
                'start_price': initial_price,
                'initial_investment': config.INITIAL_CASH,
                'history': []
            }
            
            with open(self.benchmark_file, 'w') as f:
                json.dump(initial_data, f, indent=4)
    
    def get_benchmark_data(self):
        """Get benchmark tracking data."""
        try:
            with open(self.benchmark_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading benchmark data: {e}")
            return None
    
    def calculate_benchmark_performance(self):
        """
        Calculate current benchmark performance.
        
        Returns:
            dict: Benchmark performance metrics
        """
        data = self.get_benchmark_data()
        if not data:
            return None
        
        # Fetch current benchmark price
        df = fetch_data(self.benchmark_ticker, period="1d")
        if df is None or df.empty:
            return None
        
        # Safe extraction of price
        close_val = df['Close'].iloc[-1]
        if isinstance(close_val, pd.Series):
             close_val = close_val.iloc[0]
        current_price = float(close_val)
        start_price = data.get('start_price', current_price)
        initial_investment = data.get('initial_investment', config.INITIAL_CASH)
        
        # Calculate returns
        price_return = ((current_price - start_price) / start_price) * 100
        current_value = initial_investment * (1 + price_return / 100)
        profit_loss = current_value - initial_investment
        
        return {
            'ticker': self.benchmark_ticker,
            'start_date': data.get('start_date', 'N/A'),
            'start_price': start_price,
            'current_price': current_price,
            'return_pct': price_return,
            'initial_investment': initial_investment,
            'current_value': current_value,
            'profit_loss': profit_loss
        }
    
    def compare_performance(self, portfolio_return_pct):
        """
        Compare portfolio performance against benchmark.
        
        Args:
            portfolio_return_pct (float): Portfolio return percentage
            
        Returns:
            dict: Comparison metrics
        """
        benchmark = self.calculate_benchmark_performance()
        if not benchmark:
            return None
        
        benchmark_return = benchmark['return_pct']
        alpha = portfolio_return_pct - benchmark_return
        
        outperforming = alpha > 0
        
        return {
            'portfolio_return': portfolio_return_pct,
            'benchmark_return': benchmark_return,
            'alpha': alpha,
            'outperforming': outperforming,
            'benchmark_value': benchmark['current_value'],
            'benchmark_profit_loss': benchmark['profit_loss']
        }
    
    def log_snapshot(self, portfolio_value, portfolio_return):
        """Log a snapshot of current performance."""
        data = self.get_benchmark_data()
        if not data:
            return
        
        benchmark = self.calculate_benchmark_performance()
        if not benchmark:
            return
        
        snapshot = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'portfolio_value': portfolio_value,
            'portfolio_return': portfolio_return,
            'benchmark_value': benchmark['current_value'],
            'benchmark_return': benchmark['return_pct'],
            'alpha': portfolio_return - benchmark['return_pct']
        }
        
        data['history'].append(snapshot)
        
        # Keep last 100 snapshots
        if len(data['history']) > 100:
            data['history'] = data['history'][-100:]
        
        with open(self.benchmark_file, 'w') as f:
            json.dump(data, f, indent=4)
