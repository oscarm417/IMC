from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import math as m
import statistics as stat

from collections import deque

class portfolio:
    def __init__(self):
        self.inventory = 0
        self.previous_trades = set()
        self.open_trades = deque()

    def add_trade(self,list_of_trades):
        for trade in list_of_trades:
            if str(trade) not in self.previous_trades:
                #adding string rep of trade to previous trade
                trade.quantity = trade.quantity if (trade.buyer =="SUBMISSION") else -trade.quantity
                #change quantity to negative  or positive on direction 
                self.previous_trades.add(str(trade))
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
                        if trade.quantity > 0:
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
        self.product_parameters = {'PEARLS':
                                   {'inventory_limit': 20, 'fair_price' : 10000,
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
                                    'portfolio': portfolio()
                                    }
                                }
        self.look_back_period = 52 # float('inf') #use float('inf') if you dont want this used
    
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
    
    def save_price_data_and_vol(self, product: str, smart_price: float):
        
        self.product_parameters[product]['smart_price_history'].append(smart_price)
        
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
        #print('\n')
        time_stamp = state.timestamp
        order_depth = state.order_depths[product]
        buy_orders = order_depth.buy_orders
        sell_orders = order_depth.sell_orders
        our_previous_filled = state.own_trades.get(product,0)
        market_previous_filled = state.market_trades.get(product,0)
        our_position = state.position.get(product,0)
        #best_bid ;{best_bid}|mid_price;{mid_price}|best_ask;{best_ask}|
        #print(f"time;{time_stamp}|product;{product}|smart_price_bid;{smart_price_bid}|smart_price;{smart_price}|smart_price_ask;{smart_price_ask}|our_postion;{our_position}| buy_orders;{buy_orders}| sell_orders;{sell_orders}| our_previous_filled;{our_previous_filled}| market_previous_filled;{market_previous_filled}")
    
    
    def calc_upper_lower_limit_based_on_trend(self, product):
        
        if len(self.product_parameters[product]['smart_price_52_ema']) >= self.look_back_period:
            if self.product_parameters[product]['macd_buy_sell_signal'][-1] >= 0.2:
                self.product_parameters[product]['upper_inventory_limit'] = 20
                self.product_parameters[product]['lower_inventory_limit'] = -15
            elif self.product_parameters[product]['macd_buy_sell_signal'][-1] <= -0.2:
                self.product_parameters[product]['upper_inventory_limit'] = 15
                self.product_parameters[product]['lower_inventory_limit'] = -20
            else:
                self.product_parameters[product]['upper_inventory_limit'] = self.product_parameters[product]['inventory_limit']
                self.product_parameters[product]['lower_inventory_limit'] = -self.product_parameters[product]['inventory_limit']
        
        

    
    
    def trade_logic(self, product:str, state: TradingState, market_variables: list):
        
        #UPDATES THE TARGET INVENTORY
        target_inventory = self.get_target_inventory(product)
        
        #UPDATE THE CURRENT INVENTORY
        current_inventory = self.get_current_inventory(state, product, 0)

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
            self.save_price_data_and_vol(product, smart_price)
            
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
            self.calc_upper_lower_limit_based_on_trend(product)
            
            #AVAILABLE BUYS AND SELLS AFTER MOD 1 ORDERS ARE EXECUTED
            avail_buy_orders, avail_sell_orders = self.calculate_available_buy_and_sell(product, inventory_limit, current_inventory, mod_1_buy_volume, mod_1_sell_volume)
            
            #CALCULATE CURRENT INVENTORY WITH MOD 1 ORDERS ALREADY INCLUDED
            current_inventory = self.get_current_inventory(state, product, (mod_1_buy_volume + mod_1_sell_volume))
            
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
        
        
    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        #INITIALIZE THE OUTPUT DICT AS AN EMPTY DICT
        total_transmittable_orders = {}

        #ITERATE OVER ALL AVAILABLE PRODUCTS IN THE ORDER DEPTHS
        for product in state.order_depths.keys():
            
            #DEFINE AND GET ALL ORDER BOOK DATA
            market_variables = self.initialize(state, product)
            
            #EXECUTE THE TRADE LOGIC AND OUTPUTS ALL ORDERS + DATA NEEDED FOR VISUALIZATION
            mod1, mod2, best_bid, mid_price, best_ask, smart_price_bid, smart_price, smart_price_ask = self.trade_logic(product, state, market_variables)
            
            #ADDS ALL ORDERS TO BE TRANSMITTED TO THE EMPTY DICT
            total_transmittable_orders[product] = mod1 + mod2
            
            #PRINTS THE OUTPUT DATA NEEDED FOR VISUALIZATION
            #self.output_data(product, state, mod1, mod2, best_bid, mid_price, best_ask, smart_price_bid, smart_price, smart_price_ask) 
        
        #RETURNS ALL ORDER DATA TO THE ENGINE
        return total_transmittable_orders