'''
Helpful info:

Moving averages are an important analytical tool used to identify current price trends and the potential for a change in an established trend. The simplest use of a SMA in analysis is using it to quickly identify if a security is in an uptrend or downtrend. Another popular, albeit slightly more complex, analytical use is to compare a pair of simple moving averages with each covering different time frames. If a shorter-term simple moving average is above a longer-term average, an uptrend is expected. On the other hand, if the long-term average is above a shorter-term average then a downtrend might be the expected outcome.

Popular Trading Patterns
Two popular trading patterns that use simple moving averages include the death cross and a golden cross. A death cross occurs when the 50-day SMA crosses below the 200-day SMA. This is considered a bearish signal, that further losses are in store. The golden cross occurs when a short-term SMA breaks above a long-term SMA. Reinforced by high trading volumes, this can signal further gains are in store.


It seems like on days where 10day SMA is higher than 50day SMA (golden cross days), there is a 10% chance that underlying will increase 3stds within 5 days
There is a 2% chance on non-goldencross days

Also check if volume matters



---next experiment

Find periods of time where underlying went down.  Check various expiry_dist strike_dist combos and see which went down the least during these dips.

Then find periods of time where underlying went up.  Which strike_dist expiry dist combos did option prices increase the most?

Can you find strike_dist, expiry_dist combos which seem to minimize losses on dips, but maximize gains on uptrends?



'''

import time
import numpy as np
import pandas as pd
from pandas import Timestamp
import csv
from datetime import datetime, date, timedelta
import os
from glob import glob
import random
import calendar

SYMBOL='HD'

#underlying=pd.read_csv('data/{}-underlying_data_2018-01-01_to_2020-07-01.csv'.format(SYMBOL), index_col='date')
#columns_to_drop = ['open','high','low', 'volume']
#['open', 'high', 'low', 'close', 'volume']
#underlying.drop(columns=columns_to_drop, inplace=True)
#print(underlying.columns)

'''
#------------
#Getting simple moving averages of underlying
#underlying.drop(underlying.columns[underlying.columns.str.contains('unnamed', case=False)], axis=1,inplace=True)
underlying['SMA10']=underlying.iloc[:,0].rolling(window=10).mean()
underlying['SMA50']=underlying.iloc[:,0].rolling(window=50).mean()
#underlying['Vol-SMA10']=underlying.iloc[:,1].rolling(window=10).mean()
#underlying['Vol-SMA50']=underlying.iloc[:,1].rolling(window=50).mean()
underlying['std20']=underlying.iloc[:,0].rolling(window=20).std()
underlying['std20 2']=underlying['std20']*2
underlying['std20 3']=underlying['std20']*3


#True if closing price goes above 3*std within x num_days
num_days=5
for i in range(19, underlying.shape[0]-num_days):
#starts at 19 because the std is averaged over 20 days, so std doesn't exist before this
#-num_days because it looks at the next num_days, so we can't do this check at the very end of the df
#	print(underlying.loc[underlying.index[i],'close']+underlying.loc[underlying.index[i],'std20 3'])
	stand=underlying.loc[underlying.index[i],'close']+underlying.loc[underlying.index[i],'std20 3']
	increase=False
	for n in range(1,num_days+1):
		if underlying.loc[underlying.index[i+n],'close'] >= stand:
			increase=True
			break
		
	underlying.at[underlying.index[i], 'Increase +3std'] = increase




#Doese same thing except for 2*std
for i in range(19, underlying.shape[0]-num_days):
#starts at 19 because the std is averaged over 20 days, so std doesn't exist before this
#-num_days because it looks at the next num_days, so we can't do this check at the very end of the df
#	print(underlying.loc[underlying.index[i],'close']+underlying.loc[underlying.index[i],'std20 3'])
	stand=underlying.loc[underlying.index[i],'close']+underlying.loc[underlying.index[i],'std20 2']
	increase=False
	for n in range(1,num_days+1):
		if underlying.loc[underlying.index[i+n],'close'] >= stand:
			increase=True
			break
		
	underlying.at[underlying.index[i], 'Increase +2std'] = increase


underlying.to_csv('data/{}-SMA.csv'.format(SYMBOL))

'''
#-----Plain old tradier lookup and push to csv


