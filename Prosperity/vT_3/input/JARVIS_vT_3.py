from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import math as m
import statistics as stat


class Trader:

    def __init__(self):
        pass

    def module_1_order_tapper(self, lob_buy_strikes, lob_sell_strikes, lob_buy_volume_per_strike, lob_sell_volume_per_strike, initial_inventory, inventory_limit, product, new_bid, new_ask, smart_price):
        """
        Takes the newly calculated bids and asks and checks if there are buy orders above the calculated bid or sell orders below the newly calculated ask. 
        This could also be done for the Smart Price and not for the bids and asks but this could result in resulting offers in between the bid and ask which takes away volume from the market making algo.
        Will need to backtest if either this method or using the Smart Price instead gives better results.
        """
        buy_volume = 0 
        sell_volume = 0
        buy_volume_total = 0
        sell_volume_total = 0
        new_orders: list[Order] = []
        for strike in lob_sell_strikes:
            if strike < new_ask:       # smart_price?
                buy_volume = lob_sell_volume_per_strike[lob_sell_strikes.index(strike)]
                if abs(initial_inventory + buy_volume_total + buy_volume) <= inventory_limit:
                    new_orders.append(Order(product, strike, buy_volume))
                    #print("BUY ", buy_volume, "x ", product, " @ ", strike)
                    buy_volume_total += buy_volume
                else:
                    buy_volume = abs(inventory_limit - initial_inventory - buy_volume_total)
                    new_orders.append(Order(product, strike, buy_volume))
                    #print("BUY ", buy_volume, "x ", product, " @ ", strike)
                    buy_volume_total += buy_volume

        
        for strike in lob_buy_strikes:
            if strike > new_bid:       #  smart_price?
                sell_volume = lob_buy_volume_per_strike[lob_buy_strikes.index(strike)]
                if abs(initial_inventory - sell_volume -sell_volume_total) <= inventory_limit:
                    new_orders.append(Order(product, strike, -sell_volume))
                    #print("SELL ", -sell_volume, "x ", product, " @ ", strike)
                    sell_volume_total += sell_volume
                else:
                    sell_volume = abs(initial_inventory + inventory_limit + sell_volume_total)
                    new_orders.append(Order(product, strike, -sell_volume))
                    #print("SELL ", -sell_volume, "x ", product, " @ ", strike)
                    sell_volume_total += sell_volume

        return (new_orders, buy_volume_total, sell_volume_total)

    def module_2_market_maker(self, product, inventory_adj_bid: int, inventory_adj_ask: int, smart_price_bid: int, smart_price_ask: int, avail_buy_orders: int, avail_sell_orders: int):
        """
        Module for Market Making. This takes the bid/ask of the smart price and the bid and ask of the inventory adjusted bid/ask and places orders at them.
        The layout for both bid/ask is given by poisson distribution with a lamda given to the function.
        The inventory adjusted bid/ask cant get below/above the bids/asks defined by the smart price, this would result in unfavorable exectuion prices. Instead, it "pushes" all orders breaking that rule to the smart price bid/ask and adds them up.
        """
        buy_volume = 0
        sell_volume = 0
        new_orders: list[Order] = []
        buy_order_layout = self.calculate_poisson_distribution(avail_buy_orders, 0.8)
        sell_order_layout = self.calculate_poisson_distribution(avail_sell_orders, 0.8)
        
        if inventory_adj_bid >= smart_price_bid:
            for bid_difference in range(abs(int(inventory_adj_bid) - int(smart_price_bid))):
                old_value = buy_order_layout.pop(0)
                if len(buy_order_layout) > 0:
                    buy_order_layout[0] +=  old_value
                else:
                    buy_order_layout = [old_value]
            for idx, bid_quantity in enumerate(buy_order_layout):
                if bid_quantity == 0: 
                    break
                new_orders.append(Order(product, (smart_price_bid - idx), bid_quantity))
                buy_volume += bid_quantity
                
        elif inventory_adj_bid < smart_price_bid:
            for idx, bid_quantity in enumerate(buy_order_layout):
                if bid_quantity == 0: 
                    break
                new_orders.append(Order(product, (inventory_adj_bid - idx), bid_quantity))
                buy_volume += bid_quantity
        
        
        if inventory_adj_ask < smart_price_ask:
            for ask_difference in range(abs(int(smart_price_ask) - int(inventory_adj_ask))):
                old_value = sell_order_layout.pop(0)
                if len(sell_order_layout) > 0:
                    sell_order_layout[0] +=  old_value
                else:
                    sell_order_layout = [old_value]
            for idx, ask_quantity in enumerate(sell_order_layout):
                if ask_quantity == 0: 
                    break
                new_orders.append(Order(product, (smart_price_ask + idx), -ask_quantity))
                sell_volume += ask_quantity
                
        elif inventory_adj_ask >= smart_price_ask:
            for idx, ask_quantity in enumerate(sell_order_layout):
                if ask_quantity == 0: 
                    break
                new_orders.append(Order(product, (inventory_adj_ask + idx), -ask_quantity))        
                sell_volume += ask_quantity
        
        #if product == "BANANAS":
        #    print(buy_order_layout)
        #    print(sell_order_layout)
            
        return (new_orders, buy_volume, sell_volume)

    def calculate_bid_ask(self, price: float, max_spread_width: int) -> int:
        """
        Calculates the Bid and Ask price from a given price with the maximum spread witdth.
        A value of max_spread_width = 2 results in spread widths of 2 and 1
        A value of max_spread_width = 3 results in spread widths of 2 and 3, while checking that the distance from either bid/ask to the smart price doesnt make up for more than 60% of the spread
        A value of max_spread_width = 4 results in spread widths of 4 and 3, while checking that the distance from either bid/ask to the smart price doesnt make up for more than 60% of the spread
        A value of max_spread_width = 5 results in spread widths of 4 and 5
        ...
        Note: max_spread_width has to be an integer to comply with game rules and cant be smaller than 2 -> max_spread_width=2 works but is not very clean because it can cause high imbalances in the proximity of the bids and asks to the smart price
        """
        if max_spread_width % 2 == 0:
            if isinstance(price, float):
                if price.is_integer():
                    new_bid = int(price - (max_spread_width/2))
                    new_ask = int(price + (max_spread_width/2))
                else:
                    new_bid = m.floor(price) - ((max_spread_width - 2) / 2)
                    new_ask = m.ceil(price) + ((max_spread_width - 2) / 2)
                    if max_spread_width > 2 and (price - new_bid) / max_spread_width > 0.6:
                        new_bid = new_bid + 1
                    if max_spread_width > 2 and (new_ask - price) / max_spread_width > 0.6:
                        new_ask = new_ask - 1
            elif isinstance(price, int):
                new_bid = int(price - (max_spread_width/2))
                new_ask = int(price + (max_spread_width/2))
            else:
                return
        else:
            if isinstance(price, float):
                if price.is_integer():
                    new_bid = int(price - ((max_spread_width - 1) / 2))
                    new_ask = int(price + ((max_spread_width - 1) / 2))
                else:
                    new_bid = m.floor(price) - ((max_spread_width - 1) / 2)
                    new_ask = m.ceil(price) + ((max_spread_width - 1) / 2)
                    if (price - new_bid) / max_spread_width > 0.6:
                        new_bid = new_bid + 1
                    elif (new_ask - price) / max_spread_width > 0.6:
                        new_ask = new_ask - 1
            elif isinstance(price, int):
                new_bid = int(price - ((max_spread_width - 1) / 2))
                new_ask = int(price + ((max_spread_width - 1) / 2))
            else:
                return
        return new_bid, new_ask 

    def get_initial_inventory(self, product: str, state: TradingState) -> int:
        """
        Get the initial inventory at the start of the TradingState for a given product
        """
        if product in state.position:
            inventory = state.position[product]
            return inventory
        else:
            return 0
    
    def calculate_smart_price(self, lob_average_buy: float, lob_average_sell: float, lob_buy_quantity: int, lob_sell_quantity: int) -> float:
        """
        Calculates the "Smart Price" described in "Machine Learning for Market Microstructure and High Frequency Trading" - Michael Kearns
        """
        smart_price = ((lob_average_buy *  lob_sell_quantity) + (lob_average_sell * lob_buy_quantity) ) / (lob_buy_quantity + lob_sell_quantity)
        return smart_price
    
    def initialize(self, state: TradingState, product):
        """
        Initialize and calculate all needed variables. I don't know how to use an __init__ ... 
        """
        if product == "PEARLS" or "BANANAS":
            inventory_limit = 20
        
        order_depth: OrderDepth = state.order_depths[product]   # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
        lob_buy_volume_total = m.fabs(m.fsum(order_depth.buy_orders.values()))       # Returns the absolute value of the aggregated buy order volumes of the orderbook (lob) --> positive
        lob_sell_volume_total = m.fabs(m.fsum(order_depth.sell_orders.values()))     # Returns the absolute value of the aggregated sell order volumes of the orderbook (lob) --> positive
        lob_buy_strikes = list(order_depth.buy_orders.keys())        # Returns a list of all unique strikes where at least 1 buy order has been submitted to the orderbook (lob) --> positive & low to high strikes
        lob_sell_strikes = list(order_depth.sell_orders.keys())      # Returns a list of all unique strikes where at least 1 sell order has been submitted to the orderbook (lob) --> positive & low to high strikes
        lob_buy_volume_per_strike = list(order_depth.buy_orders.values())        # Returns a list of volumes for the lob_buy_strikes --> positive & low to high strikes
        lob_sell_volume_per_strike = [-x for x in list(order_depth.sell_orders.values())]        # Returns a list of volumes for the lob_sell_strikes --> positive & low to high strikes
        lob_buy_strikes_w_vol = [lob_buy_strikes[lob_buy_volume_per_strike.index(x)] for x in lob_buy_volume_per_strike for i in range(x)]      # Returns a list of all buy strikes with the amount of strikes in the list given by their quantity in lob_buy_volume_per_strike
        lob_sell_strikes_w_vol = [lob_sell_strikes[lob_sell_volume_per_strike.index(x)] for x in lob_sell_volume_per_strike for i in range(x)]      # Returns a list of all sell strikes with the amount of strikes in the list given by their quantity in lob_sell_volume_per_strike
        lob_all_strikes_w_vol = lob_buy_strikes_w_vol + lob_sell_strikes_w_vol
        lob_average_buy = stat.fmean(lob_buy_strikes_w_vol)
        lob_average_sell = stat.fmean(lob_sell_strikes_w_vol)
        lob_buy_quantity = sum(lob_buy_volume_per_strike)
        lob_sell_quantity = sum(lob_sell_volume_per_strike) 
        best_ask = min(order_depth.sell_orders.keys())
        best_bid = max(order_depth.buy_orders.keys())
        mid_price = (best_ask + best_bid) / 2 
        current_timestamp = state.timestamp
        
    
    
        return (lob_average_buy, lob_average_sell, lob_buy_quantity, lob_sell_quantity, lob_buy_strikes, 
                lob_sell_strikes, lob_buy_volume_per_strike, lob_sell_volume_per_strike, inventory_limit,
                lob_buy_volume_total, lob_sell_volume_total)
    
    def calculate_reservation_price(self, product: str, current_inventory: int, desired_inventory: int, smart_price: float, gamma: float) -> float:
        """
        Calculates the Reservation price as defined by "High-frequency trading in a limit order book" - Marco Avellaneda & Sasha Stoikov.
        This price will be used to manage the inventory of the strategy. The parameter (T-t) from the formula will not be used as it is assumed that positions will be sold at the end of the time period anyway.
        Also, the parameter gamma will have a value of gamma = ?, while Avellaneda & Stoikov provide multiple ideas of the value gamma can have. Approaching zero would be a trader not caring about inventory risk, playing both sides of the mid price the same.
        On the other hand, a value of 1 would be a trader who would go great lengths to balance his portfolio.
        The values provided for the return probability standard deviation are the historical values calculated from the historical smart prices
        """
        reservation_price = smart_price
        if product == "PEARLS":
            abs_volatility = 7.38812499156771E-05 * smart_price 
            reservation_price = smart_price - ((current_inventory - desired_inventory) * gamma * (abs_volatility)**2)
        elif product == "BANANAS":
            abs_volatility = 1.46038979005149E-04 * smart_price 
            reservation_price = smart_price - ((current_inventory - desired_inventory) * gamma * (abs_volatility)**2)
        
        return reservation_price
        
    def calculate_poisson_distribution(self, available_orders: int, labda: float) -> list:
        """
        Calculates a Poisson distribution with lambda = labda and puts the availabla orders into the different lots according to the distribution.
        """
        no_levels = 5
        levels = []
        for k in range(no_levels):
            poisson = (pow(labda, k)) / (m.factorial(k)) * pow(m.e, -labda)
            current_level = round(poisson * available_orders)
            levels.append(current_level)

        while sum(levels) != available_orders:
            if sum(levels) > available_orders:
                idx = len(levels) - next(x for x, value in enumerate(reversed(levels)) if value > 0) - 1
                levels[idx] -= 1
            if sum(levels) < available_orders:
                levels[1] += 1
        
        return levels
        
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        
        total_transmittable_orders = {}         # Initialize the method output dict as an empty dict

        for product in state.order_depths.keys():   # Iterate over all the available products contained in the order depths
        
            if product == 'PEARLS':
                
                
                gamma = 0.4
                desired_inventory = 0
                spread_size = 3
                
                (lob_average_buy, 
                lob_average_sell, 
                lob_buy_quantity, 
                lob_sell_quantity, 
                lob_buy_strikes, 
                lob_sell_strikes, 
                lob_buy_volume_per_strike, 
                lob_sell_volume_per_strike, 
                inventory_limit,
                lob_buy_volume_total,
                lob_sell_volume_total) = self.initialize(state, 
                                                        product)
                
                initial_inventory = self.get_initial_inventory(product, 
                                                                state)
                
                print(initial_inventory)
                
                avail_buy_orders = inventory_limit - initial_inventory
                avail_sell_orders = inventory_limit + initial_inventory
                
                if lob_buy_volume_total > 0 and lob_sell_volume_total > 0:
                    
                    smart_price = self.calculate_smart_price(lob_average_buy, 
                                                            lob_average_sell, 
                                                            lob_buy_quantity, 
                                                            lob_sell_quantity)
                    
                    (smart_price_bid, 
                    smart_price_ask) = self.calculate_bid_ask(smart_price, spread_size) 
                    
                    (mod_1_new_orders,
                    mod_1_buy_volume,
                    mod_1_sell_volume) = self.module_1_order_tapper(lob_buy_strikes, 
                                                                    lob_sell_strikes, 
                                                                    lob_buy_volume_per_strike, 
                                                                    lob_sell_volume_per_strike, 
                                                                    initial_inventory, 
                                                                    inventory_limit, 
                                                                    product, 
                                                                    smart_price_bid, 
                                                                    smart_price_ask,
                                                                    smart_price)
                    
                    
                    if (1 * inventory_limit) - initial_inventory - mod_1_buy_volume < 0:
                        avail_buy_orders = 0
                    else:
                        avail_buy_orders = round(1 * inventory_limit) - initial_inventory - mod_1_buy_volume
                    if (1 * inventory_limit) + initial_inventory - mod_1_sell_volume < 0:
                        avail_sell_orders = 0
                    else:
                        avail_sell_orders = round(1 * inventory_limit) + initial_inventory - mod_1_sell_volume
                    
                    #avail_buy_orders -= mod_1_buy_volume
                    #avail_sell_orders -= mod_1_sell_volume
                    current_inventory = initial_inventory + mod_1_buy_volume - mod_1_sell_volume
                    
                    reservation_price = self.calculate_reservation_price(product,
                                                                        current_inventory,
                                                                        desired_inventory,
                                                                        smart_price,
                                                                        gamma)
                    
                    (inventory_adj_bid,
                    inventory_adj_ask) = self.calculate_bid_ask(reservation_price, spread_size)
                    
                    (mod_2_new_orders, 
                    mod_2_buy_volume, 
                    mod_2_sell_volume) = self.module_2_market_maker(product, 
                                                                    inventory_adj_bid, 
                                                                    inventory_adj_ask, 
                                                                    smart_price_bid, 
                                                                    smart_price_ask, 
                                                                    avail_buy_orders, 
                                                                    avail_sell_orders)
                
                total_transmittable_orders[product] = mod_1_new_orders + mod_2_new_orders  # + next list with orders
            
            if product == 'BANANAS':
                
                gamma = 0.34375
                desired_inventory = 0
                spread_size = 3
                
                (lob_average_buy, 
                lob_average_sell, 
                lob_buy_quantity, 
                lob_sell_quantity, 
                lob_buy_strikes, 
                lob_sell_strikes, 
                lob_buy_volume_per_strike, 
                lob_sell_volume_per_strike, 
                inventory_limit,
                lob_buy_volume_total,
                lob_sell_volume_total) = self.initialize(state, 
                                                        product)
                
                initial_inventory = self.get_initial_inventory(product, 
                                                                state)
                
                #print(initial_inventory)
                avail_buy_orders = inventory_limit - initial_inventory
                avail_sell_orders = inventory_limit + initial_inventory
                
                if lob_buy_volume_total > 0 and lob_sell_volume_total > 0:
                    
                    smart_price = self.calculate_smart_price(lob_average_buy, 
                                                            lob_average_sell, 
                                                            lob_buy_quantity, 
                                                            lob_sell_quantity)
                    
                    (smart_price_bid, 
                    smart_price_ask) = self.calculate_bid_ask(smart_price, spread_size)
                    
                    (mod_1_new_orders,
                    mod_1_buy_volume,
                    mod_1_sell_volume) = self.module_1_order_tapper(lob_buy_strikes, 
                                                                    lob_sell_strikes, 
                                                                    lob_buy_volume_per_strike, 
                                                                    lob_sell_volume_per_strike, 
                                                                    initial_inventory, 
                                                                    inventory_limit, 
                                                                    product, 
                                                                    smart_price_bid, 
                                                                    smart_price_ask,
                                                                    smart_price)
                    
                    if (1 * inventory_limit) - initial_inventory - mod_1_buy_volume < 0:
                        avail_buy_orders = 0
                    else:
                        avail_buy_orders = round(1 * inventory_limit) - initial_inventory - mod_1_buy_volume
                    if (1 * inventory_limit) + initial_inventory - mod_1_sell_volume < 0:
                        avail_sell_orders = 0
                    else:
                        avail_sell_orders = round(1 * inventory_limit) + initial_inventory - mod_1_sell_volume
                    
                    #avail_buy_orders -= mod_1_buy_volume
                    #avail_sell_orders -= mod_1_sell_volume
                    current_inventory = initial_inventory + mod_1_buy_volume - mod_1_sell_volume
                    
                    reservation_price = self.calculate_reservation_price(product,
                                                                        current_inventory,
                                                                        desired_inventory,
                                                                        smart_price,
                                                                        gamma)
                    
                    (inventory_adj_bid,
                    inventory_adj_ask) = self.calculate_bid_ask(reservation_price, spread_size)
                    
                    (mod_2_new_orders, 
                    mod_2_buy_volume, 
                    mod_2_sell_volume) = self.module_2_market_maker(product, 
                                                                    inventory_adj_bid, 
                                                                    inventory_adj_ask, 
                                                                    smart_price_bid, 
                                                                    smart_price_ask, 
                                                                    avail_buy_orders, 
                                                                    avail_sell_orders)
                
                total_transmittable_orders[product] = mod_1_new_orders + mod_2_new_orders  # + next list with orders

        return total_transmittable_orders