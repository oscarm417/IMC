import pandas as pd

df = pd.DataFrame()
df_bananas = pd.DataFrame(columns=['day', 'timestamp', 'product', 'bid_price', 'bid_volume', 'ask_price', 'ask_volume'])
df_pearls = pd.DataFrame(columns=['day', 'timestamp', 'product', 'bid_price', 'bid_volume', 'ask_price', 'ask_volume'])



df = pd.read_csv('orderbook_data.csv', delimiter=';')
df = df.drop(['profit_and_loss', 'mid_price'], axis=1)
df = df.fillna(0)

average_bid = []
average_ask = []
total_bid_volume = []
total_ask_volume = []
for idx, row in df.iterrows():
    bid_volume = int(row['bid_volume_1']) + int(row['bid_volume_2']) + int(row['bid_volume_3'])
    ask_volume = int(row['ask_volume_1']) + int(row['ask_volume_2']) + int(row['ask_volume_3'])
    bid_price = (int(row['bid_volume_1']) * int(row['bid_price_1']) + int(row['bid_volume_2']) * int(row['bid_price_2']) + int(row['bid_volume_3']) * int(row['bid_price_3'])) / bid_volume
    ask_price = (int(row['ask_volume_1']) * int(row['ask_price_1']) + int(row['ask_volume_2']) * int(row['ask_price_2']) + int(row['ask_volume_3']) * int(row['ask_price_3'])) / ask_volume
    average_bid.append(bid_price)
    average_ask.append(ask_price)
    total_bid_volume.append(bid_volume)
    total_ask_volume.append(ask_volume)

df = df.drop(['ask_volume_3', 'ask_price_3', 'ask_volume_2', 'ask_price_2', 'bid_volume_3', 'bid_price_3', 'bid_volume_2', 'bid_price_2', 'bid_price_1', 'bid_volume_1', 'ask_price_1', 'ask_volume_1'], axis=1)
#df = df.drop(['profit_and_loss', 'mid_price', 'ask_volume_3', 'ask_price_3', 'ask_volume_2', 'ask_price_2', 'bid_volume_3', 'bid_price_3', 'bid_volume_2', 'bid_price_2'], axis=1)


df['average_bid'] = average_bid
df['total_bid_volume'] = total_bid_volume
df['average_ask'] = average_ask
df['total_ask_volume'] = total_ask_volume


df.insert(loc=-1, column='average_bid', value=average_bid)
df.insert(loc=-1, column='total_bid_volume', value=total_bid_volume)
df.insert(loc=-1, column='average_ask', value=average_ask)
df.insert(loc=-1, column='total_ask_volume', value=total_ask_volume)


for idx, row in df.iterrows():
    if row['product'] == 'BANANAS':
        df_bananas.loc[idx] = row
    if row['product'] == 'PEARLS':
        df_pearls.loc[idx] = row

df_bananas = df_bananas.reset_index()
df_pearls = df_pearls.reset_index()

df_bananas = df_bananas.drop(['product', 'index'], axis=1)
df_pearls = df_pearls.drop(['product', 'index'], axis=1)

df_bananas.to_csv('orderbook_data_bananas.csv', index=False, header=False)
df_pearls.to_csv('orderbook_data_pearls.csv', index=False, header=False)
