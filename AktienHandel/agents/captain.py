from agents.base_agent import BaseAgent
from agents.market_scanner import MarketScanner
from agents.analyst import Analyst
from agents.risk_manager import RiskManager
from agents.execution import ExecutionAgent
from agents.reporting import ReportingAgent
from agents.portfolio_manager import PortfolioManager
from agents.strategies.trend_strategy import TrendStrategy
from agents.strategies.gemini_strategy import GeminiStrategy
import time
import config
from datetime import datetime

class Captain(BaseAgent):
    def __init__(self):
        super().__init__(name="Captain", role="Team Leader")
        
        # Initialize the Team
        self.scanner = MarketScanner()
        self.analyst = Analyst()
        self.risk_manager = RiskManager()
        self.executor = ExecutionAgent()
        self.reporter = ReportingAgent()
        self.portfolio_mgr = PortfolioManager()
        
        # Strategies (List of active strategies)
        # Use AI strategy if enabled, otherwise fallback to simple trend
        if config.USE_AI and config.GEMINI_API_KEY:
            self.strategies = [GeminiStrategy()]
            self.log("Using AI-powered trading strategy")
        else:
            self.strategies = [TrendStrategy()]
            self.log("Using rule-based trend strategy")

    def start_day(self):
        self.log("Starting Daily Trading Session...")
        
        # 1. Check Portfolio State
        # Update live values first to ensure dashboard and logic are in sync
        portfolio = self.executor.update_live_values()
        self.log(f"Current Portfolio Value: ${portfolio.get('total_value', 0):.2f} | Cash: ${portfolio.get('cash', 0):.2f}")
        
        # 2. Get Portfolio Manager Guidance
        guidance = self.portfolio_mgr.evaluate_portfolio(portfolio)
        self.log(f"Portfolio Strategy: {guidance['strategy']} - {guidance['reason']}")
        
        # Display benchmark comparison
        comparison = guidance.get('benchmark_comparison')
        if comparison:
            status = "BEATING" if comparison['outperforming'] else "BEHIND"
            self.log(f"Benchmark Status: {status} MSCI World by {abs(comparison['alpha']):.2f}% | Portfolio: {comparison['portfolio_return']:.2f}% vs MSCI: {comparison['benchmark_return']:.2f}%")
        
        max_new_trades = guidance.get('max_new_positions', 0)
        
        daily_trades_count = 0 
        rejection_reasons = []

        # 3. Scan Market
        candidates = self.scanner.run()
        
        # Stop if portfolio manager says HOLD
        if guidance['strategy'] == 'HOLD':
            self.log("Portfolio Manager advises HOLD - skipping trading")
            self.executor.set_daily_summary({
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'action': 'HOLD',
                'reason': guidance['reason'],
                'trades_count': 0
            })
            self.reporter.generate_daily_report()
            self.log("Daily Session Complete.")
            return
        
        for candidate in candidates:
            # Check if we've hit the portfolio manager's limit
            if daily_trades_count >= max_new_trades:
                self.log(f"Reached portfolio manager limit ({max_new_trades} new positions)")
                rejection_reasons.append("Reached max daily positions limit")
                break
            
            ticker = candidate['ticker']
            self.log(f"Processing candidate: {ticker}")
            
            # 3. Analyze Deeply
            analysis = self.analyst.run(ticker)
            if not analysis:
                rejection_reasons.append(f"{ticker}: Analysis failed")
                continue
                
            # 4. Ask Strategies
            for strategy in self.strategies:
                # For AI strategies, pass the full analysis and portfolio context
                if hasattr(strategy, 'run') and strategy.name == 'GeminiAI':
                    signal = strategy.run(ticker, analysis, portfolio_context=portfolio)
                else:
                    # Traditional strategies just need the ticker
                    signal = strategy.run(ticker)
                
                # If we have a signal
                if signal['signal'] in ['BUY', 'SELL']:
                    self.log(f"Strategy {strategy.name} generated {signal['signal']} for {ticker} ({signal['confidence']*100:.0f}%)")
                    
                    # Add Ticker to signal for context (if not already there)
                    if 'ticker' not in signal:
                        signal['ticker'] = ticker
                    
                    # Ensure price is set
                    if 'price' not in signal or signal['price'] == 0:
                        signal['price'] = analysis.get('current_price', 0)
                    
                    # 5. Risk Check
                    is_safe, reason = self.risk_manager.validate_trade(signal, portfolio, daily_trades_count)
                    
                    if is_safe:
                        self.log(f"Risk Check Passed. Executing...")
                        
                        # Calculate Quantity
                        quantity = self.risk_manager.calculate_position_size(signal, portfolio)
                        if quantity > 0:
                            success = self.executor.execute_order(signal, quantity)
                            if success:
                                daily_trades_count += 1
                                # Refresh portfolio state for next loop
                                portfolio = self.executor.get_portfolio_state()
                            else:
                                self.log("Execution failed.")
                                rejection_reasons.append(f"{ticker}: Execution failed (funds?)")
                        else:
                            self.log("Calculated quantity is 0 (insufficient funds?).")
                            rejection_reasons.append(f"{ticker}: Position size 0 (insufficient funds)")
                    else:
                        self.log(f"Risk Check Failed: {reason}")
                        rejection_reasons.append(f"{ticker}: Risk check ({reason})")
                else:
                    self.log(f"No trade signal from {strategy.name} for {ticker}")
                    rejection_reasons.append(f"{ticker}: No signal from {strategy.name}")

        # 6. End of Day Reporting
        summary_action = "TRADED" if daily_trades_count > 0 else "NO_TRADES"
        if daily_trades_count == 0:
            if not candidates:
                summary_reason = "Scanner found no candidates."
            elif rejection_reasons:
                # Summarize top reasons
                unique_reasons = list(set(rejection_reasons))
                if len(unique_reasons) > 5:
                    summary_reason = f"Analyzed {len(candidates)} candidates. Primary issue: " + (unique_reasons[0].split(':')[1] if ':' in unique_reasons[0] else unique_reasons[0])
                else:
                    summary_reason = "; ".join(unique_reasons[:3])
            else:
                summary_reason = "No actionable signals found."
        else:
            summary_reason = f"Executed {daily_trades_count} trades."

        self.executor.set_daily_summary({
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'action': summary_action,
            'reason': summary_reason,
            'trades_count': daily_trades_count
        })

        self.executor.update_live_values() # Ensure final state is saved for dashboard
        self.reporter.generate_daily_report()
        self.log("Daily Session Complete.")

if __name__ == "__main__":
    captain = Captain()
    captain.start_day()
