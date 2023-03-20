
buy_order_layout = [3, 5, 9, 11]

old_value = buy_order_layout.pop(0)
buy_order_layout[0] +=  old_value

print(buy_order_layout)