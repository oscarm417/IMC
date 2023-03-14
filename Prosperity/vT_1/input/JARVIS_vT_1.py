from typing import Dict, List
from datamodel import OrderDepth, TradingState, Order
import math as m
# import numpy as np
import statistics as stat

class Trader:

    def run(self, state: TradingState) -> Dict[str, List[Order]]:
        """
        Only method required. It takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        # Initialize the method output dict as an empty dict
        result = {}
        
        print(" ########## ", state.timestamp, " ########## ", state.timestamp)
        # Iterate over all the keys (the available products) contained in the order depths
        for product in state.order_depths.keys():

            # Check if the current product is the 'PEARLS' product, only then run the order logic
            if product == 'PEARLS':
                
                
                print("---", product)
                
                # Retrieve the Order Depth containing all the market BUY and SELL orders for PEARLS
                order_depth: OrderDepth = state.order_depths[product]
                
                if product in state.position:
                    position: TradingState = state.position[product]
                    print ("Position:", position)
                else:
                    print ("Position: 0")
                
                # Initialize the list of Orders to be sent as an empty list
                orders: list[Order] = []
                
                
                if len(order_depth.sell_orders) > 0 and len(order_depth.buy_orders) > 0:
                    
                    ob_buy_volume_total = m.fabs(m.fsum(order_depth.buy_orders.values()))       # Returns the absolute value of the aggregated buy order volumes of the orderbook (ob) --> positive
                    ob_sell_volume_total = m.fabs(m.fsum(order_depth.sell_orders.values()))     # Returns the absolute value of the aggregated sell order volumes of the orderbook (ob) --> positive
                    ob_buy_strikes = list(order_depth.buy_orders.keys())        # Returns a list of all unique strikes where at least 1 buy order has been submitted to the orderbook (ob) --> positive & low to high strikes
                    ob_sell_strikes = list(order_depth.sell_orders.keys())      # Returns a list of all unique strikes where at least 1 sell order has been submitted to the orderbook (ob) --> positive & low to high strikes
                    ob_buy_volume_per_strike = list(order_depth.buy_orders.values())        # Returns a list of volumes for the ob_buy_strikes --> positive & low to high strikes
                    ob_sell_volume_per_strike = [-x for x in list(order_depth.sell_orders.values())]        # Returns a list of volumes for the ob_sell_strikes --> positive & low to high strikes
                    ob_buy_strikes_w_vol = [ob_buy_strikes[ob_buy_volume_per_strike.index(x)] for x in ob_buy_volume_per_strike for i in range(x)]      # Returns a list of all buy strikes with the amount of strikes in the list given by their quantity in ob_buy_volume_per_strike
                    ob_sell_strikes_w_vol = [ob_sell_strikes[ob_sell_volume_per_strike.index(x)] for x in ob_sell_volume_per_strike for i in range(x)]      # Returns a list of all sell strikes with the amount of strikes in the list given by their quantity in ob_sell_volume_per_strike
                    ob_all_strikes_w_vol = ob_buy_strikes_w_vol + ob_sell_strikes_w_vol
                    
                    position_changes = 0
                    
                    MeaP = stat.fmean(ob_all_strikes_w_vol)     # Arithmetic Mean Price --> 812 Seashells
                    
                    '''
                    ### Results for permanent 1x bid and 1x ask order until at 20/-20 at which changed to either only ask or bid
                    WAP = (np.average(ob_sell_strikes, weights=ob_sell_volume_per_strike) + np.average(ob_buy_strikes, weights=ob_buy_volume_per_strike)) / 2   # Weighted Average Price --> 802 Seashells
                    GMP = stat.geometric_mean(ob_all_strikes_w_vol) # Geometric Mean Price --> 752 Seashells
                    HMP = stat.harmonic_mean(ob_all_strikes_w_vol)      # Harmonic Mean Price --> 752 Seashells
                    MGP = stat.median_grouped(ob_all_strikes_w_vol)     # Median Grouped Price --> -727 Seashells
                    MedP = stat.median(ob_all_strikes_w_vol)      # Median Price --> -108 Seashells

                    best_ask = min(order_depth.sell_orders.keys())
                    best_bid = max(order_depth.buy_orders.keys())
                    mid_price = (best_ask + best_bid) / 2       # Mid Price of lowest ask and highest bid --> -276 Seashells
                    '''
                    
                    
                    if isinstance(MeaP, float):
                        if MeaP.is_integer():
                            new_bid = int(MeaP - 1)
                            new_ask = int(MeaP + 1)
                        else:
                            new_bid = m.floor(MeaP)
                            new_ask = m.ceil(MeaP)
                    elif isinstance(MeaP, int):
                        new_bid = int(MeaP - 1)
                        new_ask = int(MeaP + 1)
                    
                    
                    
                    for strike in ob_sell_strikes:                                                                  #  
                        if strike < MeaP:                                                                           #
                            volume = ob_sell_volume_per_strike[ob_sell_strikes.index(strike)]                       #   Checks for SELL Orders below the MeaP
                            orders.append(Order(product, strike, volume))                                           #
                            print("BUY ", volume, "x ", product, " @ ", strike)                                     #
                            position_changes = position_changes + volume                                            #
                            #                                                                                        ###### Improved Result from 812 to 1540 Seashells
                    for strike in ob_buy_strikes:                                                                   #       1430 Seashells without anything else
                        if strike > MeaP:                                                                           #       2575.0596 Seashells without anything else, but also for BANANAS
                            volume = ob_buy_volume_per_strike[ob_buy_strikes.index(strike)]                         #   Checks for BUY Orders above the MeaP
                            orders.append(Order(product, strike, -volume))                                          #
                            print("SELL ", -volume, "x ", product, " @ ", strike)                                   #   !!! Wenn position_change != 0 , dann werden Orders geschickt über das Limit hinaus und dadurch werden alle Order gecancelt
                            position_changes = position_changes - volume                                            #   !!! Aufpassen und überprüfen, ob die Orders das Positionslimit übersteigen!
                    
                    
                    position = 0
                    if product in state.position:
                        position = state.position[product]
                    else:
                        position = 0
                        
                        
                    if (position + position_changes) == -20:                                                        #
                        orders.append(Order(product, (new_bid - 5), 10))                                            #
                        orders.append(Order(product, (new_bid - 4), 9))                                             #   Places Staircase of orders around MeaP with dynamic sizing of the position, depending on the inventory
                        orders.append(Order(product, (new_bid - 3), 8))                                             #   1744 Seashells without anything else
                        orders.append(Order(product, (new_bid - 2), 7))                                             #   2965.1191 Seashells without anything else, but also for BANANAS
                        orders.append(Order(product, (new_bid - 1), 6))                                             #   275 Seashells together with Module above, 577 Seashells with Module above but wider spread
                        print("Position2: ", position + position_changes)                                           # 
                        
                    elif (position + position_changes) == -19:
                        orders.append(Order(product, (new_bid - 5), 9))
                        orders.append(Order(product, (new_bid - 4), 9))
                        orders.append(Order(product, (new_bid - 3), 8))
                        orders.append(Order(product, (new_bid - 2), 7))
                        orders.append(Order(product, (new_bid - 1), 6))
                        orders.append(Order(product, (new_ask + 5), -1))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -18:
                        orders.append(Order(product, (new_bid - 5), 9))
                        orders.append(Order(product, (new_bid - 4), 8))
                        orders.append(Order(product, (new_bid - 3), 8))
                        orders.append(Order(product, (new_bid - 2), 7))
                        orders.append(Order(product, (new_bid - 1), 6))
                        orders.append(Order(product, (new_ask + 4), -1))
                        orders.append(Order(product, (new_ask + 5), -1))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -17:
                        orders.append(Order(product, (new_bid - 5), 9))
                        orders.append(Order(product, (new_bid - 4), 8))
                        orders.append(Order(product, (new_bid - 3), 7))
                        orders.append(Order(product, (new_bid - 2), 7))
                        orders.append(Order(product, (new_bid - 1), 6))
                        orders.append(Order(product, (new_ask + 3), -1))
                        orders.append(Order(product, (new_ask + 4), -1))
                        orders.append(Order(product, (new_ask + 5), -1))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -16:
                        orders.append(Order(product, (new_bid - 5), 9))
                        orders.append(Order(product, (new_bid - 4), 8))
                        orders.append(Order(product, (new_bid - 3), 7))
                        orders.append(Order(product, (new_bid - 2), 6))
                        orders.append(Order(product, (new_bid - 1), 6))
                        orders.append(Order(product, (new_ask + 2), -1))
                        orders.append(Order(product, (new_ask + 3), -1))
                        orders.append(Order(product, (new_ask + 4), -1))
                        orders.append(Order(product, (new_ask + 5), -1))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -15:
                        orders.append(Order(product, (new_bid - 5), 9))
                        orders.append(Order(product, (new_bid - 4), 8))
                        orders.append(Order(product, (new_bid - 3), 7))
                        orders.append(Order(product, (new_bid - 2), 6))
                        orders.append(Order(product, (new_bid - 1), 5))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -1))
                        orders.append(Order(product, (new_ask + 3), -1))
                        orders.append(Order(product, (new_ask + 4), -1))
                        orders.append(Order(product, (new_ask + 5), -1))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -14:
                        orders.append(Order(product, (new_bid - 5), 8))
                        orders.append(Order(product, (new_bid - 4), 8))
                        orders.append(Order(product, (new_bid - 3), 7))
                        orders.append(Order(product, (new_bid - 2), 6))
                        orders.append(Order(product, (new_bid - 1), 5))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -1))
                        orders.append(Order(product, (new_ask + 3), -1))
                        orders.append(Order(product, (new_ask + 4), -1))
                        orders.append(Order(product, (new_ask + 5), -2))
                        print("Position2: ", position + position_changes)
                        
                    elif (position + position_changes) == -13:
                        orders.append(Order(product, (new_bid - 5), 8))
                        orders.append(Order(product, (new_bid - 4), 7))
                        orders.append(Order(product, (new_bid - 3), 7))
                        orders.append(Order(product, (new_bid - 2), 6))
                        orders.append(Order(product, (new_bid - 1), 5))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -1))
                        orders.append(Order(product, (new_ask + 3), -1))
                        orders.append(Order(product, (new_ask + 4), -2))
                        orders.append(Order(product, (new_ask + 5), -2))
                        print("Position2: ", position + position_changes)
                        
                    elif (position + position_changes) == -12:
                        orders.append(Order(product, (new_bid - 5), 8))
                        orders.append(Order(product, (new_bid - 4), 7))
                        orders.append(Order(product, (new_bid - 3), 6))
                        orders.append(Order(product, (new_bid - 2), 6))
                        orders.append(Order(product, (new_bid - 1), 5))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -1))
                        orders.append(Order(product, (new_ask + 3), -1))
                        orders.append(Order(product, (new_ask + 4), -2))
                        orders.append(Order(product, (new_ask + 5), -3))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -11:
                        orders.append(Order(product, (new_bid - 5), 8))
                        orders.append(Order(product, (new_bid - 4), 7))
                        orders.append(Order(product, (new_bid - 3), 6))
                        orders.append(Order(product, (new_bid - 2), 5))
                        orders.append(Order(product, (new_bid - 1), 5))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -1))
                        orders.append(Order(product, (new_ask + 3), -1))
                        orders.append(Order(product, (new_ask + 4), -3))
                        orders.append(Order(product, (new_ask + 5), -3))
                        print("Position2: ", position + position_changes)
                        
                    elif (position + position_changes) == -10:
                        orders.append(Order(product, (new_bid - 5), 8))
                        orders.append(Order(product, (new_bid - 4), 7))
                        orders.append(Order(product, (new_bid - 3), 6))
                        orders.append(Order(product, (new_bid - 2), 5))
                        orders.append(Order(product, (new_bid - 1), 4))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -1))
                        orders.append(Order(product, (new_ask + 3), -2))
                        orders.append(Order(product, (new_ask + 4), -3))
                        orders.append(Order(product, (new_ask + 5), -3))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -9:
                        orders.append(Order(product, (new_bid - 5), 7))
                        orders.append(Order(product, (new_bid - 4), 7))
                        orders.append(Order(product, (new_bid - 3), 6))
                        orders.append(Order(product, (new_bid - 2), 5))
                        orders.append(Order(product, (new_bid - 1), 4))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -1))
                        orders.append(Order(product, (new_ask + 3), -2))
                        orders.append(Order(product, (new_ask + 4), -3))
                        orders.append(Order(product, (new_ask + 5), -4))
                        print("Position2: ", position + position_changes)
                        
                    elif (position + position_changes) == -8:
                        orders.append(Order(product, (new_bid - 5), 7))
                        orders.append(Order(product, (new_bid - 4), 6))
                        orders.append(Order(product, (new_bid - 3), 6))
                        orders.append(Order(product, (new_bid - 2), 5))
                        orders.append(Order(product, (new_bid - 1), 4))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -2))
                        orders.append(Order(product, (new_ask + 3), -2))
                        orders.append(Order(product, (new_ask + 4), -3))
                        orders.append(Order(product, (new_ask + 5), -4))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -7:
                        orders.append(Order(product, (new_bid - 5), 7))
                        orders.append(Order(product, (new_bid - 4), 6))
                        orders.append(Order(product, (new_bid - 3), 5))
                        orders.append(Order(product, (new_bid - 2), 5))
                        orders.append(Order(product, (new_bid - 1), 4))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -2))
                        orders.append(Order(product, (new_ask + 3), -3))
                        orders.append(Order(product, (new_ask + 4), -3))
                        orders.append(Order(product, (new_ask + 5), -4))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -6:
                        orders.append(Order(product, (new_bid - 5), 7))
                        orders.append(Order(product, (new_bid - 4), 6))
                        orders.append(Order(product, (new_bid - 3), 5))
                        orders.append(Order(product, (new_bid - 2), 4))
                        orders.append(Order(product, (new_bid - 1), 4))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -2))
                        orders.append(Order(product, (new_ask + 3), -3))
                        orders.append(Order(product, (new_ask + 4), -4))
                        orders.append(Order(product, (new_ask + 5), -4))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -5:
                        orders.append(Order(product, (new_bid - 5), 7))
                        orders.append(Order(product, (new_bid - 4), 6))
                        orders.append(Order(product, (new_bid - 3), 5))
                        orders.append(Order(product, (new_bid - 2), 4))
                        orders.append(Order(product, (new_bid - 1), 3))
                        orders.append(Order(product, (new_ask + 1), -1))
                        orders.append(Order(product, (new_ask + 2), -2))
                        orders.append(Order(product, (new_ask + 3), -3))
                        orders.append(Order(product, (new_ask + 4), -4))
                        orders.append(Order(product, (new_ask + 5), -5))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -4:
                        orders.append(Order(product, (new_bid - 5), 6))
                        orders.append(Order(product, (new_bid - 4), 6))
                        orders.append(Order(product, (new_bid - 3), 5))
                        orders.append(Order(product, (new_bid - 2), 4))
                        orders.append(Order(product, (new_bid - 1), 3))
                        orders.append(Order(product, (new_ask + 1), -2))
                        orders.append(Order(product, (new_ask + 2), -2))
                        orders.append(Order(product, (new_ask + 3), -3))
                        orders.append(Order(product, (new_ask + 4), -4))
                        orders.append(Order(product, (new_ask + 5), -5))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == -3:
                        orders.append(Order(product, (new_bid - 5), 6))
                        orders.append(Order(product, (new_bid - 4), 5))
                        orders.append(Order(product, (new_bid - 3), 5))
                        orders.append(Order(product, (new_bid - 2), 4))
                        orders.append(Order(product, (new_bid - 1), 3))
                        orders.append(Order(product, (new_ask + 1), -2))
                        orders.append(Order(product, (new_ask + 2), -3))
                        orders.append(Order(product, (new_ask + 3), -3))
                        orders.append(Order(product, (new_ask + 4), -4))
                        orders.append(Order(product, (new_ask + 5), -5))
                        print("Position2: ", position + position_changes)
                        
                    elif (position + position_changes) == -2:
                        orders.append(Order(product, (new_bid - 5), 6))
                        orders.append(Order(product, (new_bid - 4), 5))
                        orders.append(Order(product, (new_bid - 3), 4))
                        orders.append(Order(product, (new_bid - 2), 4))
                        orders.append(Order(product, (new_bid - 1), 3))
                        orders.append(Order(product, (new_ask + 1), -2))
                        orders.append(Order(product, (new_ask + 2), -3))
                        orders.append(Order(product, (new_ask + 3), -4))
                        orders.append(Order(product, (new_ask + 4), -4))
                        orders.append(Order(product, (new_ask + 5), -5))
                        print("Position2: ", position + position_changes)
                        
                    elif (position + position_changes) == -1:
                        orders.append(Order(product, (new_bid - 5), 6))
                        orders.append(Order(product, (new_bid - 4), 5))
                        orders.append(Order(product, (new_bid - 3), 4))
                        orders.append(Order(product, (new_bid - 2), 3))
                        orders.append(Order(product, (new_bid - 1), 3))
                        orders.append(Order(product, (new_ask + 1), -2))
                        orders.append(Order(product, (new_ask + 2), -3))
                        orders.append(Order(product, (new_ask + 3), -4))
                        orders.append(Order(product, (new_ask + 4), -5))
                        orders.append(Order(product, (new_ask + 5), -5))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 0:
                        orders.append(Order(product, (new_bid - 5), 6))
                        orders.append(Order(product, (new_bid - 4), 5))
                        orders.append(Order(product, (new_bid - 3), 4))
                        orders.append(Order(product, (new_bid - 2), 3))
                        orders.append(Order(product, (new_bid - 1), 2))
                        orders.append(Order(product, (new_ask + 1), -2))
                        orders.append(Order(product, (new_ask + 2), -3))
                        orders.append(Order(product, (new_ask + 3), -4))
                        orders.append(Order(product, (new_ask + 4), -5))
                        orders.append(Order(product, (new_ask + 5), -6))
                        print("Position2: ", position + position_changes)
                        
                    elif (position + position_changes) == 1:
                        orders.append(Order(product, (new_bid - 5), 5))
                        orders.append(Order(product, (new_bid - 4), 5))
                        orders.append(Order(product, (new_bid - 3), 4))
                        orders.append(Order(product, (new_bid - 2), 3))
                        orders.append(Order(product, (new_bid - 1), 2))
                        orders.append(Order(product, (new_ask + 1), -3))
                        orders.append(Order(product, (new_ask + 2), -3))
                        orders.append(Order(product, (new_ask + 3), -4))
                        orders.append(Order(product, (new_ask + 4), -5))
                        orders.append(Order(product, (new_ask + 5), -6))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 2:
                        orders.append(Order(product, (new_bid - 5), 5))
                        orders.append(Order(product, (new_bid - 4), 4))
                        orders.append(Order(product, (new_bid - 3), 4))
                        orders.append(Order(product, (new_bid - 2), 3))
                        orders.append(Order(product, (new_bid - 1), 2))
                        orders.append(Order(product, (new_ask + 1), -3))
                        orders.append(Order(product, (new_ask + 2), -4))
                        orders.append(Order(product, (new_ask + 3), -4))
                        orders.append(Order(product, (new_ask + 4), -5))
                        orders.append(Order(product, (new_ask + 5), -6))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 3:
                        orders.append(Order(product, (new_bid - 5), 5))
                        orders.append(Order(product, (new_bid - 4), 4))
                        orders.append(Order(product, (new_bid - 3), 3))
                        orders.append(Order(product, (new_bid - 2), 3))
                        orders.append(Order(product, (new_bid - 1), 2))
                        orders.append(Order(product, (new_ask + 1), -3))
                        orders.append(Order(product, (new_ask + 2), -4))
                        orders.append(Order(product, (new_ask + 3), -5))
                        orders.append(Order(product, (new_ask + 4), -5))
                        orders.append(Order(product, (new_ask + 5), -6))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 4:
                        orders.append(Order(product, (new_bid - 5), 5))
                        orders.append(Order(product, (new_bid - 4), 4))
                        orders.append(Order(product, (new_bid - 3), 3))
                        orders.append(Order(product, (new_bid - 2), 2))
                        orders.append(Order(product, (new_bid - 1), 2))
                        orders.append(Order(product, (new_ask + 1), -3))
                        orders.append(Order(product, (new_ask + 2), -4))
                        orders.append(Order(product, (new_ask + 3), -5))
                        orders.append(Order(product, (new_ask + 4), -6))
                        orders.append(Order(product, (new_ask + 5), -6))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 5:
                        orders.append(Order(product, (new_bid - 5), 5))
                        orders.append(Order(product, (new_bid - 4), 4))
                        orders.append(Order(product, (new_bid - 3), 3))
                        orders.append(Order(product, (new_bid - 2), 2))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -3))
                        orders.append(Order(product, (new_ask + 2), -4))
                        orders.append(Order(product, (new_ask + 3), -5))
                        orders.append(Order(product, (new_ask + 4), -6))
                        orders.append(Order(product, (new_ask + 5), -7))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 6:
                        orders.append(Order(product, (new_bid - 5), 4))
                        orders.append(Order(product, (new_bid - 4), 4))
                        orders.append(Order(product, (new_bid - 3), 3))
                        orders.append(Order(product, (new_bid - 2), 2))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -4))
                        orders.append(Order(product, (new_ask + 2), -4))
                        orders.append(Order(product, (new_ask + 3), -5))
                        orders.append(Order(product, (new_ask + 4), -6))
                        orders.append(Order(product, (new_ask + 5), -7))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 7:
                        orders.append(Order(product, (new_bid - 5), 4))
                        orders.append(Order(product, (new_bid - 4), 3))
                        orders.append(Order(product, (new_bid - 3), 3))
                        orders.append(Order(product, (new_bid - 2), 2))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -4))
                        orders.append(Order(product, (new_ask + 2), -5))
                        orders.append(Order(product, (new_ask + 3), -5))
                        orders.append(Order(product, (new_ask + 4), -6))
                        orders.append(Order(product, (new_ask + 5), -7))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 8:
                        orders.append(Order(product, (new_bid - 5), 4))
                        orders.append(Order(product, (new_bid - 4), 3))
                        orders.append(Order(product, (new_bid - 3), 2))
                        orders.append(Order(product, (new_bid - 2), 2))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -4))
                        orders.append(Order(product, (new_ask + 2), -5))
                        orders.append(Order(product, (new_ask + 3), -6))
                        orders.append(Order(product, (new_ask + 4), -6))
                        orders.append(Order(product, (new_ask + 5), -7))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 9:
                        orders.append(Order(product, (new_bid - 5), 4))
                        orders.append(Order(product, (new_bid - 4), 3))
                        orders.append(Order(product, (new_bid - 3), 2))
                        orders.append(Order(product, (new_bid - 2), 1))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -4))
                        orders.append(Order(product, (new_ask + 2), -5))
                        orders.append(Order(product, (new_ask + 3), -6))
                        orders.append(Order(product, (new_ask + 4), -7))
                        orders.append(Order(product, (new_ask + 5), -7))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 10:
                        orders.append(Order(product, (new_bid - 5), 3))
                        orders.append(Order(product, (new_bid - 4), 3))
                        orders.append(Order(product, (new_bid - 3), 2))
                        orders.append(Order(product, (new_bid - 2), 1))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -4))
                        orders.append(Order(product, (new_ask + 2), -5))
                        orders.append(Order(product, (new_ask + 3), -6))
                        orders.append(Order(product, (new_ask + 4), -7))
                        orders.append(Order(product, (new_ask + 5), -8))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 11:
                        orders.append(Order(product, (new_bid - 5), 3))
                        orders.append(Order(product, (new_bid - 4), 3))
                        orders.append(Order(product, (new_bid - 3), 1))
                        orders.append(Order(product, (new_bid - 2), 1))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -5))
                        orders.append(Order(product, (new_ask + 2), -5))
                        orders.append(Order(product, (new_ask + 3), -6))
                        orders.append(Order(product, (new_ask + 4), -7))
                        orders.append(Order(product, (new_ask + 5), -8))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 12:
                        orders.append(Order(product, (new_bid - 5), 3))
                        orders.append(Order(product, (new_bid - 4), 2))
                        orders.append(Order(product, (new_bid - 3), 1))
                        orders.append(Order(product, (new_bid - 2), 1))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -5))
                        orders.append(Order(product, (new_ask + 2), -6))
                        orders.append(Order(product, (new_ask + 3), -6))
                        orders.append(Order(product, (new_ask + 4), -7))
                        orders.append(Order(product, (new_ask + 5), -8))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 13:
                        orders.append(Order(product, (new_bid - 5), 2))
                        orders.append(Order(product, (new_bid - 4), 2))
                        orders.append(Order(product, (new_bid - 3), 1))
                        orders.append(Order(product, (new_bid - 2), 1))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -5))
                        orders.append(Order(product, (new_ask + 2), -6))
                        orders.append(Order(product, (new_ask + 3), -7))
                        orders.append(Order(product, (new_ask + 4), -7))
                        orders.append(Order(product, (new_ask + 5), -8))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 14:
                        orders.append(Order(product, (new_bid - 5), 2))
                        orders.append(Order(product, (new_bid - 4), 1))
                        orders.append(Order(product, (new_bid - 3), 1))
                        orders.append(Order(product, (new_bid - 2), 1))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -5))
                        orders.append(Order(product, (new_ask + 2), -6))
                        orders.append(Order(product, (new_ask + 3), -7))
                        orders.append(Order(product, (new_ask + 4), -8))
                        orders.append(Order(product, (new_ask + 5), -8))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 15:
                        orders.append(Order(product, (new_bid - 5), 1))
                        orders.append(Order(product, (new_bid - 4), 1))
                        orders.append(Order(product, (new_bid - 3), 1))
                        orders.append(Order(product, (new_bid - 2), 1))
                        orders.append(Order(product, (new_bid - 1), 1))
                        orders.append(Order(product, (new_ask + 1), -5))
                        orders.append(Order(product, (new_ask + 2), -6))
                        orders.append(Order(product, (new_ask + 3), -7))
                        orders.append(Order(product, (new_ask + 4), -8))
                        orders.append(Order(product, (new_ask + 5), -9))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 16:
                        orders.append(Order(product, (new_bid - 5), 1))
                        orders.append(Order(product, (new_bid - 4), 1))
                        orders.append(Order(product, (new_bid - 3), 1))
                        orders.append(Order(product, (new_bid - 2), 1))
                        orders.append(Order(product, (new_ask + 1), -6))
                        orders.append(Order(product, (new_ask + 2), -6))
                        orders.append(Order(product, (new_ask + 3), -7))
                        orders.append(Order(product, (new_ask + 4), -8))
                        orders.append(Order(product, (new_ask + 5), -9))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 17:
                        orders.append(Order(product, (new_bid - 5), 1))
                        orders.append(Order(product, (new_bid - 4), 1))
                        orders.append(Order(product, (new_bid - 3), 1))
                        orders.append(Order(product, (new_ask + 1), -6))
                        orders.append(Order(product, (new_ask + 2), -7))
                        orders.append(Order(product, (new_ask + 3), -7))
                        orders.append(Order(product, (new_ask + 4), -8))
                        orders.append(Order(product, (new_ask + 5), -9))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 18:
                        orders.append(Order(product, (new_bid - 5), 1))
                        orders.append(Order(product, (new_bid - 4), 1))
                        orders.append(Order(product, (new_ask + 1), -6))
                        orders.append(Order(product, (new_ask + 2), -7))
                        orders.append(Order(product, (new_ask + 3), -8))
                        orders.append(Order(product, (new_ask + 4), -8))
                        orders.append(Order(product, (new_ask + 5), -9))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 19:
                        orders.append(Order(product, (new_bid - 5), 1))
                        orders.append(Order(product, (new_ask + 1), -6))
                        orders.append(Order(product, (new_ask + 2), -7))
                        orders.append(Order(product, (new_ask + 3), -8))
                        orders.append(Order(product, (new_ask + 4), -9))
                        orders.append(Order(product, (new_ask + 5), -9))
                        print("Position2: ", position + position_changes)
                    
                    elif (position + position_changes) == 20:
                        orders.append(Order(product, (new_ask + 1), -6))
                        orders.append(Order(product, (new_ask + 2), -7))
                        orders.append(Order(product, (new_ask + 3), -8))
                        orders.append(Order(product, (new_ask + 4), -9))
                        orders.append(Order(product, (new_ask + 5), -10))
                        print("Position2: ", position + position_changes)
                    
                    
                    sum = 0
                    for x in orders:
                        sum = sum + x.quantity
                    
                    
                    print("Position Change:", position_changes)
                    
                    print("Net of all Trades:", sum)
                    
                    print("Orders: ", orders)
                    
                    '''
                    print("Mid Price:", mid_price)
                    print ("WAP:", WAP)
                    print ("GMP", GMP)
                    print ("HMP", HMP)
                    print ("MGP", MGP)
                    print ("MedP", MedP)
                    
                    
                    print ("New Bid:", new_bid)
                    print ("MeaP:", MeaP)
                    print ("New Ask:", new_ask)
                    
                    '''
                    
                    
                    
                    
                print("- - - - - - - - - -")
                print("Own Trades: ", state.own_trades)
                print("- - - - - - - - - -")
                print("Market Trades: ", state.market_trades)
                
                del new_bid, new_ask, ob_buy_volume_total, ob_sell_volume_total
                
                # Add all the above orders to the result dict
                result[product] = orders
                
            
            
            
        return result