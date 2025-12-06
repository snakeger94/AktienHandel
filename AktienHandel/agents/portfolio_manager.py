from agents.base_agent import BaseAgent
from utils.llm_client import LLMClient
from utils.universe_manager import UniverseManager
import config

class PortfolioManager(BaseAgent):
    """
    AI-powered portfolio manager that makes trading decisions
    based on current portfolio performance and market conditions.
    """
    def __init__(self):
        super().__init__(name="PortfolioMgr", role="Portfolio Manager")
        self.llm = LLMClient() if config.USE_AI else None
        self.universe_mgr = UniverseManager()

    def evaluate_portfolio(self, portfolio_state):
        """
        Evaluates current portfolio and gives trading guidance.
        
        Args:
            portfolio_state (dict): Current portfolio with holdings, cash, P&L
            
        Returns:
            dict: Trading guidance (aggressive/conservative/hold)
        """
        total_value = portfolio_state.get('total_value', 0)
        cash = portfolio_state.get('cash', 0)
        return_pct = portfolio_state.get('return_pct', 0)
        holdings_count = len(portfolio_state.get('holdings', {}))
        last_trade = portfolio_state.get('last_trade', None)
        recent_trades = portfolio_state.get('recent_trades', [])
        
        cash_pct = (cash / total_value * 100) if total_value > 0 else 100
        
        # Calculate crypto allocation
        crypto_value, stock_value = self._calculate_allocations(portfolio_state)
        crypto_pct = (crypto_value / total_value * 100) if total_value > 0 else 0
        
        # Get benchmark performance
        from utils.benchmark import BenchmarkTracker
        benchmark_tracker = BenchmarkTracker()
        comparison = benchmark_tracker.compare_performance(return_pct)
        
        # Default rule-based guidance with benchmark awareness
        if return_pct < -5:
            guidance = "CONSERVATIVE"
            reason = "Portfolio down >5%, reduce risk"
        elif cash_pct < 20:
            guidance = "HOLD"
            reason = "Low cash reserves, wait for opportunities"
        elif holdings_count >= 5:
            guidance = "HOLD"
            reason = "Portfolio diversified, maintain positions"
        elif comparison and comparison['outperforming']:
            guidance = "AGGRESSIVE"
            reason = f"Outperforming MSCI World by {comparison['alpha']:.2f}%, continue strategy"
        elif comparison and not comparison['outperforming'] and return_pct > 0:
            guidance = "AGGRESSIVE"
            reason = f"Underperforming MSCI World, need better positions"
        else:
            guidance = "AGGRESSIVE"
            reason = "Good conditions for growth"
        
        # Try AI enhancement
        if self.llm and self.llm.enabled:
            ai_guidance = self._get_ai_guidance(portfolio_state, comparison)
            if ai_guidance:
                return ai_guidance
        
        return {
            'strategy': guidance,
            'reason': reason,
            'max_new_positions': 5 - holdings_count if guidance == 'AGGRESSIVE' else 0,
            'benchmark_comparison': comparison
        }
    
    def _get_ai_guidance(self, portfolio, comparison):
        """Get AI-based portfolio guidance."""
        
        # Build context about recent trades
        recent_trades_text = ""
        recent_trades = portfolio.get('recent_trades', [])
        if recent_trades:
            recent_trades_text = "\nRecent Trades:\n"
            for trade in recent_trades[-3:]:
                recent_trades_text += f"- {trade.get('Action', 'N/A')} {trade.get('Ticker', 'N/A')} at EUR {trade.get('Price', 0)}\n"
        
        # Build benchmark context
        benchmark_text = ""
        if comparison:
            status = "OUTPERFORMING" if comparison['outperforming'] else "UNDERPERFORMING"
            benchmark_text = f"""
Benchmark (MSCI World): {comparison['benchmark_return']:.2f}%
Status: {status} by {abs(comparison['alpha']):.2f}%
Goal: Outperform MSCI World
"""
        
        prompt = f"""As a portfolio manager, analyze this trading portfolio:

Total Value: EUR {portfolio.get('total_value', 0):.2f}
Cash: EUR {portfolio.get('cash', 0):.2f}
Return: {portfolio.get('return_pct', 0):.1f}%
Holdings: {len(portfolio.get('holdings', {}))} positions
Trade Count: {portfolio.get('trade_count', 0)}
{benchmark_text}{recent_trades_text}

Your GOAL is to OUTPERFORM the MSCI World index.

Recommend one trading strategy:

STRATEGY: AGGRESSIVE or CONSERVATIVE or HOLD
MAX_NEW_POSITIONS: number (0-5)
REASON: One sentence focusing on beating the benchmark

Example:
STRATEGY: AGGRESSIVE
MAX_NEW_POSITIONS: 2
REASON: Portfolio underperforming MSCI World, need stronger growth stocks"""

        response = self.llm.generate(prompt, max_tokens=150)
        
        if not response:
            return None
        
        # Parse response
        lines = response.strip().split('\n')
        strategy = 'HOLD'
        max_positions = 0
        reason = 'AI analysis'
        
        for line in lines:
            line = line.strip()
            if line.startswith('STRATEGY:'):
                strategy = line.split(':', 1)[1].strip().upper()
            elif line.startswith('MAX_NEW_POSITIONS:'):
                try:
                    max_positions = int(line.split(':', 1)[1].strip())
                except:
                    max_positions = 0
            elif line.startswith('REASON:'):
                reason = line.split(':', 1)[1].strip()
        
        self.log(f"AI Guidance: {strategy} - {reason}")
        
        return {
            'strategy': strategy,
            'reason': reason,
            'max_new_positions': max_positions,
            'benchmark_comparison': comparison
        }
    
    def _calculate_allocations(self, portfolio_state):
        """
        Calculate crypto vs stock allocations.
        
        Returns:
            tuple: (crypto_value, stock_value)
        """
        holdings = portfolio_state.get('holdings', {})
        crypto_value = 0.0
        stock_value = 0.0
        
        for ticker, shares in holdings.items():
            # Get current price from portfolio state or estimate
            # This is a simplified version - in real implementation,
            # we'd fetch current prices
            value = shares * 100  # Placeholder calculation
            
            if self.universe_mgr.is_crypto(ticker):
                crypto_value += value
            else:
                stock_value += value
        
        return crypto_value, stock_value
    
    def get_crypto_allocation_info(self, portfolio_state):
        """
        Get crypto allocation percentage.
        
        Returns:
            dict: Crypto allocation info
        """
        total_value = portfolio_state.get('total_value', 0)
        crypto_value, stock_value = self._calculate_allocations(portfolio_state)
        crypto_pct = (crypto_value / total_value * 100) if total_value > 0 else 0
        
        return {
            'crypto_value': crypto_value,
            'stock_value': stock_value,
            'crypto_pct': crypto_pct,
            'within_limit': crypto_pct <= (config.MAX_CRYPTO_ALLOCATION_PCT * 100)
        }

