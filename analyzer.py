'''
NOTES:
When trying to analyzer SPCE, if I try to include 2019 dates, I get the error:

cannot concatenate object of type '<class 'list'>'; only Series and DataFrame objs are valid

I think this has something to do with SPCE being a very new stock.  IPO was end of Oct 2019.  I guess those first two months Tradier has them 
formated differently and it fucks with my code.  If I only pull 2020 data, it works fine.  Might be something worth looking into.



'''
import requests
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import time
import calendar
from dateutil.relativedelta import relativedelta




class Analyzer(object):

	def __init__(self, SYMBOL, start_date, end_date, API_key):
		'''
		Dates in form '%Y-%m-%d', eg '2020-08-16'

		'''

		self.SYMBOL=SYMBOL
		self.start_date=start_date
		self.end_date=end_date
		self.API_key=API_key

	def datestring_to_datetime(self, date_str):
		
		'''
		Converts a date string of format'%Y-%m-%d', eg '2020-08-16' and
		converts it to a pandas datetime object (not a Python native datetime object)
		'''

		date=pd.to_datetime(date_str, format='%Y-%m-%d', errors='raise')

		return date


	def datetime_to_datestring(self, date):
		'''
		Takes pandas datetime object (not Python native datetime object) and
		converts to a string which can then be fed to the Tradier API
		'''
		date_string=date.strftime('%Y-%m-%d')

		return date_string


	def create_ticker(self, symbol, expiration, strike):
		'''
		This function takes info and creates an OCC formatted ticker symbol
		This particular function creates call option tickers
		'''

		ticker = "{symbol}{y}{m:02d}{d:02d}C{strike:05d}000".format(symbol=symbol, y=str(
	            expiration.year)[2:], m=expiration.month, d=expiration.day, strike=strike)
		return ticker

	def third_fridays(self,d, n):
		'''
		Given a date, calculates n next third fridays
		Returns a list
		https://stackoverflow.com/questions/28680896/how-can-i-get-the-3rd-friday-of-a-month-in-python/28681097
		'''
	 
		def next_third_friday(d):
			""" Given a third friday find next third friday"""
			d += timedelta(weeks=4)
			return d if d.day >= 15 else d + timedelta(weeks=1)
	
		# Find closest friday to 15th of month
		s = date(d.year, d.month, 15)
		result = [s + timedelta(days=(calendar.FRIDAY - s.weekday()) % 7)]
	 
		# This month's third friday passed. Find next.
		if result[0] < d:
			result[0] = next_third_friday(result[0])
	 
		for i in range(n - 1):
			result.append(next_third_friday(result[-1]))
	 
		return result

	def pull_underlying(self):
		'''
		This method pulls historical data for the underlying stock
		'''

		response = requests.get('https://sandbox.tradier.com/v1/markets/history',
    params={'symbol': self.SYMBOL, 'interval': 'daily', 'start': self.start_date, 'end': self.end_date},
    headers={'Authorization': 'Bearer {}'.format(self.API_key), 'Accept': 'application/json'}
)

		if response:
			print("Success!")
		else:
			print("Error")

		json_response = response.json()

		days = json_response['history']['day']

		underlying = pd.DataFrame(days)
		underlying['date']= pd.to_datetime(underlying['date']) 

	
		underlying.set_index('date', inplace=True)

		return underlying

	def make_tickers(self, underlying):
		'''
		underlying = df returned from Analyzer.pull_underlying()

		This method generates all the tickers.  It goes month by month over the time frame.  For each month, it
		figures out the range of strike prices +20 over the monthly highs and -20 under monthly lows.  Then, it
		figures out the date of the next 12 third fridays (typical option expiry date).  For each of those expiry dates,
		and for each of the strike prices, it generates a unique ticker and keeps track of how many months away the expiry is from
		'current' month in the loop.
		
		'''

		#Drops all columns except date and closing price
		columns_to_drop = ['open','high','low','volume']
		underlying.drop(columns=columns_to_drop, inplace=True)
		
		#underlying.drop(underlying.columns[underlying.columns.str.contains('unnamed', case=False)], axis=1,inplace=True)
		##In case there's a weird unnamed column, you can use the above to drop it

		underlying['close']=underlying['close'].round(0)
		#Rounds the closing price to whole number

		start_date_dt=self.datestring_to_datetime(self.start_date).replace(day=1)
		end_date_dt=self.datestring_to_datetime(self.end_date).replace(day=1)
		#change dates to first of month...to keep things running smoothly

		delta=relativedelta(end_date_dt,start_date_dt) #Gets time between dates
		num_months=(delta.years*12)+delta.months       #Gets # of months between the two dates




		tickers={'expiry_dist':[], 'strike':[],'ticker':[], 'month_start':[], 'month_end':[]}
		
		
		for n in range(0,num_months):
			#cycles through num of months between the start and end date


			start_month=start_date_dt+pd.DateOffset(months=n)

			end_month=start_month+pd.DateOffset(days=calendar.monthrange(start_month.year,start_month.month)[1]-1)
			#calendar.monthrange(year,month) gives tuple of first weekday of month and # of days in month=last day
			#-1 because we are adding to the start day.  We want last day, not first day of next month


			current_month=underlying[start_month:end_month] #slices out month in underlying

			
			high=current_month['close'].max()
			low=current_month['close'].min()
			#Gets high and low closes of current month
			#Use this to determine strike ranges to pull from tradier
			

			#Gets range of strikes -20 to +20
			strikes=[]
			if low>20:
				for i in range(int(low-20),int(high+21)):
					strikes.append(i)
			else:
				#in case underlying is less than 20
				for i in range(1,int(high+21)):
					strikes.append(i)


			#Calculates next 12 third fridays, starting with the next month
			#for expiry dates
			thirds=self.third_fridays(end_month,12)

			#This loop determines the distance each expiration date is from
			#current month
			thirds_dict={'expiry_dist':[],'expiry_date':[]}
			for t in thirds:		
				delta=relativedelta(t,start_month)#Gets time between expiry date and current month
				thirds_dict['expiry_dist'].append((delta.years*12)+delta.months)
				thirds_dict['expiry_date'].append(t)

			#Turns it into a df
			thirds_df=pd.DataFrame(thirds_dict)
			thirds_df.set_index('expiry_dist', inplace=True)

			
			ticker_check=[]
			
			for index,row in thirds_df.iterrows():
				expiry_dist=index

				for s in strikes:
					expiry=row['expiry_date']
					strike=s

					ticker = self.create_ticker(self.SYMBOL, expiry, strike)
					tickerc=ticker+str(expiry_dist)
					#ticker_check ensures I don't duplicate tickers
					#I create tickerc which is ticker+expirydist since
					#some tickers might be relevant for several months
					if tickerc not in ticker_check:
						ticker_check.append(tickerc)

						tickers['expiry_dist'].append(expiry_dist)
						tickers['strike'].append(s)
						tickers['ticker'].append(ticker)
						tickers['month_start'].append(start_month)
						tickers['month_end'].append(end_month)
					


		tickers_df=pd.DataFrame(tickers)
		#tickers_df.to_csv('tickers_check.csv', index_label='Index')

		return tickers_df


	def first_pass_pullup(self, tickers_df):
		'''
		Takes a dataframe of tickers from Analyzer.make_tickers() and
		creates df of form:
		------------------------------------------------------
		|		strike1        	strike2         strike3
		|		expiry_dist1	expiry_dist2	expiry_dist3
		|
		|date1
		|date2
		|date3


		This method could take several hours.  Unfortunately, the free sandbox version of Tradier has a 60 API calls per minute 
		limit.  I have to artificially slow down the loop so I don't get capped.

		This loops month by month over the date range. and pulls up the historical data for that month for each strike price/expiry price combo

		Each month is then concatenated together to form the first draft version of our Analyzed options df, as seen above.  This df is then fed into
		the final_process function which restructures the df again to get the final version.

		'''
		num_tickers=len(tickers_df)

		start_date_dt=self.datestring_to_datetime(self.start_date).replace(day=1)
		end_date_dt=self.datestring_to_datetime(self.end_date).replace(day=1)
		#change dates to first of month...keep it simple

		delta=relativedelta(end_date_dt,start_date_dt) #Gets time between dates
		num_months=(delta.years*12)+delta.months       #Gets # of months between the two dates



		

		e_carry=[]
		not_first_run=False
		num=1

		for n in range(0,num_months):
			#cycles through num of months between the start and end date


			start_month=start_date_dt+pd.DateOffset(months=n)

			end_month=start_month+pd.DateOffset(days=calendar.monthrange(start_month.year,start_month.month)[1]-1)
			#Gets first and last day of each month within the daterange like in make_tickers()

			
			ticker_slice=tickers_df.loc[tickers_df['month_start'].astype('datetime64[ns]')==start_month]
			
			#slices out by month
			
			#strikes is a list of all strikes in the tickers csv for this month slice
			#exps is a list of all the expiry distances in the tickers csv for this month slice
			strikes=[s for s in range(ticker_slice['strike'].min(),(ticker_slice['strike'].max()+1))]
			exps=[e for e in range(ticker_slice['expiry_dist'].min(), (ticker_slice['expiry_dist'].max()+1))]

			#columns_to_drop = ['open','high','low','close']
			##if you want volumes instead of closes

			columns_to_drop = ['open','high','low','volume']
			#feed this to .drop() so that I only have 'date' as index and one other column

		
			for s in strikes:
				for e in exps:
					print('{}/{} tickers'.format(num, num_tickers)) #keep track of where you are in the process
					num+=1

					ticker= ticker_slice.loc[ticker_slice['expiry_dist']==e].loc[ticker_slice['strike']==s]['ticker'] 
					#Locate the ticker with a specific expiry_dist /strike combo.  Should only be one per slice
					
					start= ticker_slice.loc[ticker_slice['expiry_dist']==e].loc[ticker_slice['strike']==s]['month_start']
					end= ticker_slice.loc[ticker_slice['expiry_dist']==e].loc[ticker_slice['strike']==s]['month_end']
					#Use this start and end date for the tradier lookup
					
					try:
					#Many errors are possible, so try/except statements are necessary to keep things running regardless

						response = requests.get('https://sandbox.tradier.com/v1/markets/history',
					params={'symbol': ticker, 'interval': 'daily', 'start': start, 'end': end},
					headers={'Authorization': 'Bearer {}'.format(self.API_key), 'Accept': 'application/json'}
					)
					except Exception as e:
						print(e)
						continue


					if response.status_code==200:
						print("status = 200")
						json_response = response.json()
					else:
						print('status_code NOT 200')
						print(response.status_code)
						continue

					#Since I generated tickers myself, not all will work
					#This tries pulling data.  if json_response is empty..ticker didn't exist

					if not json_response['history']:
						print('Ticker does not exist')
						continue


					try:
						#PERFORM ACTIONS HERE.  The rest of this is error handling
						if not_first_run:
							'''
							the 'not_first_run' if/else statement initializes the df on first runthrough
							and then just concatenates to that original df each subsequent tradier lookup
							It's a little hackey, but it works
							'''

							history=json_response['history']['day']
							nexd = pd.DataFrame(history)
							nexd['date'] = nexd['date'].astype('datetime64[ns]')
							nexd.set_index('date', inplace=True)
							nexd.drop(columns=columns_to_drop, inplace=True)
							nexd.rename(columns={'close':(s,e)}, inplace=True)
							#renames the 'close' column to (strike, expiry_dist) tuple.  Can be converted to multi-index

							e_carry=pd.concat([e_carry,nexd])
							

						else:
							not_first_run=True
							history=json_response['history']['day']
							e_carry = pd.DataFrame(history)
							e_carry['date'] = e_carry['date'].astype('datetime64[ns]')
							e_carry.set_index('date', inplace=True)
							e_carry.drop(columns=columns_to_drop, inplace=True)
							e_carry.rename(columns={'close':(s,e)}, inplace=True)
							#save each column as tuple so I can convert to multi-index later

					except KeyError as k:
						
						print(k)
						continue

					except TypeError as t:
						print(t)
						continue

					except ValueError as v:
						#Sometimes there's only one datapoint, and throws this error
						#because it's a scalar value and fucks with pandas
						#I just ignore this data.  Woe is me.  I'll fix it one day.
						print(v)
						print(json_response['history'])
						continue
					except Traceback as e:
						#Since the ticker/tradier lookups take so long, sometimes the script
						#times out.  This just allows the program to keep running if that happens
						print(e)
						continue
		
		
		#e_carry.to_csv('e_carry-{}.csv'.format(SYMBOL), index_label='date') #In case you want to see this monstrosity of a df for some reason
		dxs=pd.concat([e_carry.loc[e_carry[c].notna(), c] for c in e_carry.columns], axis=1)
		#All the concatenations in the previous loop creates a very sloppy df with
		#many duplicate columns full of null values.
		#This line consolidates the dataframe and removes extraneous columns

		return dxs

	def first_pass_pullup_tickers(self, tickers_df):
		'''
		Takes a dataframe of tickers from Analyzer.make_tickers() and
		creates df of form:
		------------------------------------------------------
		|		strike1        	strike2         strike3
		|		expiry_dist1	expiry_dist2	expiry_dist3
		|
		|date1
		|date2
		|date3

		This does not do the Tradier lookup.  Instead, it makes an identical df...but instead of prices, it shows the tickers
		
		This lookup overloads the CPU/memory really quickly, so you should only use it for a month of data at a time.  
		Solutions to speed it up are welcome
		

		

		'''
		num_tickers=len(tickers_df)

		start_date_dt=self.datestring_to_datetime(self.start_date).replace(day=1)
		end_date_dt=self.datestring_to_datetime(self.end_date).replace(day=1)
		#change dates to first of month...keep it simple

		delta=relativedelta(end_date_dt,start_date_dt) #Gets time between dates
		num_months=(delta.years*12)+delta.months       #Gets # of months between the two dates


		e_carry=[]
		not_first_run=False
		num=1

		for n in range(0,num_months):
			#cycles through num of months between the start and end date


			start_month=start_date_dt+pd.DateOffset(months=n)

			end_month=start_month+pd.DateOffset(days=calendar.monthrange(start_month.year,start_month.month)[1]-1)
			#Gets first and last day of each month within the daterange like in make_tickers()

			
			ticker_slice=tickers_df.loc[tickers_df['month_start'].astype('datetime64[ns]')==start_month]
			
			#slices out by month
			
			#strikes is a list of all strikes in the tickers csv for this month slice
			#exps is a list of all the expiry distances in the tickers csv for this month slice
			strikes=[s for s in range(ticker_slice['strike'].min(),(ticker_slice['strike'].max()+1))]
			exps=[e for e in range(ticker_slice['expiry_dist'].min(), (ticker_slice['expiry_dist'].max()+1))]

			#columns_to_drop = ['open','high','low','close']
			##if you want volumes instead of closes


			#feed this to .drop() so that I only have 'date' as index and one other column

		
			for s in strikes:
				for e in exps:
					print('{}/{} tickers'.format(num, num_tickers)) #keep track of where you are in the process
					num+=1

					ticker= ticker_slice.loc[ticker_slice['expiry_dist']==e].loc[ticker_slice['strike']==s]['ticker'] 
					#Locate the ticker with a specific expiry_dist /strike combo.  Should only be one per slice
					
					start= ticker_slice.loc[ticker_slice['expiry_dist']==e].loc[ticker_slice['strike']==s]['month_start']
					end= ticker_slice.loc[ticker_slice['expiry_dist']==e].loc[ticker_slice['strike']==s]['month_end']
					#Use this start and end date for the tradier lookup
					
					
					#Instead of a tradier lookup, a dictionary is manually created of the same form

					dates=pd.date_range(start_month,end_month,freq='d')

					dic={'date':[], 'ticker':[]}
					dic['date']=dates
					dic['ticker']=np.full(len(dates),'.')
								#np seems to be the fastest way to fill the list.  Still gets bogged down in memory around 700 tickers in
								#[ticker]*len(dates)
								#[ticker for i in range(len(dates))]
					

					try:
						#PERFORM ACTIONS HERE.  The rest of this is error handling
						if not_first_run:
							'''
							the 'not_first_run' if/else statement initializes the df on first runthrough
							and then just concatenates to that original df each subsequent tradier lookup
							It's a little hackey, but it works
							'''

							history=dic
							nexd = pd.DataFrame(history)
							nexd['date'] = nexd['date'].astype('datetime64[ns]')
							nexd.set_index('date', inplace=True)
							
							nexd.rename(columns={'ticker':(s,e)}, inplace=True)
							#renames the 'close' column to (strike, expiry_dist) tuple.  Can be converted to multi-index

							e_carry=pd.concat([e_carry,nexd])
							

						else:
							not_first_run=True
							history=dic
							e_carry = pd.DataFrame(history)
							e_carry['date'] = e_carry['date'].astype('datetime64[ns]')
							e_carry.set_index('date', inplace=True)
							
							e_carry.rename(columns={'ticker':(s,e)}, inplace=True)
							#save each column as tuple so I can convert to multi-index later

					except KeyError as k:
						
						print(k)
						continue

					except TypeError as t:
						print(t)
						continue

					except ValueError as v:
						#Sometimes there's only one datapoint, and throws this error
						#because it's a scalar value and fucks with pandas
						#I just ignore this data.  Woe is me.  I'll fix it one day.
						print(v)
						continue
					except Traceback as e:
						#Since the ticker/tradier lookups take so long, sometimes the script
						#times out.  This just allows the program to keep running if that happens
						print(e)
						continue
		
		
		#e_carry.to_csv('e_carry-{}.csv'.format(SYMBOL), index_label='date') #In case you want to see this monstrosity of a df for some reason
		dxs=pd.concat([e_carry.loc[e_carry[c].notna(), c] for c in e_carry.columns], axis=1)
		#All the concatenations in the previous loop creates a very sloppy df with
		#many duplicate columns full of null values.
		#This line consolidates the dataframe and removes extraneous columns

		return dxs





