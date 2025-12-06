from agents.base_agent import BaseAgent
from utils.universe_manager import UniverseManager
import config

class RiskManager(BaseAgent):
    def __init__(self):
        super().__init__(name="RiskGuard", role="Risk Manager")
        self.universe_mgr = UniverseManager()

    def validate_trade(self, signal, portfolio_state, current_daily_trades):
        """
        Checks if a trade signal is safe to execute.
        
        Args:
            signal (dict): The trade signal (e.g., {'signal': 'BUY', 'ticker': 'AAPL', 'price': 150})
            portfolio_state (dict): Current cash and holdings.
            current_daily_trades (int): Number of trades made today.
            
        Returns:
            bool: True if approved, False otherwise.
            str: Reason for decision.
        """
        ticker = signal.get('ticker')
        action = signal.get('signal')
        price = signal.get('price')

        if action not in ['BUY', 'SELL']:
            return False, "Invalid Action"

        # 1. Check Max Daily Trades
        if current_daily_trades >= config.MAX_TRADES_PER_DAY:
            return False, f"Daily trade limit reached ({config.MAX_TRADES_PER_DAY})"

        # 2. Check Drawdown (Simplified: if cash is too low compared to initial, stop buying)
        # Real drawdown calculation would need historical portfolio values.
        # Here we just check if we have enough cash for a BUY.
        
        if action == 'BUY':
            cash = portfolio_state.get('cash', 0.0)
            total_value = portfolio_state.get('total_value', cash) # simplified
            
            # Check if this is crypto
            is_crypto = self.universe_mgr.is_crypto(ticker)
            
            # Position Sizing: Different limits for crypto vs stocks
            if is_crypto:
                max_position_pct = config.MAX_CRYPTO_POSITION_SIZE_PCT
                
                # Check overall crypto allocation
                crypto_value = self._calculate_crypto_value(portfolio_state)
                crypto_pct = (crypto_value / total_value) if total_value > 0 else 0
                
                if crypto_pct >= config.MAX_CRYPTO_ALLOCATION_PCT:
                    return False, f"Crypto allocation limit reached ({crypto_pct*100:.1f}% >= {config.MAX_CRYPTO_ALLOCATION_PCT*100:.0f}%)"
            else:
                max_position_pct = config.MAX_POSITION_SIZE_PCT
            
            max_position_amt = total_value * max_position_pct
            
            # Calculate cost of 1 share (or we need to decide quantity here? 
            # Usually Risk Manager determines quantity or limits it)
            # For this step, let's assume we want to buy as much as allowed or 1 share minimum.
            if price > max_position_amt:
                return False, f"Price {price} exceeds max position size {max_position_amt:.2f}"
            
            if price > cash:
                 return False, "Insufficient Cash"

        # 3. Check existing position (don't double buy for now - simplified logic)
        if action == 'BUY' and ticker in portfolio_state.get('holdings', {}):
             return False, f"Already holding {ticker}"

        # 4. Check if we have shares to SELL
        if action == 'SELL':
            if ticker not in portfolio_state.get('holdings', {}):
                return False, f"Not holding {ticker}"

        return True, "Approved"
        
    def calculate_position_size(self, signal, portfolio_state):
        """
        Determines how many shares to buy.
        """
        ticker = signal.get('ticker')
        price = signal.get('price')
        cash = portfolio_state.get('cash', 0.0)
        total_value = portfolio_state.get('total_value', cash)
        
        # Check if this is crypto (different position sizing)
        is_crypto = self.universe_mgr.is_crypto(ticker)
        
        if is_crypto:
            max_amt = total_value * config.MAX_CRYPTO_POSITION_SIZE_PCT
        else:
            max_amt = total_value * config.MAX_POSITION_SIZE_PCT
        
        # We take the smaller of max_amt and available cash
        invest_amt = min(max_amt, cash)
        
        quantity = int(invest_amt // price)
        return quantity
    
    def _calculate_crypto_value(self, portfolio_state):
        """Calculate total crypto value in portfolio."""
        holdings = portfolio_state.get('holdings', {})
        crypto_value = 0.0
        
        for ticker, shares in holdings.items():
            if self.universe_mgr.is_crypto(ticker):
                # Simplified - would need actual current prices
                crypto_value += shares * 100  # Placeholder
        
        return crypto_value
