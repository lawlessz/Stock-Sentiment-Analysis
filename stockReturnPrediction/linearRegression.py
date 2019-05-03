import pandas as pd
import mysqlClient
from sklearn import preprocessing
import statsmodels.api as sm
from statsmodels.sandbox.regression.predstd import wls_prediction_std
import matplotlib.pyplot as plt

stock = 'GOOG'
tickers = ['AAPL', 'AMD', 'AMZN', 'FB', 'GOOG', 'MSFT']
mysql_con = mysqlClient.mysql_connection()
mysql_con.init_engine('tweets_features')
type = '1H'
for stock in tickers:
    # stock = 'GOOG'
    # print(stock)
    get_stock_query = f'SELECT `time`, `close` FROM stock_prices.{stock}_{type};'
    stock_data = pd.DataFrame(list(mysql_con.select_query(get_stock_query)), columns=['time', 'return'])
    stock_data.set_index('time', inplace=True)
    stock_data.dropna(inplace=True)
    if type == '1D':
        stock_data['return'] = stock_data['return'].pct_change()
    stock_data.shift(1)



    if type == '1D':
        get_tweets_input_query = f"select * from tweets_features.{stock}_{type}_IN_TRADING_HOUR;"
        tweets_data = pd.DataFrame(list(mysql_con.select_query(get_tweets_input_query)),
                                   columns=['DATETIME', 'POSTS', 'FOLLOWERS', 'FOLLOWING', 'BULLISH', 'BEARISH', 'NEUTRAL',
                                            'FOLLOWER_NORMALIZED', 'FOLLOWING_NORMALIZED', 'POSTS_NORMALIZED',
                                            'BULLISH_FOLLOWER_WEIGHTED', 'BULLISH_FOLLOWING_WEIGHTED',
                                            'BULLISH_POSTS_WEIGHTED',
                                            'BEARISH_FOLLOWER_WEIGHTED', 'BEARISH_FOLLOWING_WEIGHTED',
                                            'BEARISH_POSTS_WEIGHTED',
                                            'NEUTRAL_FOLLOWER_WEIGHTED', 'NEUTRAL_FOLLOWING_WEIGHTED',
                                            'NEUTRAL_POSTS_WEIGHTED',
                                            'TWEETS_COUNT'])
    else:
        get_tweets_input_query = f"select * from tweets_features.{stock}_{type};"
        tweets_data = pd.DataFrame(list(mysql_con.select_query(get_tweets_input_query)),
                                   columns=['DATETIME', 'POSTS', 'FOLLOWERS', 'FOLLOWING', 'BULLISH', 'BEARISH', 'NEUTRAL',
                                            'FOLLOWER_NORMALIZED', 'FOLLOWING_NORMALIZED', 'POSTS_NORMALIZED',
                                            'BULLISH_FOLLOWER_WEIGHTED', 'BULLISH_FOLLOWING_WEIGHTED',
                                            'BULLISH_POSTS_WEIGHTED',
                                            'BEARISH_FOLLOWER_WEIGHTED', 'BEARISH_FOLLOWING_WEIGHTED',
                                            'BEARISH_POSTS_WEIGHTED',
                                            'NEUTRAL_FOLLOWER_WEIGHTED', 'NEUTRAL_FOLLOWING_WEIGHTED',
                                            'NEUTRAL_POSTS_WEIGHTED',
                                            'TWEETS_COUNT', 'IN_TRADING_HOUR', 'BULLISH_COUNT', 'BEARISH_COUNT', 'NEUTRAL_COUNT'])

    tweets_data.set_index('DATETIME', inplace=True)
    x = tweets_data.values  # returns a numpy array
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    tweets_data = pd.DataFrame(x_scaled, index=tweets_data.index, columns=tweets_data.columns)
    # tweets_data = tweets_data.shift(-1)

    merge_data = pd.merge(stock_data, tweets_data, how='left', left_index=True, right_index=True).dropna()


    y = merge_data['return']
    X = merge_data[[i for i in merge_data.columns if i !='return']]
    X = sm.add_constant(X)
    model11 = sm.OLS(y, X).fit()
    print(model11.summary())

    compare_df = pd.DataFrame([])
    compare_df['actual'] = y
    compare_df['fitted'] = model11.fittedvalues
    # plt.figure()
    # x=compare_df.plot()
    # plt.show()
    compare_df.to_sql(con=mysql_con.engine, if_exists='replace', index=True, name=f'{stock}_{type}_REGRESSION',
                           chunksize=500)
