'''
Still under construction.

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

underlying=pd.read_csv('data/NVDA-underlying_data_2018-01-01_to_2020-07-01.csv', index_col='date')
columns_to_drop = ['open','high','low','volume']
underlying.drop(columns=columns_to_drop, inplace=True)
#underlying.drop(underlying.columns[underlying.columns.str.contains('unnamed', case=False)], axis=1,inplace=True)

df=pd.read_csv('data/NVDA--Analyzer_Results_2018-01-01_to_2020-07-01.csv', index_col='index')
#index tuples are saved as strings.  No idea why.  Eval() converts back to tuples
dex = [eval(t) for t in df.index]
#print(df.index)
df.index=pd.MultiIndex.from_tuples(dex, names=['date','exp_dist'])
#recreates multi-index

underlying=underlying.replace(['NaN'], None)
print(underlying['close'].std())


df=df.join(underlying, how='inner')
#Adds the 'close' column  = underlying close price per date

#---
mask, idx = df.index.get_loc_level('1', level='exp_dist')
df_valid=df.loc[mask]
#---filters by exp_dist

#---
#df_valid=df_valid.loc['2019-09-01':'2019-11-30', :]
#---filters by date


#---
df_valid=df_valid.replace(['NaN'], None)
#---removes all 'NaN' strings so mean(), std(), other equations can work

#---
#df_valid.loc[:, df_valid.columns != 'close' ]=df_valid.loc[:, df_valid.columns != 'close' ]*100
#---How to preform a function on all columns except 'close' column
#---in this case, multiply all by 100


#----------
#This creates csv that shows how avg cost of option relates to expiry dist
'''
lis=['expiry']

for n in range(-20,21):
	lis.append(str(n))

with open('std_cost_per_expiry-{}.csv'.format('NVDA'), 'w', newline='') as csvfile:

	writer = csv.writer(csvfile)
	writer.writerow(lis)

	for exp in range(1,13):

		lst=[str(exp)]

		mask, idx = df.index.get_loc_level(str(exp), level='exp_dist')
		df_valid=df.loc[mask]

		df_valid=df_valid.replace(['NaN'], None)

		for s in range(-20, 21):
			lst.append(df_valid[str(s)].std())

		writer.writerow(lst)

'''