def final_process(first_pass_dataframe, underlying_dataframe):
	'''
	Processes the info pulled up in Analyzer.first_pass_pullup()

	Converts from:
			strike
			expiry_dist	
	date

	

	Converts to:


						-20  -19  -18  ...  18  19  20
	date1 expiry_dist1
		  expiry_dist2
		  expiry_dist3
	date2 expiry_dist1
		  expiry_dist2
		  expiry_dist3
	
	first_pass_dataframe = result from Analyze.first_pass_pullup()
	underlying_dataframe = result from Analyze.pull_underlying()


	'''
	dxs=first_pass_dataframe
	dxs.columns = pd.MultiIndex.from_tuples(dxs.columns, names=['s','exp'])
	#now it's a multi-index

	uld=underlying_dataframe


	dic={'index':[]}

	for n in range(-20,21):
		dic.update({str(n):[]})
	#This creates the dict keys

	
	for index, row in uld.iterrows():
		
		up=int(round(row['close']))
		#Gotta remove the .0 from the end of each number so up matches index...that's why we set it to int()
		#up=underlying price for current day
		
		try:
			day=dxs.loc[index]
			
		except KeyError as k:
			print('DATE NOT INCLUDED:{}'.format(k))
			continue
		
		for e in range(1,13):
			dic['index'].append((index,str(int(e))))
			#index= [(date, exp_dist), (date, exp_dist), (date, exp_dist), ...]
			for n in range(-20,21):
				try:
					
					dic[str(n)].append(day.xs(up+int(n), axis=0, level=0)[int(e)])
					#xs(up+n) will give you underlying close plus 20 to minus 20.  the [int(e)] gets the correct expiry dist
				except KeyError as k:
					'''
					Sometimes the underlying closing price plus 20, or whatever, won't exist in the underlying data
					Not a huge deal.  If you want to see which strike or expiry dists aren't  being included, uncomment the print() command below

					'''

					#print('No Exp or strike:{}'.format(k))
					dic[str(n)].append('NaN')
					continue

	df=pd.DataFrame(dic)
	df.set_index('index', inplace=True)

	return df


