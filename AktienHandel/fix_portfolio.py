"""
Quick script to recalculate and fix the portfolio total_value.
Run this to update portfolio.json with correct values.
"""
from agents.execution import ExecutionAgent

def main():
    print("Recalculating portfolio values...")
    executor = ExecutionAgent()
    
    # Get current state (this will calculate total_value correctly)
    state = executor.get_portfolio_state()
    
    print("\n" + "="*60)
    print("Portfolio Recalculation Complete")
    print("="*60)
    print(f"Cash:              EUR {state['cash']:.2f}")
    print(f"Total Value:       EUR {state['total_value']:.2f}")
    print(f"Invested in Stocks: EUR {state['total_value'] - state['cash']:.2f}")
    print(f"Profit/Loss:       EUR {state['profit_loss']:.2f}")
    print(f"Return:            {state['return_pct']:.2f}%")
    print("\nHoldings:")
    for ticker, qty in state.get('holdings', {}).items():
        print(f"  {ticker}: {qty} shares")
    print("="*60)
    
    # Save the corrected state
    executor.save_portfolio(state)
    print("\nPortfolio saved successfully!")

if __name__ == "__main__":
    main()
