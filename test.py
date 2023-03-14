from typing import Dict, List
from datamodel import TradingState, Order

running_count = 0

class Trader:
    def run(self, state: TradingState):
        global running_count
        running_count += 1
        
        print(running_count)
        
        return