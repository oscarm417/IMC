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
                buy_orders = order_depth.buy_orders
                sell_orders = order_depth.sell_orders
                
                if product in state.observations:
                    observations = state.observations[product]
                
                if product in state.position:
                    position = state.position[product]
                
                if "PEARLS" in state.market_trades or "BANANAS" in state.market_trades:
                    market_trades = state.market_trades

        return result