from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order


class Trader:

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        
        result = {}
        
        for product in state.order_depths.keys():
            
            if product == 'BANANAS':
                
                order_depth: OrderDepth = state.order_depths[product]
                
                print(order_depth.buy_orders, order_depth.sell_orders)

        return result