SYMBOL='AMD'

api_key = #insert your own api key

response = requests.get('https://sandbox.tradier.com/v1/markets/history',
    params={'symbol': SYMBOL, 'interval': 'daily', 'start': '2016-01-01', 'end': '2020-05-15'},
    headers={'Authorization': 'Bearer {}'.format(api_key), 'Accept': 'application/json'}
)

if response:
	print("Success!")
else:
	print("Error")

json_response = response.json()

days = json_response['history']['day']

df = pd.DataFrame(days)

#index_label in to_csv() simply names the index date, doesn't set date as index
df.set_index('date', inplace=True)
print(df.head())

#df.to_csv('{}.csv'.format(SYMBOL), index_label='date')

#Save to CSV.  Remember, Excel changes formats of dates, so don't get confused


'''



#------

gold_cross=underlying.loc[underlying['SMA10']>underlying['SMA50']]
anti_gc=underlying.loc[underlying['SMA10']<underlying['SMA50']]

gold_cross_inc=gold_cross.loc[gold_cross['Increase +3std']==True]
anti_gc_inc=anti_gc.loc[anti_gc['Increase +3std']==True]


gc=underlying.loc[underlying['Increase +3std']==True]
ul=underlying.loc[underlying['SMA50'].notnull()]
perc_inc=(gc.shape[0]/ul.shape[0])*100





#percent_gc and percent_anti = percentage of golden_cross pos or neg days where underlying did increase 3*std
percent_gc=(gold_cross_inc.shape[0]/gold_cross.shape[0])*100
percent_anti=(anti_gc_inc.shape[0]/anti_gc.shape[0])*100

print('number of days={}'.format(num_days))
print('percent of total where underlying increased={}'.format(perc_inc))
print('percent of goldencross where underlying increased={}'.format(percent_gc))
print('percent of non-gold cross where underlying increaesd={}'.format(percent_anti))








#----------
df=pd.read_csv('data/{}--Analyzer_Results_2018-01-01_to_2020-07-01.csv'.format(SYMBOL), index_col='index')
#df=pd.read_csv('data/results-AMD.csv', index_col='index')
#index tuples are saved as strings.  No idea why.  Eval() converts back to tuples
dex = [eval(t) for t in df.index]
#print(df.index)
df.index=pd.MultiIndex.from_tuples(dex, names=['date','exp_dist'])
#recreates multi-index
#----------


#----------
#How to get the std of thet entire 'close' column
#underlying=underlying.replace(['NaN'], None)
#print(underlying['close'].std())


#df=df.join(underlying, how='inner')
#Adds the 'close' column  = underlying close price per date

#---
#mask, idx = df.index.get_loc_level('1', level='exp_dist')
#df_valid=df.loc[mask]
#---filters by exp_dist

#---
#df_valid=df_valid.loc['2019-09-01':'2019-11-30', :]
#---filters by date


#---
#df_valid=df_valid.replace(['NaN'], None)
#---removes all 'NaN' strings so mean(), std(), other equations can work

#---
#df_valid.loc[:, df_valid.columns != 'close' ]=df_valid.loc[:, df_valid.columns != 'close' ]*100
#---How to preform a function on all columns except 'close' column
#---in this case, multiply all by 100


#----------
#This creates csv that shows how avg cost of option relates to expiry dist




lis=['expiry']

for n in range(-20,21):
	lis.append(str(n))

with open('avg_cost_per_expiry-{}.csv'.format(SYMBOL), 'w', newline='') as csvfile:

	writer = csv.writer(csvfile)
	writer.writerow(lis)

	for exp in range(1,13):

		lst=[str(exp)]

		mask, idx = df.index.get_loc_level(str(exp), level='exp_dist')
		df_valid=df.loc[mask]

		df_valid=df_valid.replace(['NaN'], None)

		for s in range(-20, 21):
			lst.append(df_valid[str(s)].mean())

		writer.writerow(lst)
'''
