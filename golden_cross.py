'''
This script tests whether the technical analysis "Golden Cross" predicts stock price increases.

Golden Cross T.A. claims that if the short term simple moving average (eg 10 days) is higher than the long term SMA (eg 50 days) with a higher than
usual volume (estimated here by a daily volume being higher than the volume sma), then underlying stock price should increase.

This script creates another csv with an index of 1 through 100.  This index specifies whether the underlying stock price increased beyond 
3 times standard devation within a certain number of days.  For example, at positon 10, you get the % of days that the underlying stock price
increased beyond 3 times standard deviation within 10 days.



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


file='data/AMD-underlying_data_2018-01-01_to_2020-07-01.csv' #insert the csv created by Analyzer.pull_underlying()

gc_days=2
#gc_days = # of days in a row that are GC positive (meaning 10day SMA higher than 50 day and volume higher than 10 day volume SMA)

underlying=pd.read_csv('{}'.format(file), index_col='date')
columns_to_drop = ['open','high','low']
#['open', 'high', 'low', 'close', 'volume']
underlying.drop(columns=columns_to_drop, inplace=True)



#------------
#Getting simple moving averages of underlying
#underlying.drop(underlying.columns[underlying.columns.str.contains('unnamed', case=False)], axis=1,inplace=True)
underlying['SMA10']=underlying.iloc[:,0].rolling(window=10).mean()
underlying['SMA50']=underlying.iloc[:,0].rolling(window=50).mean()
#underlying['SMA200']=underlying.iloc[:,0].rolling(window=200).mean()
underlying['Vol-SMA10']=underlying.iloc[:,1].rolling(window=10).mean()
underlying['Vol-SMA50']=underlying.iloc[:,1].rolling(window=50).mean()

#getting the standard deviations
underlying['std20']=underlying.iloc[:,0].rolling(window=20).std()
underlying['std20 2']=underlying['std20']*2
underlying['std20 3']=underlying['std20']*3



with open('gc_{}.csv'.format(fild), 'w', newline='') as csvfile:
	writer = csv.writer(csvfile)
	writer.writerow(['num_days', 'total%  increase', 'Goldencross +', 'Goldencross-', '# pos', '# neg'])
	# total% increase = % of days where stock price increased more than 3 times std  within num_days
	# Goldencross + is % of days where golden cross was applicable where stock price increased more than 3 times std  within num_days
	# Goldencross - = days where gc was not applicable and stock price increased more than 3 times std  within num_days
	#   # pos and # neg  gives # of days within sample period where golden cross was negative or positive


	for nd in range(1, 101):


		#True if closing price goes above 3*std within x num_days
		num_days=nd
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




		#Does same thing except for 2*std
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




		
		
		
		
		
		for i in range(49+gc_days, underlying.shape[0]):
			'''
			49 days because you need SMA50...and that can't get calculated until you have 49 days

			Set multi to True if the all of the last 3 days have been golden cross applicable.  
			'''
			
			multi=False
			for gcd in range(0, gc_days+1):
				if (underlying.loc[underlying.index[i-gcd], 'SMA10']>underlying.loc[underlying.index[i-gcd], 'SMA50']) and (underlying.loc[underlying.index[i-gcd], 'volume']>underlying.loc[underlying.index[i-gcd], 'Vol-SMA10']):
					multi=True
					continue
				else:
					#if any are not gc applicable, multi is set to false and the loop is broken
					multi=False
					break

				
			underlying.at[underlying.index[i], 'multiple_gc'] = multi


		
		gold_cross=underlying.loc[underlying['multiple_gc']==True]
		anti_gc=underlying.loc[underlying['multiple_gc']==False]
		

		gold_cross_inc=gold_cross.loc[gold_cross['Increase +3std']==True]
		anti_gc_inc=anti_gc.loc[anti_gc['Increase +3std']==True]


		gc=underlying.loc[underlying['Increase +3std']==True]
		ul=underlying.loc[underlying['SMA50'].notnull()]
		perc_inc=(gc.shape[0]/ul.shape[0])*100





		#percent_gc and percent_anti = percentage of golden_cross pos or neg days where underlying did increase 3*std
		percent_gc=(gold_cross_inc.shape[0]/gold_cross.shape[0])*100
		percent_anti=(anti_gc_inc.shape[0]/anti_gc.shape[0])*100

		writer.writerow([num_days,perc_inc, percent_gc, percent_anti, gold_cross.shape[0], anti_gc.shape[0]])
