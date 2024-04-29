import asyncio
import os
import time
from typing import List, Tuple

import octobot_commons.symbols as symbols
import octobot_commons.os_util as os_util
import triangular_arbitrage.detector as detector
from binance.client import Client

# Binance API configuration
BINANCE_API_KEY = "your_binance_api_key"
BINANCE_API_SECRET = "your_binance_api_secret"

# Initialize Binance client
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

async def execute_trade(opportunity: detector.ShortTicker, order_side: str, order_amount: float) -> bool:
    """
    Execute a trade based on the detected arbitrage opportunity.
    
    Args:
        opportunity (detector.ShortTicker): The detected arbitrage opportunity.
        order_side (str): The side of the order ('buy' or 'sell').
        order_amount (float): The amount of the order.
    
    Returns:
        bool: True if the trade was executed successfully, False otherwise.
    """
    try:
        symbol = str(opportunity.symbol)
        if order_side == 'buy':
            order = client.order_market_buy(symbol=symbol, quantity=order_amount)
        else:
            order = client.order_market_sell(symbol=symbol, quantity=order_amount)
        return order['status'] == 'FILLED'
    except Exception as e:
        print(f"Error executing trade: {e}")
        return False

async def triangular_arbitrage(exchange_name: str) -> Tuple[List[detector.ShortTicker], float]:
    """
    Detect and execute triangular arbitrage opportunities on the specified exchange.
    
    Args:
        exchange_name (str): The name of the exchange to scan for arbitrage opportunities.
    
    Returns:
        Tuple[List[detector.ShortTicker], float]: A tuple containing the best arbitrage opportunities and the best profit.
    """
    best_opportunities, best_profit = await detector.run_detection(exchange_name)
    
    if best_opportunities is not None:
        # Execute trades for the best arbitrage opportunities
        for i, opportunity in enumerate(best_opportunities):
            order_side = 'buy' if opportunity.reversed else 'sell'
            order_amount = 100  # Adjust the order amount as needed
            executed = await execute_trade(opportunity, order_side, order_amount)
            if executed:
                print(f"{i+1}. {order_side} {str(opportunity.symbol)} executed successfully")
            else:
                print(f"{i+1}. {order_side} {str(opportunity.symbol)} failed to execute")
    
    return best_opportunities, best_profit

async def main():
    benchmark = os_util.parse_boolean_environment_var("IS_BENCHMARKING", "False")
    if benchmark:
        start_time = time.perf_counter()
    
    # Start arbitrage detection and execution
    print("Scanning for triangular arbitrage opportunities...")
    best_opportunities, best_profit = await triangular_arbitrage("binance")
    
    if best_opportunities is not None:
        print("-------------------------------------------")
        print(f"New {round(best_profit, 4)}% Binance opportunity:")
        for i, opportunity in enumerate(best_opportunities):
            order_side = 'buy' if opportunity.reversed else 'sell'
            print(f"{i+1}. {order_side} {str(opportunity.symbol)}")
        print("-------------------------------------------")
    else:
        print("No arbitrage opportunity detected")
    
    if benchmark:
        elapsed_time = time.perf_counter() - start_time
        print(f"{__file__} executed in {elapsed_time:0.2f} seconds.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