if __name__ == "__main__":   


	#Edit SYMBOL, start_date, and end_date below

	SYMBOL='AMD'
	start_date='2018-04-01'
	end_date='2018-07-01'
	#Dates in form '%Y-%m-%d', eg '2020-08-16'

	#Dates must be first day of month.  Otherwise, you'll get all sorts of errors.

	API_key = "KjcDWUZqzMkUBtE7TVIl0ECNI8WS"


	#----------


	tp=Analyzer(SYMBOL, start_date, end_date, API_key)

	underlying=tp.pull_underlying()
	underlying.to_csv('data/{}-underlying_data_{}_to_{}.csv'.format(SYMBOL,start_date,end_date), index_label='date')

	tickers=tp.make_tickers(underlying)


	#uncomment what you want to use

	#--------Results are tickers-----------------------
	dxs_tickers=tp.first_pass_pullup_tickers(tickers)
	dxs_tickers.to_csv('data/date-x-strikes-tickers-{}.csv'.format(SYMBOL), index_label='date')

	result_tickers=final_process(dxs_tickers, underlying)
	result_tickers.to_csv('data/{}--Analyzer_Results_{}_to_{}_TICKERS.csv'.format(SYMBOL,start_date,end_date), index_label='index')

	#---------Results are options prices----------------
	#dxs=tp.first_pass_pullup(tickers)
	#dxs.to_csv('data/date-x-strikes-{}.csv'.format(SYMBOL), index_label='date')
	
	#result=final_process(dxs, underlying)
	#result.to_csv('data/{}--Analyzer_Results_{}_to_{}.csv'.format(SYMBOL,start_date,end_date), index_label='index')


