from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import math as m
import statistics as stat


class Trader:

    def __init__(self):
        self.product_parameters = {'PEARLS':{
                                    'inventory_limit': 20, 'fair_price' : 10000,
                                    'lower_inventory_limit': -20, 'upper_inventory_limit': 20
                                    },
                                    
                                    'BANANAS':{
                                    'inventory_limit': 20, 'fair_price' : 5000,
                                    'lower_inventory_limit': -20, 'upper_inventory_limit': 20
                                    },
                                    
                                    'COCONUTS':{
                                    'inventory_limit': 555, 'fair_price' : 8000,
                                    'lower_inventory_limit': -600, 'upper_inventory_limit': 600
                                    },
                                    
                                    'PINA_COLADAS':{
                                    'inventory_limit': 296, 'fair_price' : 15000,
                                    'lower_inventory_limit': -300, 'upper_inventory_limit': 300
                                    },
                                    
                                    'DIVING_GEAR':{
                                    'inventory_limit': 50, 'buy_sell_signal': 0,
                                    'mid_price_ema':[], 'ema_count': 0,
                                    'lower_inventory_limit': -50, 'upper_inventory_limit': 50
                                    },
                                    
                                    'BERRIES':{
                                    'inventory_limit': 250, 'fair_price' : 0,
                                    'lower_inventory_limit': -250, 'upper_inventory_limit': 250
                                    },
                                    
                                    'DOLPHIN_SIGHTINGS':{
                                    'last_sightings': 0
                                    },
                                }
        self.stat_arb_pair_parameters = {
            "COCONUTS_PINA_COLADAS":{'mean_ratio': 1.875, 'stdev_ratio': 0.00447052512964639, 'mean_ratio_backtest': 1.874649044228040, 'stdev_ratio_backtest': 0.0014590944891508,
                                    'coconuts_order_minimum': 15, 'pina_coladas_order_minimum': 8, 'trade_opportunities': 37}
        }
        
    
    def module_1_order_tapper(self, lob_buy_strikes, lob_sell_strikes, lob_buy_volume_per_strike, lob_sell_volume_per_strike, initial_inventory, inventory_limit, product, new_bid, new_ask, timestamp):
        """
        Takes the newly calculated bids and asks and checks if there are buy orders above the calculated bid or sell orders below the newly calculated ask. 
        This could also be done for the Smart Price and not for the bids and asks but this could result in resulting offers in between the bid and ask which takes away volume from the market making algo.
        Will need to backtest if either this method or using the Smart Price instead gives better results.
        """
        timestamp = timestamp/100
        buy_volume = 0 
        sell_volume = 0
        buy_volume_total = 0
        sell_volume_total = 0
        new_orders: list[Order] = []
        for strike in lob_sell_strikes:
            if strike < new_ask:
                if product == 'BERRIES' and 5000 < timestamp < 7000:
                    break
                buy_volume = lob_sell_volume_per_strike[lob_sell_strikes.index(strike)]
                if abs(initial_inventory + buy_volume_total + buy_volume) <= inventory_limit:
                    new_orders.append(Order(product, strike, buy_volume))
                    buy_volume_total += buy_volume
                else:
                    buy_volume = abs(inventory_limit - initial_inventory - buy_volume_total)
                    new_orders.append(Order(product, strike, buy_volume))
                    buy_volume_total += buy_volume
                    break
        
        for strike in reversed(lob_buy_strikes):
            if strike > new_bid:
                if product == 'BERRIES' and 2000 < timestamp < 5000:
                    break
                sell_volume = lob_buy_volume_per_strike[lob_buy_strikes.index(strike)]
                if abs(initial_inventory - sell_volume - sell_volume_total) <= inventory_limit:
                    new_orders.append(Order(product, strike, -sell_volume))
                    sell_volume_total += sell_volume
                else:
                    sell_volume = abs(initial_inventory + inventory_limit - sell_volume_total)
                    new_orders.append(Order(product, strike, -sell_volume))
                    sell_volume_total += sell_volume
                    break
        
        buy_volume = 0
        sell_volume = 0
        
        if product == 'BERRIES' and 2500 < timestamp < 4800:
            #check if position limit is reached, otherwise buy at best ask
            if abs(initial_inventory + buy_volume_total + buy_volume) <= inventory_limit:
                difference_to_limit = inventory_limit - abs(initial_inventory + buy_volume_total + buy_volume)
                needed_volume = min(lob_sell_volume_per_strike[0], difference_to_limit)
                new_orders.append(Order(product, lob_sell_strikes[0], needed_volume))
                buy_volume_total += needed_volume
        
        if product == 'BERRIES' and 5200 < timestamp < 7000:
            #check if position limit is reached otherwise sell at best bid
            if abs(initial_inventory - sell_volume - sell_volume_total) <= inventory_limit:
                difference_to_limit = inventory_limit - abs(initial_inventory - sell_volume - sell_volume_total)
                needed_volume = min(lob_buy_volume_per_strike[-1], difference_to_limit)
                new_orders.append(Order(product, lob_buy_strikes[-1], -needed_volume))
                sell_volume_total += needed_volume
        
        return (new_orders, buy_volume_total, sell_volume_total)

    def module_2_market_maker(self, product: str, smart_price_bid: int, smart_price_ask: int, avail_buy_orders: int, avail_sell_orders: int):
        """
        Module for Market Making. This takes the bid/ask of the smart price and places orders at them.
        """
        new_orders: list[Order] = []
        
        new_orders.append(Order(product, (smart_price_bid), avail_buy_orders))
        new_orders.append(Order(product, (smart_price_ask), -avail_sell_orders))
        
        return (new_orders)
    
    def calculate_bid_ask(self, product: str, smart_price: float, lob_buy_strikes: list, lob_sell_strikes: list):
        """
        Calculates the the best available Bid/Ask price to maximize profit.
        """
        
        for idx, bid_strike in enumerate(list(reversed(lob_buy_strikes))):
            if smart_price > bid_strike and abs(smart_price - bid_strike) > 1:
                smart_price_bid = bid_strike + 1
                break
            elif idx+1 == len(lob_buy_strikes):
                smart_price_bid = m.floor(smart_price) - 1
                break
        
        for idx, ask_strike in enumerate(lob_sell_strikes):
            if smart_price < ask_strike and abs(smart_price - ask_strike) > 1:
                smart_price_ask = ask_strike - 1
                break
            elif idx+1 == len(lob_sell_strikes):
                smart_price_ask = m.ceil(smart_price) + 1
                break
        
        while smart_price_ask in lob_sell_strikes and smart_price_ask - 1 >= smart_price:
            smart_price_ask -= 1
        
        while smart_price_bid in lob_buy_strikes and smart_price_bid + 1 <= smart_price:
            smart_price_bid += 1
        
        
        return smart_price_bid, smart_price_ask
    
    def calculate_smart_price(self, lob_average_buy: float, lob_average_sell: float, lob_buy_quantity: int, lob_sell_quantity: int) -> float:
        """
        Calculates the "Smart Price" described in "Machine Learning for Market Microstructure and High Frequency Trading" - Michael Kearns
        """
        smart_price = ((lob_average_buy *  lob_sell_quantity) + (lob_average_sell * lob_buy_quantity) ) / (lob_buy_quantity + lob_sell_quantity)
        
        return smart_price
    
    def initialize(self, state: TradingState, product):
        """
        Initialize and calculate all needed variables
        """
        inventory_limit = self.product_parameters[product]['inventory_limit']
        order_depth: OrderDepth = state.order_depths[product]   # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
        lob_buy_volume_total = m.fabs(m.fsum(order_depth.buy_orders.values()))       # Returns the absolute value of the aggregated buy order volumes of the orderbook (lob) --> positive
        lob_sell_volume_total = m.fabs(m.fsum(order_depth.sell_orders.values()))     # Returns the absolute value of the aggregated sell order volumes of the orderbook (lob) --> positive
        lob_buy_strikes = list(order_depth.buy_orders.keys())        # Returns a list of all unique strikes where at least 1 buy order has been submitted to the orderbook (lob) --> positive & low to high strikes
        lob_sell_strikes = list(order_depth.sell_orders.keys())      # Returns a list of all unique strikes where at least 1 sell order has been submitted to the orderbook (lob) --> positive & low to high strikes
        lob_buy_volume_per_strike = list(order_depth.buy_orders.values())        # Returns a list of volumes for the lob_buy_strikes --> positive & low to high strikes
        lob_sell_volume_per_strike = [-x for x in list(order_depth.sell_orders.values())]        # Returns a list of volumes for the lob_sell_strikes --> positive & low to high strikes
        lob_buy_strikes_w_vol = [lob_buy_strikes[lob_buy_volume_per_strike.index(x)] for x in lob_buy_volume_per_strike for i in range(x)]      # Returns a list of all buy strikes with the amount of strikes in the list given by their quantity in lob_buy_volume_per_strike
        lob_sell_strikes_w_vol = [lob_sell_strikes[lob_sell_volume_per_strike.index(x)] for x in lob_sell_volume_per_strike for i in range(x)]      # Returns a list of all sell strikes with the amount of strikes in the list given by their quantity in lob_sell_volume_per_strike
        lob_average_buy = stat.fmean(lob_buy_strikes_w_vol)
        lob_average_sell = stat.fmean(lob_sell_strikes_w_vol)
        lob_buy_quantity = sum(lob_buy_volume_per_strike)
        lob_sell_quantity = sum(lob_sell_volume_per_strike) 

        return (lob_average_buy, lob_average_sell, lob_buy_quantity, lob_sell_quantity, lob_buy_strikes, 
                lob_sell_strikes, lob_buy_volume_per_strike, lob_sell_volume_per_strike, inventory_limit,
                lob_buy_volume_total, lob_sell_volume_total)
    
    def calculate_available_buy_and_sell(self, product: str, inventory_limit: int, initial_inventory: int, buy_volume: int, sell_volume: int, timestamp: int):
        """
        Calculates the buy and sell orders still available taking the module 1 orders into account
        """
        
        if product == 'BERRIES':
            self.adjust_berry_limits(product, timestamp)
        
        upper_bound = self.product_parameters[product]['upper_inventory_limit']
        lower_bound = self.product_parameters[product]['lower_inventory_limit']
        
        if min(upper_bound, inventory_limit) - initial_inventory - buy_volume < 0:
            avail_buy_orders = 0
        else:
            avail_buy_orders = min(upper_bound, inventory_limit) - initial_inventory - buy_volume
        
        if abs(max(lower_bound, -inventory_limit)) + initial_inventory - sell_volume < 0:
            avail_sell_orders = 0
        else:
            avail_sell_orders = abs(max(lower_bound, -inventory_limit)) + initial_inventory - sell_volume
        
        return round(avail_buy_orders), round(avail_sell_orders)
    
    def adjust_berry_limits(self, product: str,timestamp: int):
        timestamp = timestamp/100
        current_upper = self.product_parameters[product]['upper_inventory_limit']
        current_lower = self.product_parameters[product]['lower_inventory_limit']
        
        if timestamp <= 2000:
            lower_increment = timestamp*(250/2000)
            current_lower = -250 + lower_increment
            self.product_parameters[product]['upper_inventory_limit'] = 250
            self.product_parameters[product]['lower_inventory_limit'] = current_lower #going towards zero 

        elif 2000 < timestamp <= 2500 :
            lower_increment = (timestamp-2000)*(250/500)
            current_lower = 0 + lower_increment
            self.product_parameters[product]['upper_inventory_limit'] = 250
            self.product_parameters[product]['lower_inventory_limit'] = current_lower #going towards 250 
        
        elif 2500 < timestamp <= 4800 :
            self.product_parameters[product]['upper_inventory_limit'] = 250 #Full long
            self.product_parameters[product]['lower_inventory_limit'] = 250 #Full long

        elif 4800 < timestamp <= 4900 :
            lower_increment = (timestamp-4800)*(250/100)
            current_lower = 250 + -lower_increment  
            self.product_parameters[product]['upper_inventory_limit'] = 250
            self.product_parameters[product]['lower_inventory_limit'] = current_lower #go towards 0
        
        elif 4900 < timestamp <= 5100 :  
            increment = (timestamp-4900)*(250/200)
            current_upper = 250 - increment 
            current_lower = 0 - increment
            self.product_parameters[product]['upper_inventory_limit'] = current_upper #go twoards 0
            self.product_parameters[product]['lower_inventory_limit'] = current_lower #go towards -250

        elif 5100 < timestamp <= 5200 : #full short 
            increment = (timestamp-5100)*(250/100)
            current_upper = 0 - increment
            self.product_parameters[product]['upper_inventory_limit'] = current_upper #go towards -250 
            self.product_parameters[product]['lower_inventory_limit'] = -250

        elif 5200 < timestamp <= 7000 :#Full short
            self.product_parameters[product]['upper_inventory_limit'] = -250
            self.product_parameters[product]['lower_inventory_limit'] = -250
        
        elif 7000 < timestamp: #back to MM
            self.product_parameters[product]['upper_inventory_limit'] = 100
            self.product_parameters[product]['lower_inventory_limit'] = -100
    
    def pearls_bananas_berries_trade_logic(self, product: str, state: TradingState):
        """
        Market making logic for Bananas and Pearls only. 
        Defining Smart_price, setting a bid/ask from there, clearing all orders in between and pushing all remaining orders to the bid/ask. Works like a charm
        """
        # TIME 
        timestamp  = state.timestamp
        
        #UPDATE INITIAL INVENTORY
        initial_inventory = state.position.get(product,0)
        
        
        #DEFINE AND GET ALL NEEDED ORDERBOOK DATA
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
        lob_sell_volume_total) = self.initialize(state, product)
        
        #CHECKS IF THERE ARE ORDERS ON BOTH SIDES OF THE ORDERBOOK
        if lob_buy_volume_total > 0 and lob_sell_volume_total > 0:
            
            #CALC SMART PRICE
            smart_price = self.calculate_smart_price(lob_average_buy, 
                                                    lob_average_sell, 
                                                    lob_buy_quantity, 
                                                    lob_sell_quantity)
            
            #CALC BID/ASK
            smart_price_bid, smart_price_ask = self.calculate_bid_ask(product, smart_price, lob_buy_strikes, lob_sell_strikes)
            
            #MOD1 BUY AND SELL ORDERS 
            
            mod_1_new_orders, mod_1_buy_volume, mod_1_sell_volume = self.module_1_order_tapper(lob_buy_strikes, 
                                                                                                lob_sell_strikes, 
                                                                                                lob_buy_volume_per_strike, 
                                                                                                lob_sell_volume_per_strike, 
                                                                                                initial_inventory, 
                                                                                                inventory_limit, 
                                                                                                product, 
                                                                                                smart_price_bid, 
                                                                                                smart_price_ask,
                                                                                                timestamp
                                                                                                )
            
            #AVAILABLE BUYS AND SELLS AFTER MOD 1 ORDERS ARE EXECUTED
            avail_buy_orders, avail_sell_orders = self.calculate_available_buy_and_sell(product, inventory_limit, initial_inventory, mod_1_buy_volume, mod_1_sell_volume, timestamp)
            
            #MOD2 BUY AND SELL ORDERS
            mod_2_new_orders = self.module_2_market_maker(product, 
                                                        smart_price_bid, 
                                                        smart_price_ask, 
                                                        avail_buy_orders, 
                                                        avail_sell_orders
                                                        )
            
            #RETURN ALL ORDER DATA AND THE DATA NEEDED FOR VISUALIZATION
            return mod_1_new_orders, mod_2_new_orders
        
        elif lob_buy_volume_total > 0 and not lob_sell_volume_total > 0:
            initial_inventory = state.position.get(product, 0)
            ridiculous_sell_order = []
            avail_buy_orders, avail_sell_orders = self.calculate_available_buy_and_sell(product, inventory_limit, initial_inventory, 0, 0)
            
            sell_price = round(lob_average_buy * 1.005)
            
            ridiculous_sell_order.append(Order(product, sell_price, -avail_sell_orders))
            
            return ridiculous_sell_order
        
        elif not lob_buy_volume_total > 0 and lob_sell_volume_total > 0:
            initial_inventory = state.position.get(product, 0)
            ridiculous_buy_order = []
            avail_buy_orders, avail_sell_orders = self.calculate_available_buy_and_sell(product, inventory_limit, initial_inventory, 0, 0)
            
            buy_price = round(lob_average_sell * 0.995)
            
            ridiculous_buy_order.append(Order(product, buy_price, avail_buy_orders))
            
            return ridiculous_buy_order
    
    def pina_coco_trade_logic(self, state: TradingState, product_1: str, product_2: str):
        """
        Stat Arb trade logic for pina coladas and coconut order pair
        Product 2 is always the product which needs to be more expensive. That is how the mean ratio is currently defined.
        If z-Score is positive that means current ratio is bigger than mean. We should then go long in product_1 and short in product_2
        If z-Score is negative that means current ratio is lower than mean. We should then go short in product_1 and long in product_2
        z_score_acutal is ALWAYS closer to 0 than z_score_mid.
        """
        product_1_orders: list[Order] = []
        product_2_orders: list[Order] = []
        
        z_score_for_max_orders = 2
        z_score_for_strategy_start = 0.7
        
        pair_key = product_1+"_"+product_2
        
        product_1_order_multiplier = self.stat_arb_pair_parameters[pair_key]['coconuts_order_minimum']
        product_2_order_multiplier = self.stat_arb_pair_parameters[pair_key]['pina_coladas_order_minimum']
        
        product_1_inventory_limit = self.product_parameters[product_1]['inventory_limit']
        product_2_inventory_limit = self.product_parameters[product_2]['inventory_limit']
        
        trade_opportunities = self.stat_arb_pair_parameters[pair_key]['trade_opportunities']
        
        product_1_max_orders = product_1_order_multiplier * trade_opportunities
        product_2_max_orders = product_2_order_multiplier * trade_opportunities
        
        mean_ratio = self.stat_arb_pair_parameters[pair_key]['mean_ratio']
        stdev_ratio = self.stat_arb_pair_parameters[pair_key]['stdev_ratio']
        
        order_depth_product_1: OrderDepth = state.order_depths[product_1]
        order_depth_product_2: OrderDepth = state.order_depths[product_2]
        
        initial_position_product_1 = state.position.get(product_1, 0)
        initial_position_product_2 = state.position.get(product_2, 0)
        
        best_bid_product_1 = max(order_depth_product_1.buy_orders.keys())
        best_ask_product_1 = min(order_depth_product_1.sell_orders.keys())
        best_bid_volume_product_1 = abs(list(order_depth_product_1.buy_orders.values())[-1])
        best_bid_avail_units_product_1 = int(best_bid_volume_product_1 / product_1_order_multiplier)
        best_ask_volume_product_1 = abs(list(order_depth_product_1.sell_orders.values())[0])
        best_ask_avail_units_product_1 = int(best_ask_volume_product_1 /  product_1_order_multiplier)
        mid_price_product_1 = stat.fmean([best_bid_product_1, best_ask_product_1])
        
        
        best_bid_product_2 = max(order_depth_product_2.buy_orders.keys())
        best_ask_product_2 = min(order_depth_product_2.sell_orders.keys())
        best_bid_volume_product_2 = abs(list(order_depth_product_2.buy_orders.values())[-1])
        best_bid_avail_units_product_2 = int(best_bid_volume_product_2 / product_2_order_multiplier)
        best_ask_volume_product_2 = abs(list(order_depth_product_2.sell_orders.values())[0])
        best_ask_avail_units_product_2 = int(best_ask_volume_product_2 /  product_2_order_multiplier)
        mid_price_product_2 = stat.fmean([best_bid_product_2, best_ask_product_2])
        
        current_mid_ratio = mid_price_product_2 / mid_price_product_1
        
        z_score_mid = (current_mid_ratio - mean_ratio) / stdev_ratio
        
        
        if z_score_mid > z_score_for_strategy_start:
            current_ratio = best_bid_product_2/best_ask_product_1
            z_score_actual = (current_ratio - mean_ratio) / stdev_ratio
            
            if z_score_actual > z_score_for_strategy_start :
                desired_position_product_1 = min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_1_order_multiplier), product_1_max_orders)
                desired_position_product_2 = - min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_2_order_multiplier), product_2_max_orders)
                if desired_position_product_1 >= product_1_inventory_limit:
                    desired_position_product_1 = product_1_inventory_limit
                    desired_position_product_2 = - product_2_inventory_limit
                #print(z_score_mid, z_score_actual)
            else:
                desired_position_product_1 = 0
                desired_position_product_2 = 0
            
            
        elif z_score_mid < - z_score_for_strategy_start:
            current_ratio = best_ask_product_2/best_bid_product_1
            z_score_actual = (current_ratio - mean_ratio) / stdev_ratio
            
            if z_score_actual < - z_score_for_strategy_start:
                desired_position_product_1 = min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_1_order_multiplier), product_1_max_orders)
                desired_position_product_2 = -min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_2_order_multiplier), product_2_max_orders)
                if desired_position_product_2 >= product_2_inventory_limit:
                    desired_position_product_1 = - product_1_inventory_limit
                    desired_position_product_2 = product_2_inventory_limit
                #print(z_score_mid, z_score_actual)
            else:
                desired_position_product_1 = 0
                desired_position_product_2 = 0
        else:
            desired_position_product_1 = 0
            desired_position_product_2 = 0
        
        
        if initial_position_product_1 >= 0 and z_score_mid > 0: 
            if initial_position_product_1 < desired_position_product_1:
                # Add more, long 1 short 2
                available_units = min(best_ask_avail_units_product_1, best_bid_avail_units_product_2)
                product_1_orders.append(Order(product_1, best_ask_product_1, min((available_units * product_1_order_multiplier), abs(desired_position_product_1 - initial_position_product_1))))
                product_2_orders.append(Order(product_2, best_bid_product_2, -min((available_units * product_2_order_multiplier), abs(desired_position_product_2 - initial_position_product_2))))
                
            
        elif initial_position_product_1 > 0 and z_score_mid <= 0:
            # Neutralize everything we have
            available_units = min(best_bid_avail_units_product_1, best_ask_avail_units_product_2)
            product_1_orders.append(Order(product_1, best_bid_product_1, - min((available_units * product_1_order_multiplier), abs(desired_position_product_1 - initial_position_product_1))))
            product_2_orders.append(Order(product_2, best_ask_product_2, min((available_units * product_2_order_multiplier), abs(desired_position_product_2 - initial_position_product_2))))
        
        
        elif initial_position_product_1 < 0 and z_score_mid >= 0: 
            # Neutralize everything we have
            available_units = min(best_ask_avail_units_product_1, best_bid_avail_units_product_2)
            product_1_orders.append(Order(product_1, best_ask_product_1, min((available_units * product_1_order_multiplier), abs(desired_position_product_1 - initial_position_product_1))))
            product_2_orders.append(Order(product_2, best_bid_product_2, - min((available_units * product_2_order_multiplier), abs(desired_position_product_2 - initial_position_product_2))))
            
            
        elif initial_position_product_1 <= 0 and z_score_mid < 0:
            if initial_position_product_1 > desired_position_product_1:
                #add more, short 1 long 2
                available_units = min(best_bid_avail_units_product_1, best_ask_avail_units_product_2)
                product_1_orders.append(Order(product_1, best_bid_product_1, - min((available_units * product_1_order_multiplier), abs(desired_position_product_1 - initial_position_product_1))))
                product_2_orders.append(Order(product_2, best_ask_product_2, min((available_units * product_2_order_multiplier), abs(desired_position_product_2 - initial_position_product_2))))
        
        
        
        return product_1_orders, product_2_orders
    
    def normalize_data(self,data,max_val,min_val):
        return (data-min_val)/(max_val-min_val)
    
    def calc_vol(self,spread,spread_mean,spread_len):
        numerator = m.pow(spread-spread_mean,2)
        denom = spread_len -1
        inner = numerator/denom
        return m.sqrt(inner)

    def trade_picnics(self, state: TradingState):
        """
        Stat Arb trade logic for pina coladas and coconut order pair
        Product 2 is always the product which needs to be more expensive. That is how the mean ratio is currently defined.
        If z-Score is positive that means current ratio is bigger than mean. We should then go long in product_1 and short in product_2
        If z-Score is negative that means current ratio is lower than mean. We should then go short in product_1 and long in product_2
        z_score_acutal is ALWAYS closer to 0 than z_score_mid.
        """
        product_basket_orders: list[Order] = []
        product_dip_orders: list[Order] = []
        product_guitar_orders: list[Order] = []
        product_bread_orders: list[Order] = []
        
        # z_score_for_max_orders = 2
        # z_score_for_strategy_start = 0.7

        # spread_upper_signal = 0.11760762022715847
        # spread_lower_signal = -0.061506137078973636
        # max_vol_threshold = 0.0009
        
        product_etf_inventory_limit = 70
        product_dip_inventory_limit = 300
        product_guitar_inventory_limit = 70
        product_bread_inventory_limit = 150
        
        
        order_depth_basket: OrderDepth = state.order_depths['PICNIC_BASKET']
        order_depth_dip: OrderDepth = state.order_depths['DIP']
        order_depth_guitar: OrderDepth = state.order_depths['UKULELE']
        order_depth_bread: OrderDepth = state.order_depths['BAGUETTE']
        
        initial_position_basket = state.position.get('PICNIC_BASKET', 0)
        initial_position_dip = state.position.get('DIP', 0)
        initial_position_guitar = state.position.get('UKULULE', 0)
        initial_position_bread = state.position.get("BAGUEGE", 0)
