Pulls Options data from Tradier and organizes it in a dataframe/csv of form:




						-20  -19  -18  ...  18  19  20
	date1 expiry_dist1
		  expiry_dist2
		  expiry_dist3
	date2 expiry_dist1
		  expiry_dist2
		  expiry_dist3

Where index is multi-index of date and the distance between that date and the expiration date of the option.  The columns are -20 to +20, which correlates to the distance the option strike price is from the underlying stock price on a particular day.


Versions and packages used for this project:

Python 3.8.5  
requests==2.24.0
numpy==1.19.1
pandas==1.1.0
