from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import math as m
import statistics as stat


class Trader:

    def __init__(self):
        pass

    def module_1_order_tapper(self, lob_buy_strikes, lob_sell_strikes, lob_buy_volume_per_strike, lob_sell_volume_per_strike, initial_inventory, inventory_limit, product, new_bid, new_ask):
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
        #if abs(initial_inventory - inventory_limit) <= (0.75 * inventory_limit):        # Shutting down module 1 when 75 % of inventory limit is reached -> reduces profit, but also less position risk
        for strike in lob_sell_strikes:
            if strike < new_ask:
                buy_volume = lob_sell_volume_per_strike[lob_sell_strikes.index(strike)]
                if abs(initial_inventory + buy_volume) <= inventory_limit:
                    new_orders.append(Order(product, strike, buy_volume))
                    #print("BUY ", buy_volume, "x ", product, " @ ", strike)
                    buy_volume_total += buy_volume
                else:
                    buy_volume = abs(inventory_limit - initial_inventory)
                    new_orders.append(Order(product, strike, buy_volume))
                    #print("BUY ", buy_volume, "x ", product, " @ ", strike)
                    buy_volume_total += buy_volume

        
        for strike in lob_buy_strikes:
            if strike > new_bid:
                sell_volume = lob_buy_volume_per_strike[lob_buy_strikes.index(strike)]
                if abs(initial_inventory - sell_volume) <= inventory_limit:
                    new_orders.append(Order(product, strike, -sell_volume))
                    #print("SELL ", -sell_volume, "x ", product, " @ ", strike)
                    sell_volume_total += sell_volume
                else:
                    sell_volume = abs(initial_inventory + inventory_limit)
                    new_orders.append(Order(product, strike, -sell_volume))
                    #print("SELL ", -sell_volume, "x ", product, " @ ", strike)
                    sell_volume_total += sell_volume
        return (new_orders, buy_volume_total, sell_volume_total)

    def module_2_market_maker(self, product, inventory_adj_bid: int, inventory_adj_ask: int, smart_price_bid: int, smart_price_ask: int, avail_buy_orders: int, avail_sell_orders: int):
        """
        Module for Market Making. This takes the bid/ask of the smart price and the bid and ask of the inventory adjusted bid/ask and places orders at them.
        The layout for both bid/ask is given by the level list, currently increasing the quantity as the distance to the smart price increases.
        The inventory adjusted bid/ask cant get below/above the bids/asks defined by the smart price, this would result in unfavorable exectuion prices. Instead, it "pushes" all orders breaking that rule to the smart price bid/ask and adds them up.
        
        
        Results for pearls:
            +2763 with [20, 15, 5, 7, 8, 9, 10, 11, 12] distribution // gamma = 0.34375  //  sigma = const = 0.74210853
            +2750 with [20, 15, 5, 7, 8, 9, 10, 11, 12] distribution // gamma = 0.34375
            +2750 with all orders at bid/ask // gamma = 0.34375
            +2741 with all orders at bid/ask // gamma = 0.375  //  sigma = const = 0.74210853
            +2728 with all orders at bid/ask // gamma = 0.375
            +2727 with all orders at bid/ask // gamma = 0.3125
            +2698 with all orders at bid/ask // gamma = 0.25
            +2685 with all orders at bid/ask // gamma = 0.4375
            +2660 with all orders at bid/ask // gamma = 0.5
            +2619 with all orders at bid/ask // gamma = 0.75
            +2612 with all orders at bid/ask // gamma = 1
            +2535 with [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] distribution // gamma = 0.75
            +2525 with [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] distribution // gamma = 0.5
            +2523 with all orders at bid/ask // gamma = 0.1
            +2515 with [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] distribution // gamma = 0.25
            +2485 with [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] distribution // gamma = 0.34375
            +2478 with [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] distribution // gamma = 1
            +2379 with [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] distribution // gamma = 0.75
            +2338 with all orders at bid/ask // gamma = 0
            +2037 with [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] distribution // gamma = 0
            +1725 with [4, 5, 6, 7, 8, 9, 10, 11, 12] distribution // gamma = 0.34375  //  full position management, even at unfavorable prices
            
            
            
        """
        buy_volume = 0
        sell_volume = 0
        level = [20, 15, 5, 7, 8, 9, 10, 11, 12]        # Maximum of 40 Orders currently possible, as the position limit is 20
        new_orders: list[Order] = []
        buy_order_layout = [0] * len(level)
        sell_order_layout = [0] * len(level)
        
        while buy_order_layout[8] < level[8]:
            while buy_order_layout[7] < level[7]:
                while buy_order_layout[6] < level[6]:
                    while buy_order_layout[5] < level[5]:
                        while buy_order_layout[4] < level[4]:
                            while buy_order_layout[3] < level[3]:
                                while buy_order_layout[2] < level[2]:
                                    while buy_order_layout[1] < level[1]:
                                        while buy_order_layout[0] < level[0] and avail_buy_orders > 0:
                                            buy_order_layout[0] += 1
                                            avail_buy_orders -= 1
                                        if avail_buy_orders <= 0: break
                                        buy_order_layout[1] += 1
                                        avail_buy_orders -= 1
                                    if avail_buy_orders <= 0: break
                                    buy_order_layout[2] += 1
                                    avail_buy_orders -= 1
                                if avail_buy_orders <= 0: break
                                buy_order_layout[3] += 1
                                avail_buy_orders -= 1
                            if avail_buy_orders <= 0:break
                            buy_order_layout[4] += 1
                            avail_buy_orders -= 1
                        if avail_buy_orders <= 0:break
                        buy_order_layout[5] += 1
                        avail_buy_orders -= 1
                    if avail_buy_orders <= 0:break
                    buy_order_layout[6] += 1
                    avail_buy_orders -= 1
                if avail_buy_orders <= 0:break
                buy_order_layout[7] += 1
                avail_buy_orders -= 1
            if avail_buy_orders <= 0:break
            buy_order_layout[8] += 1
            avail_buy_orders -= 1
            
        while sell_order_layout[8] < level[8]:
            while sell_order_layout[7] < level[7]:
                while sell_order_layout[6] < level[6]:
                    while sell_order_layout[5] < level[5]:
                        while sell_order_layout[4] < level[4]:
                            while sell_order_layout[3] < level[3]:
                                while sell_order_layout[2] < level[2]:
                                    while sell_order_layout[1] < level[1]:
                                        while sell_order_layout[0] < level[0] and avail_sell_orders > 0:
                                            sell_order_layout[0] += 1
                                            avail_sell_orders -= 1
                                        if avail_sell_orders <= 0: break
                                        sell_order_layout[1] += 1
                                        avail_sell_orders -= 1
                                    if avail_sell_orders <= 0: break
                                    sell_order_layout[2] += 1
                                    avail_sell_orders -= 1
                                if avail_sell_orders <= 0: break
                                sell_order_layout[3] += 1
                                avail_sell_orders -= 1
                            if avail_sell_orders <= 0:break
                            sell_order_layout[4] += 1
                            avail_sell_orders -= 1
                        if avail_sell_orders <= 0:break
                        sell_order_layout[5] += 1
                        avail_sell_orders -= 1
                    if avail_sell_orders <= 0:break
                    sell_order_layout[6] += 1
                    avail_sell_orders -= 1
                if avail_sell_orders <= 0:break
                sell_order_layout[7] += 1
                avail_sell_orders -= 1
            if avail_sell_orders <= 0:break
            sell_order_layout[8] += 1
            avail_sell_orders -= 1
        
        
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
            
        #print(buy_order_layout)
        #print(sell_order_layout)
            
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
            inventory: TradingState = state.position[product]
            return inventory
        else:
            return 0
    
    def calculate_smart_price(self, lob_average_buy: float, lob_average_sell: float, lob_buy_quantity: int, lob_sell_quantity: int) -> float:
        """
        Calculates the "Smart Price" described in "Machine Learning for Market Microstructure and High Frequency Trading" - Michael Kearns
        """
        samrt_price = ((lob_average_buy *  lob_sell_quantity) + (lob_average_sell * lob_buy_quantity) ) / (lob_buy_quantity + lob_sell_quantity)
        return samrt_price
    
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
        desired_inventory = 0
        gamma = 0.34375
    
    
        return (lob_average_buy, lob_average_sell, lob_buy_quantity, lob_sell_quantity, lob_buy_strikes, 
                lob_sell_strikes, lob_buy_volume_per_strike, lob_sell_volume_per_strike, inventory_limit,
                lob_buy_volume_total, lob_sell_volume_total, current_timestamp, desired_inventory, gamma)
    
    def calculate_return_volatility(self, smart_price: float, current_timestamp: int, product: str) -> list:
        """
        Calculates the price volatility rolling average of the last 50 smart prices.
        Indexing for historical_data matrices:
            First level indexing:   0 = Day at T - 49
                                    -1 = Current Day
            Second Level Indexing:  0 = Current timestamp
                                    1 = Smart price of current time period
                                    2 = Percentage change to prior time period
                                    3 = Sample standard deviation for the last 50 returns 
                                    4 = Deviation from 3 turned into an absolute value with the current smart price
        """
        global historical_data_pearls
        global historical_data_bananas
        
        lag_periods = 50
        
        if product == "PEARLS":
            if "historical_data_pearls" not in globals():
                historical_data_pearls = []
            
            if "historical_data_pearls" in globals():
                tradingstate_data = [current_timestamp, smart_price]
                historical_data_pearls.append(tradingstate_data)
                
                if len(historical_data_pearls) > lag_periods:
                    del historical_data_pearls[0]

                current_day_index = len(historical_data_pearls) - 1
                last_day_index = len(historical_data_pearls) - 2

                
                if len(historical_data_pearls) > 1 :
                    percentage_change = m.log(historical_data_pearls[current_day_index][1] / historical_data_pearls[last_day_index][1])
                    historical_data_pearls[current_day_index].append(percentage_change)
                    perc_standard_deviation = stat.stdev([x[2] for x in historical_data_pearls])
                    abs_standard_deviation = perc_standard_deviation * smart_price
                    historical_data_pearls[current_day_index].extend((perc_standard_deviation, abs_standard_deviation))
                    
                elif len(historical_data_pearls) <= 1 :
                    percentage_change = 0
                    perc_standard_deviation = 0
                    abs_standard_deviation = 0
                    historical_data_pearls[current_day_index].extend((percentage_change, perc_standard_deviation, abs_standard_deviation))
                
            
        return
    
    def calculate_reservation_price(self, product: str, current_inventory: int, desired_inventory: int, smart_price: float, gamma: float) -> float:
        """
        Calculates the Reservation price as defined by "High-frequency trading in a limit order book" - Marco Avellaneda & Sasha Stoikov.
        This price will be used to manage the inventory of the strategy. The parameter (T-t) from the formula will not be used as it is assumed that positions will be sold at the end of the time period anyway.
        Also, the parameter gamma will have a value of gamma = 0.5 while Avellaneda & Stoikov provide multiple ideas of the value gamma can have. Approaching zero would be a trader not caring about inventory risk, playing both sides of the mid price the same.
        On the other hand, a value of 1 would be a trader who would go great lengths to balance his portfolio
        """
        reservation_price = smart_price
        if product == "PEARLS":
            if len(historical_data_pearls) == 50:                   #
                abs_volatility = historical_data_pearls[-1][4]      #   This has to be here because AWS Lambda sometimes starts a new Trader instance, resulting in the loss of the data in historical_data_pearls
            elif len(historical_data_pearls) < 50:                  #   The provided value is the average of the backtested values
                abs_volatility = 0.74210853                         #
            
            reservation_price = smart_price - ((current_inventory - desired_inventory) * gamma * (abs_volatility)**2)
        
        return reservation_price
        
        
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Ttakes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        global historical_data_pearls
        global historical_data_bananas
        
        total_transmittable_orders = {}         # Initialize the method output dict as an empty dict


        for product in state.order_depths.keys():   # Iterate over all the available products contained in the order depths
        
        
            if product == 'PEARLS':                 #   !!!!    Make function that allocates number of shares to the different modules depending on volatility of the asset     !!!!
                
                
                
                
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
                lob_sell_volume_total,
                current_timestamp,
                desired_inventory,
                gamma) = self.initialize(state, 
                                        product)
                
                
                initial_inventory = self.get_initial_inventory(product, 
                                                                state)
                
                
                avail_buy_orders = inventory_limit - initial_inventory
                avail_sell_orders = inventory_limit + initial_inventory
                
                
                if lob_buy_volume_total > 0 and lob_sell_volume_total > 0:
                    
                    
                    smart_price = self.calculate_smart_price(lob_average_buy, 
                                                            lob_average_sell, 
                                                            lob_buy_quantity, 
                                                            lob_sell_quantity)
                    
                    self.calculate_return_volatility(smart_price, current_timestamp, product)
                    
                    (smart_price_bid, 
                    smart_price_ask) = self.calculate_bid_ask(smart_price, 3) # maximum spread as a percentage of market price? or at a percentage of smart price? 0.05 % bzw 5 bps des smart price?
                    
                    
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
                                                                    smart_price_ask)
                    
                    
                    avail_buy_orders -= mod_1_buy_volume
                    avail_sell_orders -= mod_1_sell_volume
                    current_inventory = initial_inventory + mod_1_buy_volume - mod_1_sell_volume
                    
                    #print("Smart Price: ", smart_price)
                    #print("Initial inventory:", initial_inventory)
                    #print("Current Inventory:", current_inventory)
                    #print("----------------")
                    
                    reservation_price = self.calculate_reservation_price(product, current_inventory, desired_inventory, smart_price, gamma)
                    
                    (inventory_adj_bid,
                    inventory_adj_ask) = self.calculate_bid_ask(reservation_price, 3)
                    
                    (mod_2_new_orders, 
                    mod_2_buy_volume, 
                    mod_2_sell_volume) = self.module_2_market_maker(product, 
                                                                    inventory_adj_bid, 
                                                                    inventory_adj_ask, 
                                                                    smart_price_bid, 
                                                                    smart_price_ask, 
                                                                    avail_buy_orders, 
                                                                    avail_sell_orders)
                    
                    
                    #print (initial_inventory, mod_1_buy_volume, mod_1_sell_volume, mod_2_buy_volume, mod_2_sell_volume)
                    
                    #print("Smart Price:", smart_price)
                    #print("Reservation Price:", reservation_price)
                    #print("Inventory:", current_inventory)
                    #print("av buy orders:", avail_buy_orders)
                    #print("av sell orders:", avail_sell_orders)
                    #print(mod_2_new_orders)
                    
                    
                    print(smart_price)
                    
                # Add all the above orders to the total_transmittable_orders dict
                
                total_transmittable_orders[product] = mod_1_new_orders + mod_2_new_orders  # + next list with orders
                #print(total_transmittable_orders[product])
                #new_list = [x.quantity for x in total_transmittable_orders[product]]
                #print(sum(new_list) + 2*initial_inventory)
                #print("---------------------")
            
            
            
        return total_transmittable_orders