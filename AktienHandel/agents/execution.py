from agents.base_agent import BaseAgent
import config
import json
import csv
import os
from datetime import datetime
import pandas as pd

class ExecutionAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Executor", role="Paper Broker")
        self.portfolio_file = config.PORTFOLIO_FILE
        self.trade_log_file = config.TRADE_LOG_FILE
        self.initialize_portfolio()

    def initialize_portfolio(self):
        """Creates portfolio file if it doesn't exist."""
        if not os.path.exists(self.portfolio_file):
            initial_state = {
                'cash': config.INITIAL_CASH,
                'holdings': {}, # ticker: quantity
                'total_value': config.INITIAL_CASH,
                'last_trade': None,  # Track the most recent trade
                'trade_count': 0,  # Total number of trades
                'start_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.save_portfolio(initial_state)
            self.log("Initialized new portfolio.")
        
        # Ensure log file exists/header
        if not os.path.exists(self.trade_log_file):
            with open(self.trade_log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Date', 'Ticker', 'Action', 'Quantity', 'Price', 'Total', 'Reason'])

    def get_portfolio_state(self):
        try:
            with open(self.portfolio_file, 'r') as f:
                state = json.load(f)
            
            # Calculate current total value including stock positions
            total_value = state.get('cash', 0)
            holdings = state.get('holdings', {})
            
            # Add value of all stock positions at current prices
            from utils.data_loader import fetch_data
            for ticker, quantity in holdings.items():
                df = fetch_data(ticker, period="1d")
                if df is not None and not df.empty:
                    close_val = df['Close'].iloc[-1]
                    if isinstance(close_val, pd.Series):
                        close_val = close_val.iloc[0]
                    current_price = float(close_val)
                    total_value += current_price * quantity
                    state.setdefault('current_prices', {})[ticker] = current_price
            
            state['total_value'] = total_value
            
            # Calculate performance metrics
            initial_value = config.INITIAL_CASH
            state['profit_loss'] = total_value - initial_value
            state['return_pct'] = ((total_value - initial_value) / initial_value) * 100
            
            # Add recent trades summary
            state['recent_trades'] = self._get_recent_trades(5)
            
            return state
        except Exception as e:
            self.log(f"Error reading portfolio: {e}")
            return {
                'cash': 0, 
                'holdings': {}, 
                'total_value': 0, 
                'profit_loss': 0, 
                'return_pct': 0,
                'last_trade': None,
                'trade_count': 0,
                'recent_trades': []
            }
    
    def _get_recent_trades(self, count=5):
        """Get recent trades from the trade log."""
        try:
            import csv
            if not os.path.exists(self.trade_log_file):
                return []
            
            with open(self.trade_log_file, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.DictReader(f)
                trades = list(reader)
                return trades[-count:] if trades else []
        except Exception as e:
            return []

    def save_portfolio(self, state):
        with open(self.portfolio_file, 'w') as f:
            json.dump(state, f, indent=4)

    def execute_order(self, signal, quantity):
        """
        Executes the order and updates portfolio/logs.
        """
        ticker = signal.get('ticker')
        action = signal.get('signal')
        price = signal.get('price')
        reason = signal.get('reason')
        
        state = self.get_portfolio_state()
        cash = state['cash']
        holdings = state['holdings']
        
        total_cost = price * quantity
        
        if action == 'BUY':
            if cash < total_cost:
                self.log("Execution Failed: Insufficient funds (Race condition?)")
                return False
            
            cash -= total_cost
            holdings[ticker] = holdings.get(ticker, 0) + quantity
            self.log(f"BOUGHT {quantity} {ticker} @ {price}")
            
        elif action == 'SELL':
            current_qty = holdings.get(ticker, 0)
            if current_qty < quantity:
                self.log("Execution Failed: Not enough shares")
                return False
                
            cash += total_cost
            holdings[ticker] = current_qty - quantity
            if holdings[ticker] == 0:
                del holdings[ticker]
            self.log(f"SOLD {quantity} {ticker} @ {price}")

        # Update State
        state['cash'] = cash
        state['holdings'] = holdings
        
        # Calculate total_value including all stock holdings
        total_value = cash
        from utils.data_loader import fetch_data
        for ticker_symbol, qty in holdings.items():
            try:
                df = fetch_data(ticker_symbol, period="1d")
                if df is not None and not df.empty:
                    close_val = df['Close'].iloc[-1]
                    if isinstance(close_val, pd.Series):
                        close_val = close_val.iloc[0]
                    current_price = float(close_val)
                    total_value += current_price * qty
                    state.setdefault('current_prices', {})[ticker_symbol] = current_price
            except Exception as e:
                self.log(f"Warning: Could not fetch price for {ticker_symbol}: {e}")
                # Fallback: use the trade price if it's the ticker we just traded
                if ticker_symbol == ticker:
                    total_value += price * qty
        
        state['total_value'] = total_value
        
        # Calculate performance metrics
        initial_value = config.INITIAL_CASH
        state['profit_loss'] = total_value - initial_value
        state['return_pct'] = ((total_value - initial_value) / initial_value) * 100
        
        
        # Track last trade
        state['last_trade'] = {
            'ticker': ticker,
            'action': action,
            'quantity': quantity,
            'price': price,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        state['trade_count'] = state.get('trade_count', 0) + 1
        
        self.save_portfolio(state)
        self.log_trade(ticker, action, quantity, price, total_cost, reason)
        return True

    def log_trade(self, ticker, action, quantity, price, total, reason):
        with open(self.trade_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ticker, action, quantity, price, total, reason
            ])

    def update_live_values(self):
        """
        Force update of portfolio.json with current live market prices.
        Useful for dashboard synchronization.
        """
        # get_portfolio_state already fetches live prices
        state = self.get_portfolio_state()
        self.save_portfolio(state)
        # self.log(f"Portfolio valuation updated: EUR {state['total_value']:.2f}")
        return state

    def set_daily_summary(self, summary_data):
        """
        Updates the daily summary in portfolio.json to explain what happened today.
        summary_data: dict with keys 'date', 'action', 'reason', 'trades'
        """
        state = self.get_portfolio_state()
        state['last_session'] = summary_data
        self.save_portfolio(state)
