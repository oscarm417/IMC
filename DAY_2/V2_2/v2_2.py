from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import math as m
import statistics as stat
from collections import deque
from collections import Counter


class portfolio:
    def __init__(self):
        self.inventory = 0
        self.previous_trades = set()
        self.open_trades = deque()

    def convertToNumber (self,s):
        return int.from_bytes(s.encode(), 'little')

    def convertFromNumber (self,n):
        return n.to_bytes(m.ceil(n.bit_length() / 8), 'little').decode()
    
    def add_trade(self,list_of_trades):
        #checking for duplicate trades 
        trade_str = dict(Counter([str(i) for i in list_of_trades]))
        trade_string_object = {str(i):i for i in list_of_trades}
        for trade_str,c in trade_str.items():
            temp_ob = trade_string_object[trade_str]
            temp_ob.quantity = temp_ob.quantity*c
            trade_string_object[trade_str] = temp_ob
        list_of_trades = [v for k,v in trade_string_object.items()]

        for trade in list_of_trades:
            trade.quantity = trade.quantity if (trade.buyer =="SUBMISSION") else -trade.quantity
            unique_trade_number = self.convertToNumber(str(trade))
            if unique_trade_number not in self.previous_trades:
                self.previous_trades.add(unique_trade_number)
                if self.inventory == 0: 
                    #if inventory zero just add the trade 
                    self.open_trades.append(trade)
                    self.inventory += trade.quantity
                else:
                    #if inventory in direction of trade
                    if (trade.quantity > 0 and self.inventory > 0) or (trade.quantity < 0 and self.inventory < 0):
                        self.open_trades.append(trade)
                        self.inventory += trade.quantity
                    else: #if inventory in opposit direction trade
                        self.inventory += trade.quantity
                        while trade.quantity != 0 and  len(self.open_trades) != 0 :
                            currTrade = self.open_trades.popleft()
                            if abs(currTrade.quantity) > abs(trade.quantity):
                                currTrade.quantity  = currTrade.quantity   + trade.quantity
                                trade.quantity = 0 
                                self.open_trades.appendleft(currTrade)
                            elif abs(currTrade.quantity) < abs(trade.quantity):
                                trade.quantity += currTrade.quantity
                            elif abs(currTrade.quantity) == abs(trade.quantity):
                                trade.quantity = 0
                        if trade.quantity != 0:
                            self.open_trades.append(trade)
                
        
    def update_inventory(self):
        if len(self.open_trades) > 0:
            self.inventory = sum([i.quantity for i in self.open_trades])

    def get_average_holding_price(self):
        if self.inventory != 0 :
            avg_price = sum([(trade.quantity/self.inventory)*trade.price for trade in self.open_trades ])
            return avg_price
        else:
            return "No Positions"
    
    def __str__(self) -> str:
        return f"inventory: {self.inventory}\nAverage Holding Price {str(self.get_average_holding_price())}\nCurrent Trades: {[str(i)for i in self.open_trades]}"
    def __repr__(self) -> str:
        return f"inventory: {self.inventory}\nAverage Holding Price {str(self.get_average_holding_price())}\nCurrent Trades: {[str(i)for i in self.open_trades]}"


