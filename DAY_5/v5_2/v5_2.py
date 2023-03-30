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
                                    'lower_inventory_limit': -20, 'upper_inventory_limit': 20,
                                    'long_trade': False, 'short_trade': False
                                    },
                                    
                                    'COCONUTS':{
                                    'inventory_limit': 555, 'fair_price' : 8000,
                                    'lower_inventory_limit': -600, 'upper_inventory_limit': 600
                                    },
                                    
                                    'PINA_COLADAS':{
                                    'inventory_limit': 296, 'fair_price' : 15000,
                                    'lower_inventory_limit': -300, 'upper_inventory_limit': 300,
                                    'directional_trade': False
                                    },
                                    
                                    'DIVING_GEAR':{
                                    'inventory_limit': 50, 'buy_sell_signal': 0,
                                    'mid_price_ema':[], 'ema_count': 0,
                                    'lower_inventory_limit': -50, 'upper_inventory_limit': 50
                                    },
                                    
                                    'BERRIES':{
                                    'inventory_limit': 250, 'fair_price' : 0,
                                    'lower_inventory_limit': -250, 'upper_inventory_limit': 250,
                                    'long_trade': False, 'short_trade': False
                                    },
                                    
                                    'DOLPHIN_SIGHTINGS':{
                                    'last_sightings': 0
                                    },
                                    
                                    'UKULELE':{
                                        'inventory_limit': 70
                                    },
                                    'BAGUETTE':{
                                        'inventory_limit': 140
                                    },
                                    'DIP':{
                                        'inventory_limit': 280
                                    },
                                    'PICNIC_BASKET':{
                                        'inventory_limit': 70
                                    }
                                    
                                    
                                }
        self.stat_arb_pair_parameters = {
            "COCONUTS_PINA_COLADAS":{'mean_ratio': 1.875, 'stdev_ratio': 0.00447052512964639, 'mean_ratio_backtest': 1.874649044228040, 'stdev_ratio_backtest': 0.0014590944891508,
                                    'coconuts_order_minimum': 15, 'pina_coladas_order_minimum': 8, 'trade_opportunities': 37},
            "UKULELE_BAGUETTE_DIP_PICNIC_BASKET":{'mean_ratio': 1.005, 'stdev_ratio': 0.0016906625300147206, 'picnic_basket_order_minimum': 1, 'baguette_order_minimum': 2, 
                                                    'dip_order_minimum': 4, 'ukulele_order_minimum': 1, 'trade_opportunities': 70
                
            }
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

    def adjust_bananas_limits(self,state,product):
        market_trades = state.market_trades.get(product,[])
        long = self.product_parameters[product]['long_trade'] 
        short = self.product_parameters[product]['short_trade'] 

        if len(market_trades) > 0:
            people_buying  = set([trade.buyer for trade in market_trades])
            people_selling  =set([trade.seller for trade in market_trades])
            if 'Olivia' in people_buying and long == False and short == False:
                self.product_parameters[product]['long_trade'] = True
                self.product_parameters[product]['short_trade'] = False
                self.product_parameters[product]['upper_inventory_limit'] = 20
                self.product_parameters[product]['lower_inventory_limit'] = 20
            elif 'Olivia' in people_selling and long == False and short == False:
                self.product_parameters[product]['long_trade'] = False
                self.product_parameters[product]['short_trade'] = True
                self.product_parameters[product]['upper_inventory_limit'] = -20
                self.product_parameters[product]['lower_inventory_limit'] = -20
            
            elif 'Olivia' in people_buying and long == False and short == True:
                self.product_parameters[product]['long_trade'] = False
                self.product_parameters[product]['short_trade'] = False
                self.product_parameters[product]['upper_inventory_limit'] = 20
                self.product_parameters[product]['lower_inventory_limit'] = -20
            
            elif 'Olivia' in people_selling and long == False and short == True:
                self.product_parameters[product]['long_trade'] = False
                self.product_parameters[product]['short_trade'] = False
                self.product_parameters[product]['upper_inventory_limit'] = 20
                self.product_parameters[product]['lower_inventory_limit'] = -20

            else:
                long = self.product_parameters[product]['long_trade'] 
                short = self.product_parameters[product]['short_trade']  
                if long == False and short == False:
                    self.product_parameters[product]['upper_inventory_limit'] = 20
                    self.product_parameters[product]['lower_inventory_limit'] = -20
    
    def calculate_available_buy_and_sell(self,state, product: str, inventory_limit: int, initial_inventory: int, buy_volume: int, sell_volume: int, timestamp: int):
        """
        Calculates the buy and sell orders still available taking the module 1 orders into account
        """
        
        if product == 'BERRIES':
            self.adjust_berry_limits(state,product, timestamp)
        #if product == 'BANANAS':
        #    self.adjust_bananas_limits(state,product)
        
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
    
    def adjust_berry_limits(self, state, product: str,timestamp: int):

        market_trades = state.market_trades.get(product,[])
        if len(market_trades):
            people_buying  = set([trade.buyer for trade in market_trades])
            people_selling  =set([trade.seller for trade in market_trades])
        else:
            people_buying  = []
            people_selling  = []

        position = state.position.get(product,0)
        
        timestamp = timestamp/100
        current_upper = self.product_parameters[product]['upper_inventory_limit']
        current_lower = self.product_parameters[product]['lower_inventory_limit']
        
        long = self.product_parameters[product]['long_trade']
        short = self.product_parameters[product]['short_trade'] 

        if 'Oliva' in people_buying and long == False and short == False:
            self.product_parameters[product]['long_trade'] = True
            self.product_parameters[product]['short_trade'] = False
            self.product_parameters[product]['upper_inventory_limit'] = 250
            self.product_parameters[product]['lower_inventory_limit'] = 250

        elif 'Oliva' in people_selling and long == False and short == False :
            self.product_parameters[product]['long_trade'] = False
            self.product_parameters[product]['short_trade'] = True
            self.product_parameters[product]['upper_inventory_limit'] = -250
            self.product_parameters[product]['lower_inventory_limit'] = -250

        elif 'Olivia' in people_selling and long == True and short == False: #close long
            self.product_parameters[product]['long_trade'] = False
            self.product_parameters[product]['short_trade'] = False
            self.product_parameters[product]['upper_inventory_limit'] = 250
            self.product_parameters[product]['lower_inventory_limit'] = -250

        elif 'Olivia' in people_buying and long == False and short == True: #close short
            self.product_parameters[product]['long_trade'] = False
            self.product_parameters[product]['short_trade'] = False
            self.product_parameters[product]['upper_inventory_limit'] = 250
            self.product_parameters[product]['lower_inventory_limit'] = -250

        if self.product_parameters[product]['long_trade'] == False and self.product_parameters[product]['short_trade'] == False:
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
            avail_buy_orders, avail_sell_orders = self.calculate_available_buy_and_sell(state,product, inventory_limit, initial_inventory, mod_1_buy_volume, mod_1_sell_volume, timestamp)
            
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
            avail_buy_orders, avail_sell_orders = self.calculate_available_buy_and_sell(state,product, inventory_limit, initial_inventory, 0, 0)
            
            sell_price = round(lob_average_buy * 1.005)
            
            ridiculous_sell_order.append(Order(product, sell_price, -avail_sell_orders))
            
            return ridiculous_sell_order
        
        elif not lob_buy_volume_total > 0 and lob_sell_volume_total > 0:
            initial_inventory = state.position.get(product, 0)
            ridiculous_buy_order = []
            avail_buy_orders, avail_sell_orders = self.calculate_available_buy_and_sell(state,product, inventory_limit, initial_inventory, 0, 0)
            
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
    
    def picnic_basket_trade_logic (self, state: TradingState, product_1: str, product_2: str, product_3: str, product_4: str):
        """
        Stat Arb logic for the picnic basket and corresponding products.
        """
        product_1_orders: list[Order] = []
        product_2_orders: list[Order] = []
        product_3_orders: list[Order] = []
        product_4_orders: list[Order] = []
        
        z_score_for_max_orders = 2
        z_score_for_strategy_start = 0.7
        
        
        pair_key = product_1+"_"+product_2+"_"+product_3+"_"+product_4
        
        
        mean_ratio = self.stat_arb_pair_parameters[pair_key]['mean_ratio']
        stdev_ratio = self.stat_arb_pair_parameters[pair_key]['stdev_ratio']
        
        
        product_1_order_multiplier = self.stat_arb_pair_parameters[pair_key]['ukulele_order_minimum']
        product_2_order_multiplier = self.stat_arb_pair_parameters[pair_key]['baguette_order_minimum']
        product_3_order_multiplier = self.stat_arb_pair_parameters[pair_key]['dip_order_minimum']
        product_4_order_multiplier = self.stat_arb_pair_parameters[pair_key]['picnic_basket_order_minimum']
        
        
        product_1_inventory_limit = self.product_parameters[product_1]['inventory_limit']
        product_2_inventory_limit = self.product_parameters[product_2]['inventory_limit']
        product_3_inventory_limit = self.product_parameters[product_3]['inventory_limit']
        product_4_inventory_limit = self.product_parameters[product_4]['inventory_limit']
        
        
        trade_opportunities = self.stat_arb_pair_parameters[pair_key]['trade_opportunities']
        
        
        product_1_max_orders = product_1_order_multiplier * trade_opportunities
        product_2_max_orders = product_2_order_multiplier * trade_opportunities
        product_3_max_orders = product_3_order_multiplier * trade_opportunities
        product_4_max_orders = product_4_order_multiplier * trade_opportunities
        
        
        order_depth_product_1: OrderDepth = state.order_depths[product_1]
        order_depth_product_2: OrderDepth = state.order_depths[product_2]
        order_depth_product_3: OrderDepth = state.order_depths[product_3]
        order_depth_product_4: OrderDepth = state.order_depths[product_4]
        
        
        initial_position_product_1 = state.position.get(product_1, 0)
        initial_position_product_2 = state.position.get(product_2, 0)
        initial_position_product_3 = state.position.get(product_3, 0)
        initial_position_product_4 = state.position.get(product_4, 0)
        
        
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
        
        best_bid_product_3 = max(order_depth_product_3.buy_orders.keys())
        best_ask_product_3 = min(order_depth_product_3.sell_orders.keys())
        best_bid_volume_product_3 = abs(list(order_depth_product_3.buy_orders.values())[-1])
        best_bid_avail_units_product_3 = int(best_bid_volume_product_3 / product_3_order_multiplier)
        best_ask_volume_product_3 = abs(list(order_depth_product_3.sell_orders.values())[0])
        best_ask_avail_units_product_3 = int(best_ask_volume_product_3 /  product_3_order_multiplier)
        mid_price_product_3 = stat.fmean([best_bid_product_3, best_ask_product_3])
        
        best_bid_product_4 = max(order_depth_product_4.buy_orders.keys())
        best_ask_product_4 = min(order_depth_product_4.sell_orders.keys())
        best_bid_volume_product_4 = abs(list(order_depth_product_4.buy_orders.values())[-1])
        best_bid_avail_units_product_4 = int(best_bid_volume_product_4 / product_4_order_multiplier)
        best_ask_volume_product_4 = abs(list(order_depth_product_4.sell_orders.values())[0])
        best_ask_avail_units_product_4 = int(best_ask_volume_product_4 /  product_4_order_multiplier)
        mid_price_product_4 = stat.fmean([best_bid_product_4, best_ask_product_4])
        
        
        current_mid_ratio = mid_price_product_4 / (mid_price_product_1 + (2*mid_price_product_2) + (4*mid_price_product_3))
        
        
        z_score_mid = (current_mid_ratio - mean_ratio) / stdev_ratio
        
        
        if z_score_mid > z_score_for_strategy_start:
            
            current_ratio = best_bid_product_4/ (best_ask_product_1 + (2*best_ask_product_2) + (4*best_ask_product_3))
            z_score_actual = (current_ratio - mean_ratio) / stdev_ratio
            
            if z_score_actual > z_score_for_strategy_start :
                desired_position_product_1 = min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_1_order_multiplier), product_1_max_orders)
                desired_position_product_2 = min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_2_order_multiplier), product_2_max_orders)
                desired_position_product_3 = min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_3_order_multiplier), product_3_max_orders)
                desired_position_product_4 = -min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_4_order_multiplier), product_4_max_orders)
                
                if desired_position_product_1 >= product_1_inventory_limit:
                    desired_position_product_1 = product_1_inventory_limit
                    desired_position_product_2 = product_2_inventory_limit
                    desired_position_product_3 = product_3_inventory_limit
                    desired_position_product_4 = - product_4_inventory_limit
            else:
                desired_position_product_1 = 0
                desired_position_product_2 = 0
                desired_position_product_3 = 0
                desired_position_product_4 = 0
            
        elif z_score_mid < - z_score_for_strategy_start:
            current_ratio = best_ask_product_4/(best_bid_product_1 + (2*best_bid_product_2) + (4*best_bid_product_3))
            z_score_actual = (current_ratio - mean_ratio) / stdev_ratio
            
            if z_score_actual < - z_score_for_strategy_start:
                desired_position_product_1 = min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_1_order_multiplier), product_1_max_orders)
                desired_position_product_2 = min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_2_order_multiplier), product_2_max_orders)
                desired_position_product_3 = min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_3_order_multiplier), product_3_max_orders)
                desired_position_product_4 = -min((round((z_score_actual / (z_score_for_max_orders - z_score_for_strategy_start)) * trade_opportunities) * product_4_order_multiplier), product_4_max_orders)
                
                if desired_position_product_4 >= product_4_inventory_limit:
                    desired_position_product_1 = - product_1_inventory_limit
                    desired_position_product_2 = - product_2_inventory_limit
                    desired_position_product_3 = - product_3_inventory_limit
                    desired_position_product_4 = product_4_inventory_limit
                    

                #print(z_score_mid, z_score_actual)
            else:
                desired_position_product_1 = 0
                desired_position_product_2 = 0
                desired_position_product_3 = 0
                desired_position_product_4 = 0
        else:
            desired_position_product_1 = 0
            desired_position_product_2 = 0
            desired_position_product_3 = 0
            desired_position_product_4 = 0
        
        
        if initial_position_product_1 >= 0 and z_score_mid > 0: 
            if initial_position_product_1 < desired_position_product_1:
                # Add more, long 1,2,3 short 4
                available_units = min(best_ask_avail_units_product_1, best_ask_avail_units_product_2, best_ask_avail_units_product_3, best_bid_avail_units_product_4)
                product_1_orders.append(Order(product_1, best_ask_product_1, min((available_units * product_1_order_multiplier), abs(desired_position_product_1 - initial_position_product_1))))
                product_2_orders.append(Order(product_2, best_ask_product_2, min((available_units * product_2_order_multiplier), abs(desired_position_product_2 - initial_position_product_2))))
                product_3_orders.append(Order(product_3, best_ask_product_3, min((available_units * product_3_order_multiplier), abs(desired_position_product_3 - initial_position_product_3))))
                product_4_orders.append(Order(product_4, best_bid_product_4, -min((available_units * product_4_order_multiplier), abs(desired_position_product_4 - initial_position_product_4))))
                
            
        elif initial_position_product_1 > 0 and z_score_mid <= 0:
            # Neutralize everything we have
            available_units = min(best_bid_avail_units_product_1, best_bid_avail_units_product_2, best_bid_avail_units_product_3, best_ask_avail_units_product_4)
            product_1_orders.append(Order(product_1, best_bid_product_1, - min((available_units * product_1_order_multiplier), abs(desired_position_product_1 - initial_position_product_1))))
            product_2_orders.append(Order(product_2, best_bid_product_2, - min((available_units * product_2_order_multiplier), abs(desired_position_product_2 - initial_position_product_2))))
            product_3_orders.append(Order(product_3, best_bid_product_3, - min((available_units * product_3_order_multiplier), abs(desired_position_product_3 - initial_position_product_3))))
            product_4_orders.append(Order(product_4, best_ask_product_4, min((available_units * product_4_order_multiplier), abs(desired_position_product_4 - initial_position_product_4))))
        
        
        elif initial_position_product_1 < 0 and z_score_mid >= 0: 
            # Neutralize everything we have
            available_units = min(best_ask_avail_units_product_1, best_ask_avail_units_product_2, best_ask_avail_units_product_3, best_bid_avail_units_product_4)
            product_1_orders.append(Order(product_1, best_ask_product_1, min((available_units * product_1_order_multiplier), abs(desired_position_product_1 - initial_position_product_1))))
            product_2_orders.append(Order(product_2, best_ask_product_2, min((available_units * product_2_order_multiplier), abs(desired_position_product_2 - initial_position_product_2))))
            product_3_orders.append(Order(product_3, best_ask_product_3, min((available_units * product_3_order_multiplier), abs(desired_position_product_3 - initial_position_product_3))))
            product_4_orders.append(Order(product_4, best_bid_product_4, -min((available_units * product_4_order_multiplier), abs(desired_position_product_4 - initial_position_product_4))))
            
            
        elif initial_position_product_1 <= 0 and z_score_mid < 0:
            if initial_position_product_1 > desired_position_product_1:
                #add more, short 1,2,3 long 4
                available_units = min(best_bid_avail_units_product_1, best_bid_avail_units_product_2, best_bid_avail_units_product_3, best_ask_avail_units_product_4)
                product_1_orders.append(Order(product_1, best_bid_product_1, - min((available_units * product_1_order_multiplier), abs(desired_position_product_1 - initial_position_product_1))))
                product_2_orders.append(Order(product_2, best_bid_product_2, - min((available_units * product_2_order_multiplier), abs(desired_position_product_2 - initial_position_product_2))))
                product_3_orders.append(Order(product_3, best_bid_product_3, - min((available_units * product_3_order_multiplier), abs(desired_position_product_3 - initial_position_product_3))))
                product_4_orders.append(Order(product_4, best_ask_product_4, min((available_units * product_4_order_multiplier), abs(desired_position_product_4 - initial_position_product_4))))
        
        
        return product_1_orders, product_2_orders, product_3_orders, product_4_orders
    
    
    
    
    
    
    
    
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
            
            ukulele_orders, baguette_orders, dip_orders, picnic_basket_orders = self.picnic_basket_trade_logic(state, 'UKULELE', 'BAGUETTE', 'DIP', 'PICNIC_BASKET')
            
            total_transmittable_orders['PICNIC_BASKET']  = picnic_basket_orders
            total_transmittable_orders['DIP']  = dip_orders
            total_transmittable_orders['UKULELE']  = ukulele_orders
            total_transmittable_orders['BAGUETTE'] = baguette_orders
        
        
        
        #RETURNS ALL ORDER DATA TO THE ENGINE
        return total_transmittable_orders