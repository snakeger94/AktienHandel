
from agents.execution import ExecutionAgent
import time

def refresh():
    print("Refreshing portfolio values from live market data...")
    agent = ExecutionAgent()
    state = agent.update_live_values()
    
    print("\nUpdated Portfolio State:")
    print(f"Total Value: EUR {state['total_value']:.2f}")
    print(f"Cash:        EUR {state['cash']:.2f}")
    print(f"Holdings Value: EUR {state['total_value'] - state['cash']:.2f}")
    print("Done.")

if __name__ == "__main__":
    refresh()
