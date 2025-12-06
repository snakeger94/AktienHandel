from agents.base_agent import BaseAgent
from utils.llm_client import LLMClient
import config
import csv
import pandas as pd
import os

import sys

class ReportingAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Reporter", role="Daily Reporter")
        self.trade_log_file = config.TRADE_LOG_FILE
        self.llm = LLMClient() if config.USE_AI else None
        
        # Ensure stdout can handle unicode (e.g. for Windows console)
        if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass

    def generate_daily_report(self):
        """
        Reads the trade log and prints a summary of recent activity.
        Uses AI to generate insights.
        """
        self.log("Generating Daily Report...")
        
        # Get current portfolio state
        from agents.execution import ExecutionAgent
        from utils.benchmark import BenchmarkTracker
        
        executor = ExecutionAgent()
        portfolio = executor.get_portfolio_state()
        
        benchmark_tracker = BenchmarkTracker()
        benchmark_perf = benchmark_tracker.calculate_benchmark_performance()
        comparison = benchmark_tracker.compare_performance(portfolio.get('return_pct', 0))
        
        # Log snapshot for historical tracking
        benchmark_tracker.log_snapshot(portfolio.get('total_value', 0), portfolio.get('return_pct', 0))
        
        print("\n" + "="*70)
        print(" DAILY TRADING REPORT")
        print("="*70)
        
        # Portfolio Status
        print("\n PORTFOLIO STATUS")
        print("-" * 70)
        print(f" Total Value:      EUR {portfolio.get('total_value', 0):.2f}")
        print(f" Cash Available:   EUR {portfolio.get('cash', 0):.2f}")
        print(f" Invested:         EUR {portfolio.get('total_value', 0) - portfolio.get('cash', 0):.2f}")
        print(f" Profit/Loss:      EUR {portfolio.get('profit_loss', 0):.2f}")
        print(f" Return:           {portfolio.get('return_pct', 0):.2f}%")
        print(f" Total Trades:     {portfolio.get('trade_count', 0)}")
        
        # Daily Summary (New)
        last_session = portfolio.get('last_session')
        if last_session:
            print("\n" + "-" * 70)
            print(" LATEST SESSION RESULT")
            print("-" * 70)
            print(f" Date:             {last_session.get('date')}")
            print(f" Action:           {last_session.get('action')}")
            print(f" Reason:           {last_session.get('reason')}")
            print(f" Trades Executed:  {last_session.get('trades_count')}")

        # Last Trade
        last_trade = portfolio.get('last_trade')
        if last_trade:
            print(f" Last Trade:       {last_trade['action']} {last_trade['quantity']} {last_trade['ticker']} @ EUR {last_trade['price']:.2f}")
        
        # Portfolio Composition
        print("\n" + "-" * 70)
        print(" PORTFOLIO COMPOSITION AFTER TRADES")
        print("-" * 70)
        
        holdings = portfolio.get('holdings', {})
        if holdings:
            from utils.data_loader import fetch_data
            total_invested = 0
            
            for ticker, quantity in holdings.items():
                df = fetch_data(ticker, period="1d")
                if df is not None and not df.empty:
                    close_val = df['Close'].iloc[-1]
                    if isinstance(close_val, pd.Series):
                        close_val = close_val.iloc[0]
                    current_price = float(close_val)
                    position_value = current_price * quantity
                    total_invested += position_value
                    allocation_pct = (position_value / portfolio.get('total_value', 1)) * 100
                    print(f"   {ticker:6s}: {quantity:3d} shares @ EUR {current_price:7.2f} = EUR {position_value:9.2f} ({allocation_pct:5.1f}%)")
            
            cash_allocation = (portfolio.get('cash', 0) / portfolio.get('total_value', 1)) * 100
            print(f"   {'CASH':6s}:                             EUR {portfolio.get('cash', 0):9.2f} ({cash_allocation:5.1f}%)")
        else:
            print("   No holdings - 100% cash")
        
        # Benchmark Comparison
        print("\n" + "-" * 70)
        print(" PERFORMANCE vs MSCI WORLD")
        print("-" * 70)
        
        if benchmark_perf and comparison:
            portfolio_return = portfolio.get('return_pct', 0)
            benchmark_return = benchmark_perf['return_pct']
            alpha = comparison['alpha']
            
            status = "OUTPERFORMING" if comparison['outperforming'] else "UNDERPERFORMING"
            
            print(f" Status:           {status}")
            print(f" Portfolio Return: {portfolio_return:+.2f}%")
            print(f" MSCI World Return:{benchmark_return:+.2f}%")
            print(f" Alpha (Difference): {alpha:+.2f}%")
            print()
            print(f" If invested in MSCI World:")
            print(f"   Would have: EUR {comparison['benchmark_value']:.2f}")
            print(f"   Difference: EUR {(portfolio.get('total_value', 0) - comparison['benchmark_value']):+.2f}")
        else:
            print(" Benchmark data not available")
        
        # Investment Development
        print("\n" + "-" * 70)
        print(" INVESTMENT DEVELOPMENT")
        print("-" * 70)
        start_date = portfolio.get('start_date', 'N/A')
        print(f" Starting Capital: EUR {config.INITIAL_CASH:.2f}")
        print(f" Start Date:       {start_date}")
        print(f" Current Value:    EUR {portfolio.get('total_value', 0):.2f}")
        print(f" Total Return:     EUR {portfolio.get('profit_loss', 0):+.2f} ({portfolio.get('return_pct', 0):+.2f}%)")
        
        if portfolio.get('profit_loss', 0) >= 0:
            print(f" Status:           Profitable")
        else:
            print(f" Status:           Loss")
        
        # Trading Activity
        print("\n" + "="*70)
        
        if not os.path.exists(self.trade_log_file):
            self.log("No trade history found.")
            return

        try:
            # Use 'replace' to handle potential legacy CP1252 characters without crashing
            df = pd.read_csv(self.trade_log_file, encoding='utf-8', encoding_errors='replace')
            if df.empty:
                self.log("Trade log is empty.")
                return

            total_trades = len(df)
            buys = len(df[df['Action'] == 'BUY'])
            sells = len(df[df['Action'] == 'SELL'])
            
            print(" TRADING ACTIVITY")
            print("="*70)
            print(f" Total Trades: {total_trades}")
            print(f" Buys: {buys} | Sells: {sells}")
            print("-" * 70)
            print(" Recent Activity:")
            print(df.tail(5)[['Date', 'Ticker', 'Action', 'Price', 'Reason']].to_string(index=False))
            print("="*70)
            
            # AI Summary
            if self.llm and self.llm.enabled and not df.empty:
                self._generate_ai_summary(df, portfolio, comparison)
            
            print()
            
        except Exception as e:
            self.log(f"Error generating report: {e}")
    
    def _generate_ai_summary(self, df, portfolio, comparison):
        """Generate AI-powered insights from trading activity."""
        recent_trades = df.tail(10)
        
        trade_summary = "\n".join([
            f"{row['Ticker']}: {row['Action']} at ${row['Price']:.2f}"
            for _, row in recent_trades.iterrows()
        ])
        
        benchmark_context = ""
        if comparison:
            status = "outperforming" if comparison['outperforming'] else "underperforming"
            benchmark_context = f"\nPortfolio is {status} MSCI World by {abs(comparison['alpha']):.2f}%."
        
        prompt = f"""Summarize the trading activity and performance in 2-3 sentences:

Recent Trades:
{trade_summary}

Portfolio Return: {portfolio.get('return_pct', 0):.2f}%{benchmark_context}

Focus on strategy effectiveness and whether we're meeting our goal to beat MSCI World."""

        response = self.llm.generate(prompt, max_tokens=200)
        
        if response:
            print("\n[AI INSIGHTS]")
            print("-" * 70)
            print(response)
            print("="*70)
        else:
            print("\n[AI summary unavailable (content blocked)]")
            print("="*70)
