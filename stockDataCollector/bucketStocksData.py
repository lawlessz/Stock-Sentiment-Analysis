import mysqlClient
import pandas as pd
import datetime
import numpy as np


def in_trading_hour(x):
    start = datetime.time(14, 30)
    end = datetime.time(21, 0)
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start < x <= end
    else:
        return start < x or x <= end


def percent_change(x):
    if len(x):
        return (x[-1] - x[0]) / x[0]


mysql_con = mysqlClient.mysql_connection()
mysql_con.init_engine('stock_prices')
engine = mysql_con.engine
# ,
for stocks in ['AAPL', 'AMD', 'AMZN', 'FB', 'GOOG', 'MSFT']:
    print(f'getting {stocks} data...')
    data = mysql_con.select_query(f"SELECT * from stock_prices.{stocks};")
    data_df = pd.DataFrame(list(data),
                           columns=['TIME', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME'])
    data_df.set_index('TIME', inplace=True)
    applied_function = {'CLOSE': lambda x: percent_change(x), 'HIGH': 'max', 'LOW': 'min',
                        'OPEN': 'max', 'VOLUME': 'sum'}
    # for freq in ['5MIN', '15MIN', '30MIN', '1H', '2H', '6H', '12H']:
    for freq in ['1H']:
        print(f"getting {freq} bucket data...")
        this_data_batch = data_df.resample(freq).agg(applied_function)
        # this_data_batch['IN_TRADING_HOUR'] = this_data_batch.index.map(lambda x: in_trading_hour(x.time()))
        print(this_data_batch)
        this_data_batch.to_sql(con=mysql_con.engine, if_exists='replace', index=True, name=f'{stocks}_{freq}',
                               chunksize=500)



from pandas_datareader import data

start_date = '2018-10-01'
end_date = '2018-12-01'
tickers = ['AAPL', 'AMD', 'AMZN', 'FB', 'GOOG', 'MSFT']
# User pandas_reader.data.DataReader to load the desired data. As simple as that.
panel_data = data.DataReader(tickers, 'yahoo', start_date, end_date)
req_unstacked = panel_data.unstack().reset_index()
flated_df = req_unstacked.set_index(['Symbols', 'Date', 'Attributes']).unstack().reset_index()
flated_df.columns = flated_df.columns.droplevel()
flated_df.columns = ['SYMBOL', 'TIME', 'Adj Close', 'CLOSE', 'HIGH', 'LOW', 'OPEN', 'VOLUME']
for group in flated_df.groupby('SYMBOL'):
    symbol, data_df = group
    data_df.set_index('TIME', inplace=True)
    data_df.drop(columns=['SYMBOL'], inplace=True)
    data_df['Daily Adj Rt'] = data_df['Adj Close'].pct_change(1)
    data_df['Daily Rt'] = data_df['CLOSE'].pct_change(1)
    print(data_df)
    data_df.to_sql(con=mysql_con.engine, if_exists='replace', index=True, name=f'{symbol}_1D',
                               chunksize=500)