# abs(desired_position_product_1 - initial_position_product_1
        #BASKET VOLUME AND PRICE INFO 
        best_bid_basket = max(order_depth_basket.buy_orders.keys())
        best_ask_basket = min(order_depth_basket.sell_orders.keys())
        best_bid_volume_basket = abs(list(order_depth_basket.buy_orders.values())[-1])
        best_bid_avail_units_basket = min(best_bid_volume_basket,70+initial_position_basket)
        best_ask_volume_basket= abs(list(order_depth_basket.sell_orders.values())[0])
        best_ask_avail_units_basket = min(best_ask_volume_basket,70-initial_position_basket)
        mid_price_basket = stat.fmean([best_bid_basket, best_ask_basket])

        #DIP VOLUME AND PRICE INFO 
        best_bid_dip = max(order_depth_dip.buy_orders.keys())
        best_ask_dip = min(order_depth_dip.sell_orders.keys())
        best_bid_volume_dip = abs(list(order_depth_dip.buy_orders.values())[-1])
        best_bid_avail_units_dip = min(best_bid_volume_dip,280+initial_position_dip)
        best_ask_volume_dip= abs(list(order_depth_dip.sell_orders.values())[0])
        best_ask_avail_units_dip = min(best_ask_volume_dip,280-initial_position_dip)
        mid_price_dip = stat.fmean([best_bid_dip, best_ask_dip])

        #GUITAR VOLUME AND PRICE INFO 
        best_bid_guitar = max(order_depth_guitar.buy_orders.keys())
        best_ask_guitar = min(order_depth_guitar.sell_orders.keys())
        best_bid_volume_guitar = abs(list(order_depth_guitar.buy_orders.values())[-1])
        best_bid_avail_units_guitar = min(best_bid_volume_guitar,70+initial_position_guitar)
        best_ask_volume_guitar= abs(list(order_depth_guitar.sell_orders.values())[0])
        best_ask_avail_units_guitar = min(best_ask_volume_guitar,70-initial_position_guitar)
        mid_price_guitar = stat.fmean([best_bid_guitar, best_ask_guitar])

        #BREAD VOLUME AND PRICE INFO 
        best_bid_bread = max(order_depth_bread.buy_orders.keys())
        best_ask_bread = min(order_depth_bread.sell_orders.keys())
        best_bid_volume_bread = abs(list(order_depth_bread.buy_orders.values())[-1])
        best_bid_avail_units_bread = min(best_bid_volume_bread,140+initial_position_bread)
        best_ask_volume_bread= abs(list(order_depth_bread.sell_orders.values())[0])
        best_ask_avail_units_bread = min(best_ask_volume_bread,140-initial_position_bread)
        mid_price_bread = stat.fmean([best_bid_bread, best_ask_bread])

        grouped_price_max = 74312.5
        grouped_price_min = 72995.5
        basket_price_max = 74807.5
        basket_price_min = 73335.5

        grouped_basket_price = (4*mid_price_dip) + (2*mid_price_bread) + mid_price_guitar
        grouped_basket_price = self.normalize_data(grouped_basket_price,grouped_price_max,grouped_price_min)
        basket_price = self.normalize_data(mid_price_basket,basket_price_max,basket_price_min)
        spread =grouped_basket_price - basket_price 

        spread_mean = 0.02805074157409242
        spread_len = 30000
        vol = self.calc_vol(spread,spread_mean,spread_len)

        upper_start = 0.11760762022715847
        lower_start = -0.061506137078973636
        # current_mid_ratio = mid_price_product_2 / mid_price_product_1
        # z_score_mid = (current_mid_ratio - mean_ratio) / stdev_ratio
        if  spread >= upper_start and vol < 0.0009:
            #short spread
            desired_position_basket =  70
            desired_position_dip = -280
            desired_position_guitar = -70
            desired_position_bread = -140 
        
        elif spread < lower_start and vol < 0.0009: 
            #long spread
            desired_position_basket =  -70
            desired_position_dip = 280
            desired_position_guitar = 70
            desired_position_bread = 140 
        else: 
            desired_position_basket =  0
            desired_position_dip = 0
            desired_position_guitar = 0
            desired_position_bread = 0

        

        if initial_position_basket  >= 0  and spread > 0:
            if initial_position_basket < desired_position_basket: 
                #FUll Filling the short spread 1, 4, 2, 1
                available_units = m.floor(min(best_ask_avail_units_basket, best_bid_avail_units_dip/4,best_bid_avail_units_bread/2,best_bid_avail_units_guitar))
                product_basket_orders.append(Order('PICNIC_BASKET', best_ask_basket,min(available_units,abs(desired_position_basket-initial_position_basket))))
                product_dip_orders.append(Order('DIP', best_bid_dip,-min(available_units*4,abs(desired_position_dip-initial_position_dip))))
                product_guitar_orders.append(Order('UKULELE', best_bid_guitar,-min(available_units*2,abs(desired_position_guitar-initial_position_guitar))))
                product_bread_orders.append(Order('BAGUETTE', best_bid_bread,-min(available_units,abs(desired_position_bread-initial_position_bread))))

        elif initial_position_basket > 0 and spread <= 0:
            # closing the short spread
            available_units = min(best_bid_avail_units_basket, best_ask_avail_units_dip/4,best_ask_avail_units_bread/2,best_ask_avail_units_guitar)
            product_basket_orders.append(Order('PICNIC_BASKET', best_bid_basket,-min(available_units,abs(desired_position_basket-initial_position_basket))))
            product_dip_orders.append(Order('DIP', best_ask_dip,min(available_units*4,abs(desired_position_dip-initial_position_dip))))
            product_guitar_orders.append(Order('UKULELE', best_ask_guitar,min(available_units,abs(desired_position_guitar-initial_position_guitar))))
            product_bread_orders.append(Order('BAGUETTE', best_ask_bread,min(available_units*2,abs(desired_position_bread-initial_position_bread))))
            
        elif initial_position_basket < 0 and spread >= 0: 
            #Close Long Spread 
            available_units = min(best_ask_avail_units_basket, best_bid_avail_units_dip/4,best_bid_avail_units_bread/2,best_bid_avail_units_guitar)
            product_basket_orders.append(Order('PICNIC_BASKET', best_ask_basket,min(available_units,abs(desired_position_basket-initial_position_basket))))
            product_dip_orders.append(Order('DIP', best_bid_dip,-min(available_units/4,abs(desired_position_dip-initial_position_dip))))
            product_guitar_orders.append(Order('UKULELE', best_bid_guitar,-min(available_units,abs(desired_position_guitar-initial_position_guitar))))
            product_bread_orders.append(Order('BAGUETTE', best_bid_bread,-min(available_units/2,abs(desired_position_bread-initial_position_bread))))
            
        elif initial_position_basket <= 0 and spread < 0 :
            #Go Long Position 
            available_units = min(best_bid_avail_units_basket, best_ask_avail_units_dip/4,best_ask_avail_units_bread/2,best_ask_avail_units_guitar)
            product_basket_orders.append(Order('PICNIC_BASKET', best_bid_basket,-min(available_units,abs(desired_position_basket-initial_position_basket))))
            product_dip_orders.append(Order('DIP', best_ask_dip,min(available_units*4,abs(desired_position_dip-initial_position_dip))))
            product_guitar_orders.append(Order('UKULELE', best_ask_guitar,min(available_units,abs(desired_position_guitar-initial_position_guitar))))
            product_bread_orders.append(Order('BAGUETTE', best_ask_bread,min(available_units/2,abs(desired_position_bread-initial_position_bread))))

        return product_basket_orders, product_dip_orders, product_guitar_orders,product_bread_orders
    
    def diving_gear_dolphins_trade_logic (self, state: TradingState, tradable_product: str, observed_product: str):
        """
        Trade logic to trade Diving Gear based on the Doplhin sightings reported
        """
        current_timestamp  = state.timestamp
        diving_gear_orders: list[Order] = []
        current_sightings = state.observations.get(observed_product, 0)
        last_sigthings = self.product_parameters[observed_product]['last_sightings']
        position_maximum = self.product_parameters[tradable_product]['inventory_limit']
        
        
        if tradable_product in state.own_trades:
            last_trade_timestamp = state.own_trades[tradable_product][0].timestamp
        else:
            last_trade_timestamp = 0
        
        
        time_since_last_trade = current_timestamp - last_trade_timestamp
        
        
        sighting_spike_initiating_position = 6
        
        
        order_depth_tradable_product: OrderDepth = state.order_depths[tradable_product]
        initial_position_tradable_product = state.position.get(tradable_product, 0)
        
        
        all_bids_tradable_product = list(reversed(list(order_depth_tradable_product.buy_orders.keys())))
        all_asks_tradable_product = list(order_depth_tradable_product.sell_orders.keys())
        bid_volume_tradable_product = list(reversed(list(order_depth_tradable_product.buy_orders.values())))
        ask_volume_tradable_product = [abs(x) for x in list(order_depth_tradable_product.sell_orders.values())]
        mid_price_tradable_product = stat.fmean([all_bids_tradable_product[0], all_asks_tradable_product[0]])
        
        if time_since_last_trade > 78000:
            self.product_parameters[tradable_product]['buy_sell_signal'] = 0
        
        if current_timestamp != 0:
            if last_sigthings != 0: 
                sightings_difference = current_sightings - last_sigthings
                if sightings_difference >= sighting_spike_initiating_position:
                    self.product_parameters[tradable_product]['buy_sell_signal'] = 1
                elif sightings_difference <= -sighting_spike_initiating_position:
                    self.product_parameters[tradable_product]['buy_sell_signal'] = -1
            else:
                self.product_parameters[observed_product]['last_sightings'] = current_sightings
            self.product_parameters[observed_product]['last_sightings'] = current_sightings
        else:
            self.product_parameters[observed_product]['last_sightings'] = current_sightings
        
        
        buy_sell_signal = self.product_parameters[tradable_product]['buy_sell_signal']
        
        
        if buy_sell_signal == 1 and initial_position_tradable_product < position_maximum:
            #buy more until maximum
            volume_needed = abs(position_maximum - initial_position_tradable_product)
            volume_filled = 0
            for idx, strike in enumerate(all_asks_tradable_product):
                volume = min(ask_volume_tradable_product[idx], (volume_needed - volume_filled))
                volume_filled += volume
                diving_gear_orders.append(Order(tradable_product, strike, volume))
        
        elif buy_sell_signal == 0 and initial_position_tradable_product > 0:
            #sell until 0 reached
            volume_needed = abs(initial_position_tradable_product)
            volume_filled = 0
            for idx, strike in enumerate(all_bids_tradable_product):
                volume = min(bid_volume_tradable_product[idx], (volume_needed - volume_filled))
                volume_filled += volume
                diving_gear_orders.append(Order(tradable_product, strike, - volume))
        
        elif buy_sell_signal == 0 and initial_position_tradable_product < 0:
            #buy until 0 reached
            volume_needed = abs(initial_position_tradable_product)
            volume_filled = 0
            for idx, strike in enumerate(all_asks_tradable_product):
                volume = min(ask_volume_tradable_product[idx], (volume_needed - volume_filled))
                volume_filled += volume
                diving_gear_orders.append(Order(tradable_product, strike, volume))
        
        elif buy_sell_signal == -1 and initial_position_tradable_product > - position_maximum:
            #sell until maximum
            volume_needed = abs(- position_maximum - initial_position_tradable_product)
            volume_filled = 0
            for idx, strike in enumerate(all_bids_tradable_product):
                volume = min(bid_volume_tradable_product[idx], (volume_needed - volume_filled))
                volume_filled += volume
                diving_gear_orders.append(Order(tradable_product, strike, - volume))
        
        
        
        return diving_gear_orders
    
    
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        #INITIALIZE THE OUTPUT DICT AS AN EMPTY DICT
        total_transmittable_orders = {}

        
        #MARKET MAKING
        for product in state.order_depths.keys():
            if product in ['PEARLS','BANANAS', 'BERRIES']:
                
                #EXECUTE THE TRADE LOGIC AND OUTPUTS ALL ORDERS + DATA NEEDED FOR VISUALIZATION
                module_1_orders, module_2_orders = self.pearls_bananas_berries_trade_logic(product, state)
                
                #ADDS ALL ORDERS TO BE TRANSMITTED TO THE EMPTY DICT
                total_transmittable_orders[product] = module_1_orders + module_2_orders
            
            
        #STATS ARBITRAGE
        if 'PINA_COLADAS' in state.order_depths.keys() and 'COCONUTS' in state.order_depths.keys():
            product_1_orders, product_2_orders = self.pina_coco_trade_logic(state, 'COCONUTS', 'PINA_COLADAS')
            
            total_transmittable_orders['COCONUTS'] = product_1_orders
            total_transmittable_orders['PINA_COLADAS'] = product_2_orders
        
        
        #ALL-IN WOMBO-COMBO
        if 'DIVING_GEAR' in state.order_depths.keys() and 'DOLPHIN_SIGHTINGS' in state.observations.keys():
            
            diving_gear_orders = self.diving_gear_dolphins_trade_logic(state, 'DIVING_GEAR', 'DOLPHIN_SIGHTINGS')
            
            total_transmittable_orders['DIVING_GEAR'] = diving_gear_orders

        if 'UKULELE' in state.order_depths.keys() and 'DIP' in state.order_depths.keys() and 'BAGUETTE' in state.order_depths.keys() and 'PICNIC_BASKET' in state.order_depths.keys():
            product_basket_orders, product_dip_orders, product_guitar_orders,product_bread_orders = self.trade_picnics(state)
            total_transmittable_orders['PICNIC_BASKET']  = product_basket_orders
            total_transmittable_orders['DIP']  = product_dip_orders
            total_transmittable_orders['UKULELE']  = product_guitar_orders
            total_transmittable_orders['BAGUETTE'] = product_bread_orders

        
        #RETURNS ALL ORDER DATA TO THE ENGINE
        return total_transmittable_orders