class Trader:

    def __init__(self):
        self.product_parameters = {'PEARLS':{
                                    'inventory_limit': 20, 'fair_price' : 10000,
                                    'smart_price_history':[], 'smart_price_52_ema':[],
                                    'smart_price_24_ema': [], 'smart_price_macd':[], 'smart_price_macd_signal_line': [],
                                    'macd_buy_sell_signal':[], 'percentage_change_history':[], 'perc_stdev_history':[],
                                    'lower_inventory_limit': -20, 'upper_inventory_limit': 20,
                                    'portfolio': portfolio()},

                                    'BANANAS':{
                                    'inventory_limit': 20, 'fair_price' : 5000,
                                    'smart_price_history':[], 'smart_price_52_ema':[],
                                    'smart_price_24_ema': [], 'smart_price_macd':[], 'smart_price_macd_signal_line': [],
                                    'macd_buy_sell_signal':[], 'percentage_change_history':[], 'perc_stdev_history':[],
                                    'lower_inventory_limit': -15, 'upper_inventory_limit': 15,
                                    'portfolio': portfolio()},
                                    
                                    'COCONUTS':{
                                    'inventory_limit': 600, 'fair_price' : 8000,
                                    'smart_price_history':[], 'smart_price_52_ema':[],
                                    'smart_price_24_ema': [], 'smart_price_macd':[], 'smart_price_macd_signal_line': [],
                                    'macd_buy_sell_signal':[], 'percentage_change_history':[], 'perc_stdev_history':[],
                                    'lower_inventory_limit': -600, 'upper_inventory_limit': 600,
                                    'portfolio': portfolio()},
                                    
                                    'PINA_COLADAS':{
                                    'inventory_limit': 300, 'fair_price' : 15000,
                                    'smart_price_history':[], 'smart_price_52_ema':[],
                                    'smart_price_24_ema': [], 'smart_price_macd':[], 'smart_price_macd_signal_line': [],
                                    'macd_buy_sell_signal':[], 'percentage_change_history':[], 'perc_stdev_history':[],
                                    'lower_inventory_limit': -300, 'upper_inventory_limit': 300,
                                    'portfolio': portfolio()}
                                }
        self.arb_pairs_parameters = {
            "COCONUTS_PINA_COLADAS":{'ratio': 1.5512024480504607,'mean':2593.3223399315643,'std':30.53152286091472,'side': 0 ,'position1':0,'position2':0}
        }
        self.look_back_period = 52 #use float('inf') if you dont want this used
    
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
            if strike < new_ask:
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
                sell_volume = lob_buy_volume_per_strike[lob_buy_strikes.index(strike)]
                if abs(initial_inventory - sell_volume -sell_volume_total) <= inventory_limit:
                    new_orders.append(Order(product, strike, -sell_volume))
                    sell_volume_total += sell_volume
                else:
                    sell_volume = abs(initial_inventory + inventory_limit - sell_volume_total)
                    new_orders.append(Order(product, strike, -sell_volume))
                    sell_volume_total += sell_volume
                    break
        
        return (new_orders, buy_volume_total, sell_volume_total)

    def module_2_market_maker(self, smart_price: float, product: str, smart_price_bid: int, smart_price_ask: int, avail_buy_orders: int, avail_sell_orders: int):
        """
        Module for Market Making. This takes the bid/ask of the smart price and places orders at them.
        """
        new_orders: list[Order] = []
        
        new_orders.append(Order(product, (smart_price_bid), avail_buy_orders))
        new_orders.append(Order(product, (smart_price_ask), -avail_sell_orders))
        
        return (new_orders)
    
    # def module_3_sell_at_market_if_profit(self, avail_buy_orders:int, avail_sell_orders:int, smart_price: float, product: str, smart_price_bid: int, smart_price_ask, bid_price_1, ask_price_1,inventory):
    #     """
    #     If we are max short and we currently have a profit if we buy at (ask)market then take the offer
    #     if we are max long and we currently have a profit if we sell at (bid)market then take the offer
    #     """
    #     #IN CASE STATE GETS RESET THEN DONT TRADE AS CALCULATION WILL BE OFF
    #     if inventory == self.product_paramters[product]['portfolio'].position:
    #         new_orders: list[Order] = []
    #         average_holding_price = self.product_parameters[product]['portfolio'].get_average_holding_price()
    #         #IF MAX SHORT
    #         if inventory == -self.product_parameters[product]['inventory_limit'] and average_holding_price > ask_price_1:
    #             price_to_buy = max(smart_price_ask,ask_price_1)
    #             new_orders.append(Order(product,(ask_price_1), avail_buy_orders))
    #             avail_buy_orders = 0 
    #         #IF MAX LONG
    #         elif inventory == self.product_parameters[product]['inventory_limit'] and average_holding_price > bid_price_1:
    #             price_to_sell = max(smart_price_bid,bid_price_1)
    #             new_orders.append(Order(product,(bid_price_1), -avail_sell_orders))
    #             avail_sell_orders
    #     return new_orders, 
    
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
        
        
        if product == "PEARLS":
            if smart_price_bid > self.product_parameters[product]['fair_price']:
                smart_price_bid = self.product_parameters[product]['fair_price']
            elif smart_price_ask < self.product_parameters[product]['fair_price']:
                smart_price_ask = self.product_parameters[product]['fair_price']
        
        
        
        return smart_price_bid, smart_price_ask
    
    def calculate_smart_price(self, lob_average_buy: float, lob_average_sell: float, lob_buy_quantity: int, lob_sell_quantity: int) -> float:
        """
        Calculates the "Smart Price" described in "Machine Learning for Market Microstructure and High Frequency Trading" - Michael Kearns
        """
        smart_price = ((lob_average_buy *  lob_sell_quantity) + (lob_average_sell * lob_buy_quantity) ) / (lob_buy_quantity + lob_sell_quantity)
        
        return smart_price
    
    def save_price_data_and_vol(self, product: str, smart_price: float, own_trades,inventory):
        
        self.product_parameters[product]['smart_price_history'].append(smart_price)
        if own_trades != 0:
            self.product_parameters[product]['portfolio'].add_trade(own_trades)
            self.product_parameters[product]['portfolio'].update_inventory()

        if len(self.product_parameters[product]['smart_price_history']) > 1 :
            if len(self.product_parameters[product]['smart_price_history']) > self.look_back_period:
                del self.product_parameters[product]['smart_price_history'][0]
                del self.product_parameters[product]['percentage_change_history'][0]
                del self.product_parameters[product]['perc_stdev_history'][0]
                del self.product_parameters[product]['smart_price_52_ema'][0]
                del self.product_parameters[product]['smart_price_24_ema'][0]
                del self.product_parameters[product]['smart_price_macd'][0]
                del self.product_parameters[product]['smart_price_macd_signal_line'][0]
                del self.product_parameters[product]['macd_buy_sell_signal'][0]
                
            
            percentage_change = m.log(self.product_parameters[product]['smart_price_history'][-1] / self.product_parameters[product]['smart_price_history'][-2])
            self.product_parameters[product]['percentage_change_history'].append(percentage_change)
            
            perc_standard_deviation = stat.stdev([x for x in self.product_parameters[product]['percentage_change_history']])
            self.product_parameters[product]['perc_stdev_history'].append(perc_standard_deviation)
            
            k_52 = 2 / (min(len(self.product_parameters[product]['smart_price_history']), 52) + 1)
            exp_moving_ave_52 = (smart_price * k_52) + self.product_parameters[product]['smart_price_52_ema'][-1] * (1 - k_52)
            self.product_parameters[product]['smart_price_52_ema'].append(exp_moving_ave_52)
            
            k_24 = 2 / (min(len(self.product_parameters[product]['smart_price_history']), 24) + 1)
            exp_moving_ave_24 = (smart_price * k_24) + self.product_parameters[product]['smart_price_24_ema'][-1] * (1 - k_24)
            self.product_parameters[product]['smart_price_24_ema'].append(exp_moving_ave_24)
            
            MACD = self.product_parameters[product]['smart_price_24_ema'][-1] - self.product_parameters[product]['smart_price_52_ema'][-1]
            self.product_parameters[product]['smart_price_macd'].append(MACD)
            
            k_signal = 2 / (min(len(self.product_parameters[product]['smart_price_history']), 18) + 1)
            macd_signal_line = (MACD * k_signal) + self.product_parameters[product]['smart_price_macd_signal_line'][-1] * (1 - k_signal)
            self.product_parameters[product]['smart_price_macd_signal_line'].append(macd_signal_line)
            
            macd_buy_sell_signal = MACD - macd_signal_line
            self.product_parameters[product]['macd_buy_sell_signal'].append(macd_buy_sell_signal)
            
            #if product == "PEARLS":
            #    print(smart_price, exp_moving_ave_52, exp_moving_ave_24, MACD, macd_signal_line, macd_buy_sell_signal)
            
            
        elif len(self.product_parameters[product]['smart_price_history']) <= 1 :
            percentage_change = 0
            perc_standard_deviation = 0
            exp_moving_ave_52 = smart_price
            exp_moving_ave_24 = smart_price
            MACD = 0
            macd_signal_line = 0
            macd_buy_sell_signal = 0
            self.product_parameters[product]['percentage_change_history'].append(percentage_change)
            self.product_parameters[product]['perc_stdev_history'].append(perc_standard_deviation)
            self.product_parameters[product]['smart_price_52_ema'].append(exp_moving_ave_52)
            self.product_parameters[product]['smart_price_24_ema'].append(exp_moving_ave_24)
            self.product_parameters[product]['smart_price_macd'].append(MACD)
            self.product_parameters[product]['smart_price_macd_signal_line'].append(macd_signal_line)
            self.product_parameters[product]['macd_buy_sell_signal'].append(macd_buy_sell_signal)
            
            #if product == "PEARLS":
            #    print(smart_price, exp_moving_ave_52, exp_moving_ave_24, MACD, macd_signal_line, macd_buy_sell_signal)
    
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
        #lob_all_strikes_w_vol = lob_buy_strikes_w_vol + lob_sell_strikes_w_vol
        lob_average_buy = stat.fmean(lob_buy_strikes_w_vol)
        lob_average_sell = stat.fmean(lob_sell_strikes_w_vol)
        lob_buy_quantity = sum(lob_buy_volume_per_strike)
        lob_sell_quantity = sum(lob_sell_volume_per_strike) 
        best_ask = min(order_depth.sell_orders.keys())
        best_bid = max(order_depth.buy_orders.keys())
        mid_price = (best_ask + best_bid) / 2 
        #current_timestamp = state.timestamp

        return (lob_average_buy, lob_average_sell, lob_buy_quantity, lob_sell_quantity, lob_buy_strikes, 
                lob_sell_strikes, lob_buy_volume_per_strike, lob_sell_volume_per_strike, inventory_limit,
                lob_buy_volume_total, lob_sell_volume_total,best_bid,mid_price,best_ask)
    
    def calculate_available_buy_and_sell(self, product, inventory_limit, initial_inventory, mod_1_buy_volume, mod_1_sell_volume):
        """
        Calculates the buy and sell orders still available taking the module 1 orders into account
        """
        upper_bound = self.product_parameters[product]['upper_inventory_limit']
        lower_bound = self.product_parameters[product]['lower_inventory_limit']

        if min(upper_bound,inventory_limit) - initial_inventory - mod_1_buy_volume < 0:
            avail_buy_orders = 0
        else:
            avail_buy_orders = min(upper_bound,inventory_limit) - initial_inventory - mod_1_buy_volume
        if abs(max(lower_bound, -inventory_limit)) + initial_inventory - mod_1_sell_volume < 0:
            avail_sell_orders = 0
        else:
            avail_sell_orders = abs(max(lower_bound, -inventory_limit)) + initial_inventory - mod_1_sell_volume
        
        return round(avail_buy_orders), round(avail_sell_orders)
    
    def get_current_inventory(self, state, product, position_changes):
        """
        Just to clean up the trade_logic and make it more readable. This gets the current inventory
        """
        
        initial_inventory = state.position.get(product,0)  
        current_inventory = initial_inventory + position_changes

        return current_inventory
    
    def get_target_inventory(self, product):
        """
        Updates and returns the target inventory.
        """
        upper_bound = self.product_parameters[product]['upper_inventory_limit']
        lower_bound = self.product_parameters[product]['lower_inventory_limit']
        target_inventory = (upper_bound + lower_bound) / 2

        return target_inventory
    
    def output_data(self, product, state, mod1, mod2, best_bid, mid_price, best_ask, smart_price_bid, smart_price, smart_price_ask):
        """
        Print data that is needed for the visualization tool. 
        """
        print('\n')
        time_stamp = state.timestamp
        order_depth = state.order_depths[product]
        buy_orders = order_depth.buy_orders
        sell_orders = order_depth.sell_orders
        our_previous_filled = state.own_trades.get(product,0)
        market_previous_filled = state.market_trades.get(product,0)
        our_position = state.position.get(product,0)
        #best_bid ;{best_bid}|mid_price;{mid_price}|best_ask;{best_ask}|
        print(f"time;{time_stamp}|product;{product}|smart_price_bid;{smart_price_bid}|smart_price;{smart_price}|smart_price_ask;{smart_price_ask}|our_postion;{our_position}| buy_orders;{buy_orders}| sell_orders;{sell_orders}| our_previous_filled;{our_previous_filled}| market_previous_filled;{market_previous_filled}")
    
    def calc_allmighty_banana_trend_indicator(self, product):
        """
        Calculates the available bids/asks for module 2 to adjust in case of huge swings. Currently only works on BANANAS, hence the same
        """
        if product == "BANANAS":
            if len(self.product_parameters[product]['smart_price_52_ema']) >= self.look_back_period:
            
                current_macd = self.product_parameters[product]['smart_price_macd'][-1]
            
                self.product_parameters[product]['upper_inventory_limit'] = max(min(20, 20 + round((current_macd + 0.75) * 50)), 0)
                self.product_parameters[product]['lower_inventory_limit'] = min(max(-20, -20 + round((current_macd - 0.75) * 50)), 0)
            else:
                return
    
    def trade_logic(self, product:str, state: TradingState, market_variables: list):
        
        #UPDATES THE TARGET INVENTORY
        target_inventory = self.get_target_inventory(product)
        
        #UPDATE THE CURRENT INVENTORY
        current_inventory = self.get_current_inventory(state, product, 0)

        #OWN TRADES TO TRACK CURRENT AVERAGE HOLDING PRICE 
        own_trades = state.own_trades.get(product,0)

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
        lob_sell_volume_total,
        best_bid,
        mid_price,
        best_ask) = market_variables
        
        #CHECKS IF THERE ARE ORDERS ON BOTH SIDES OF THE ORDERBOOK
        if lob_buy_volume_total > 0 and lob_sell_volume_total > 0:
            
            #CALC SMART PRICE
            smart_price = self.calculate_smart_price(lob_average_buy, 
                                                    lob_average_sell, 
                                                    lob_buy_quantity, 
                                                    lob_sell_quantity)
            
            #GET PRICE DATA AND CALC VOL
            self.save_price_data_and_vol(product, smart_price,own_trades,current_inventory)
            
            #CALC BID/ASK
            smart_price_bid, smart_price_ask = self.calculate_bid_ask(product, smart_price, lob_buy_strikes, lob_sell_strikes)
            
            
            #MOD1 BUY AND SELL ORDERS 
            mod_1_new_orders, mod_1_buy_volume, mod_1_sell_volume = self.module_1_order_tapper(lob_buy_strikes, 
                                                                                                lob_sell_strikes, 
                                                                                                lob_buy_volume_per_strike, 
                                                                                                lob_sell_volume_per_strike, 
                                                                                                current_inventory, 
                                                                                                inventory_limit, 
                                                                                                product, 
                                                                                                smart_price_bid, 
                                                                                                smart_price_ask,
                                                                                                smart_price
                                                                                                )
            #ADJUST UPPER AND LOWER LIMIT
            self.calc_allmighty_banana_trend_indicator(product)
            
            #AVAILABLE BUYS AND SELLS AFTER MOD 1 ORDERS ARE EXECUTED
            avail_buy_orders, avail_sell_orders = self.calculate_available_buy_and_sell(product, inventory_limit, current_inventory, mod_1_buy_volume, mod_1_sell_volume)
            
            #CALCULATE CURRENT INVENTORY WITH MOD 1 ORDERS ALREADY INCLUDED
            current_inventory = self.get_current_inventory(state, product, (mod_1_buy_volume + mod_1_sell_volume))

            #SELL IF MAXED AND WE CAN PROFIT BY EXITING POSITION AT MARKET VALUE
            # self.module_3_sell_at_market_if_profit(avail_buy_orders,avail_sell_orders, smart_price, product, smart_price_bid, smart_price_ask, best_bid, best_ask ,state.position.get(product,0))


            
            #MOD2 BUY AND SELL ORDERS
            mod_2_new_orders = self.module_2_market_maker(smart_price,
                                                        product, 
                                                        smart_price_bid, 
                                                        smart_price_ask, 
                                                        avail_buy_orders, 
                                                        avail_sell_orders
                                                        )
            
            #RETURN ALL ORDER DATA AND THE DATA NEEDED FOR VISUALIZATION
            return mod_1_new_orders, mod_2_new_orders, best_bid,mid_price, best_ask, smart_price_bid, smart_price, smart_price_ask
        
        elif lob_buy_volume_total > 0 and not lob_sell_volume_total > 0:
            
            ridiculous_sell_order = []
            avail_buy_orders, avail_sell_orders = self.calculate_available_buy_and_sell(product, inventory_limit, current_inventory, 0, 0)
            
            sell_price = round(lob_average_buy * 1.005)
            
            ridiculous_sell_order.append(Order(product, sell_price, -avail_sell_orders))
            
            return ridiculous_sell_order
        
        elif not lob_buy_volume_total > 0 and lob_sell_volume_total > 0:
            
            ridiculous_buy_order = []
            avail_buy_orders, avail_sell_orders = self.calculate_available_buy_and_sell(product, inventory_limit, current_inventory, 0, 0)
            
            buy_price = round(lob_average_sell * 0.995)
            
            ridiculous_buy_order.append(Order(product, buy_price, avail_buy_orders))
            
            return ridiculous_buy_order
        

    def arb_calculate_allocations(self,state,product_1,product_2,ratio):
        """
        Returns 
        Long Spread: prod1_short,prod2_long
        Short Spread: prod1_long,prod2_short
        
        outvalue -> (Long Spread, Short Spread)        

        quantities are all positive, so dont forget to add "-" for shorts 
        """
        prod1_current_inventory = state.position.get(product_1,0)
        prod2_current_inventory = state.position.get(product_2,0)

        prod_1_avail_buys = self.product_parameters[product_1]['inventory_limit'] - prod1_current_inventory
        prod_1_avail_sells = -self.product_parameters[product_1]['inventory_limit'] - prod1_current_inventory
        prod_2_avail_buys = self.product_parameters[product_1]['inventory_limit'] - prod2_current_inventory
        prod_2_avail_sells = -self.product_parameters[product_1]['inventory_limit'] - prod2_current_inventory
        #BASED ON CURRENT AVAILABLE BUYS-SELLS-CALC MAXIMUM AMOUT OF PAIRS 

        #available to go long the spread
        prod_2_needed = abs(prod_1_avail_sells/ratio)
        prod_1_needed = prod_2_avail_buys*ratio
        if prod_2_needed > prod_2_avail_buys: 
            prod_2_to_trade_long = prod_2_avail_buys
            prod_1_to_trade_short = prod_1_needed
        elif prod_1_needed > abs(prod_1_avail_sells):
            prod_2_to_trade_long = prod_2_needed 
            prod_1_to_trade_short = abs(prod_1_avail_sells)
        else: #enought to make a perfect trade
            prod_2_to_trade_long = prod_2_needed
            prod_1_to_trade_short = prod_1_needed

        long_spread = (prod_1_to_trade_short,prod_2_to_trade_long)
        #allocations if shorting the spread
        prod_2_needed = prod_1_avail_buys/ratio
        prod_1_needed = abs(prod_2_avail_sells *ratio)
        if prod_2_needed > abs(prod_2_avail_sells): 
            prod_2_to_trade_short = abs(prod_2_avail_sells)
            prod_1_to_trade_long = prod_1_needed
        elif prod_1_needed > prod_1_avail_buys:
            prod_2_to_trade_short = prod_2_needed 
            prod_1_to_trade_long = prod_1_avail_buys
        else: #enought to make a perfect trade
            prod_2_to_trade_short = prod_2_needed
            prod_1_to_trade_long = prod_1_needed
        short_spread = (prod_1_to_trade_long,prod_2_to_trade_short)
        

        return long_spread,short_spread

    def generate_market_orders(self, product_1,ob_1,prod_1_needed):
        market_orders_to_send = []
        #orders closes to mid appear first in loop
        ob_1_buys = sorted([[k,v] for k,v in ob_1.buy_orders.items()], key = lambda x: x[0], reverse = True )
        ob_1_sells = sorted([[k,v] for k,v in ob_1.sell_orders.items()], key = lambda x: x[0], reverse = False )
        direction_1 = ob_1_sells if prod_1_needed > 0 else ( ob_1_buys if prod_1_needed < 0  else 0)
        if direction_1  != 0:
            for price,volume in direction_1:
                if prod_1_needed == 0:
                    break
                if volume >= abs(prod_1_needed):
                    #orders match size
                    market_orders_to_send.append(Order(product_1, price,prod_1_needed))
                    prod_1_needed == 0 
                elif volume < abs(prod_1_needed):
                    #needed volume is largeer so iterate through order book 
                    if prod_1_needed < 0 :
                        #need to sell
                        market_orders_to_send.append(Order(product_1, price,-volume))
                        prod_1_needed += volume 
                    else:
                        #need to buy 
                        market_orders_to_send.append(Order(product_1, price, volume))
                        prod_1_needed -= volume 
        return market_orders_to_send

    def zscore(self,val,avrg,stdv):
        return (val - avrg) / stdv

    def bid_mid_ask(self,ob):
        ob_1_buys = sorted([[k,v] for k,v in ob.buy_orders.items()], key = lambda x: x[0], reverse = True )
        ob_1_sells = sorted([[k,v] for k,v in ob.sell_orders.items()], key = lambda x: x[0], reverse = False )

        bid = ob_1_buys[0][0]
        ask = ob_1_sells[0][0]
        mid = stat.mean([bid,ask])
        return bid,mid,ask
    def arb_logic(self,state, product_1, product_2):
        """
        spread = product_2 - (product_1*ratio)
        long spread = buy - sell
        short spread = sell - long
        """
        prod1_orders_to_send = []
        prod2_orders_to_send = []
        pair_key = product_1+"_"+product_2
        ratio = self.arb_pairs_parameters[pair_key]['ratio']
        ob_1 = state.order_depths[product_1] 
        ob_2 = state.order_depths[product_2]
        
        product_1_bid,product_1_mid,product_1_ask = self.bid_mid_ask(ob_1)
        product_2_bid,product_2_mid,product_2_ask = self.bid_mid_ask(ob_1)

        spread = product_2_mid - (ratio*product_1_mid)
        side = self.arb_pairs_parameters[pair_key]['side']
        signal = self.zscore(spread,self.arb_pairs_parameters[pair_key]['mean'],self.arb_pairs_parameters[pair_key]['std'])

        
        #CURRENT INVENTORY & TARGET INVENTORY
        prod_1_target_inventory  = self.arb_pairs_parameters[pair_key]['position1']
        prod_2_target_inventory =  self.arb_pairs_parameters[pair_key]['position2']
        prod1_current_inventory = state.position.get(product_1,0)
        prod2_current_inventory = state.position.get(product_2,0)
        print(f'side;{side}|signal;{signal}|spread;{spread}|product1_inventory;{prod1_current_inventory}|product2_inventory;{prod2_current_inventory}')

        #HOW MUCH TO BUY AND SELLS
        #short_prodct_1,long_product_2        , long_product_1, short_product_2 
        long_spread_sell_buys, short_spread_buy_sells =  self.arb_calculate_allocations(state,product_1,product_2,ratio)

        #position open but not complete or #posiiton closed but not complete
        if side in [-1,1,0] and (prod_1_target_inventory != prod1_current_inventory or prod_2_target_inventory != prod2_current_inventory):
            prod_1_needed = prod_1_target_inventory - prod1_current_inventory
            prod_2_needed = prod_2_target_inventory - prod2_current_inventory
            prod1_orders = self.generate_market_orders(product_1, ob_1, prod_1_needed)
            prod2_orders = self.generate_market_orders(product_2, ob_2, prod_2_needed)
    
            prod1_orders_to_send += prod1_orders
            prod2_orders_to_send += prod2_orders
        else:
            # check to open/close spread trade 
            if signal <= -1 and side == 0: #Go long 
                side = 1
                #buy prod2
                #sell prod1
                prod_1_needed, prod_2_needed = long_spread_sell_buys
                prod1_orders = self.generate_market_orders(product_1, ob_1, -prod_1_needed)
                prod2_orders = self.generate_market_orders(product_2, ob_2, prod_2_needed)
                prod1_orders_to_send += prod1_orders
                prod2_orders_to_send += prod2_orders
            elif side >= 1 and side == 0: #Go Short 
                side = -1
                #sell prod2
                #buy prod1
                prod_1_needed, prod_2_needed = short_spread_buy_sells
                prod1_orders = self.generate_market_orders(product_1, ob_1, prod_1_needed)
                prod2_orders = self.generate_market_orders(product_2, ob_2, -prod_2_needed)
                prod1_orders_to_send += prod1_orders
                prod2_orders_to_send += prod2_orders

            elif (signal >= 0 and  side == 1) or (signal <= 0 and  side == -1):#Close Long Position
                side = 0 
                #sell prod2
                #buy prod1
                prod1_orders = self.generate_market_orders(product_1, ob_1, -prod1_current_inventory)
                prod2_orders = self.generate_market_orders(product_2, ob_2, -prod2_current_inventory)
                prod1_orders_to_send += prod1_orders
                prod2_orders_to_send += prod2_orders
        return prod1_orders_to_send,prod2_orders_to_send


    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        #INITIALIZE THE OUTPUT DICT AS AN EMPTY DICT
        total_transmittable_orders = {}

        
        #MARKET MAKING 
        #ITERATE OVER ALL AVAILABLE PRODUCTS IN THE ORDER DEPTHS
        for product in state.order_depths.keys():
            if product in ['PEARLS','BANANAS']:
                #DEFINE AND GET ALL ORDER BOOK DATA
                market_variables = self.initialize(state, product)
                
                #EXECUTE THE TRADE LOGIC AND OUTPUTS ALL ORDERS + DATA NEEDED FOR VISUALIZATION
                mod1, mod2, best_bid, mid_price, best_ask, smart_price_bid, smart_price, smart_price_ask = self.trade_logic(product, state, market_variables)
                
                #ADDS ALL ORDERS TO BE TRANSMITTED TO THE EMPTY DICT
                total_transmittable_orders[product] = mod1 + mod2
                
                #PRINTS THE OUTPUT DATA NEEDED FOR VISUALIZATION
                self.output_data(product, state, mod1, mod2, best_bid, mid_price, best_ask, smart_price_bid, smart_price, smart_price_ask) 
                
                
        
        
        #STATS ARBITRAGE
        #SPREAD = PRODUCT2 - PRODUCT1*B
        if 'PINA_COLADAS' in state.order_depths.keys() and 'COCONUTS' in state.order_depths.keys():
            o1, o2 = self.arb_logic(state, 'COCONUTS', 'PINA_COLADAS')
            total_transmittable_orders['COCONUTS'] = o1
            total_transmittable_orders['PINA_COLADAS'] = o2
        
        
        #RETURNS ALL ORDER DATA TO THE ENGINE
        return total_transmittable_orders