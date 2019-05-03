import mysqlClient
import pandas as pd
import datetime
import numpy as np


def in_trading_hour(x):
    start = datetime.time(14, 30)
    end = datetime.time(21, 0)
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end


mysql_con = mysqlClient.mysql_connection()
mysql_con.init_engine('tweets_features')
engine = mysql_con.engine
# ,
for stocks in ['AAPL', 'AMD', 'AMZN', 'FB', 'GOOG', 'MSFT']:
    print(f'getting {stocks} data...')
    data = mysql_con.select_query(f"SELECT * from tweets_features.{stocks}_CLASSIFIED;")
    data_df = pd.DataFrame(list(data),
                           columns=['GUID', 'DATETIME', 'URL', 'CONTENTS', 'AUTHOR', 'NAME', 'COUNTRY',
                                    'STATE/REGION', 'CITY/URBAN_AREA', 'CATEGORY', 'EMOTION', 'SOURCE', 'GENDER',
                                    'POSTS', 'FOLLOWERS', 'FOLLOWING', 'POST_TITLES', 'POST_TYPE', 'IMAGE_URL',
                                    'BRAND', 'BULLISH', 'BEARISH', 'NEUTRAL'])
    data_df.set_index('DATETIME', inplace=True)
    data_df.drop(columns=['GUID'], inplace=True)

    # TODO: Factorize location data and sum the count for each location as a feature
    # data_df['COUNTRY'].fillna("HIDDING", inplace=True)
    # data_df['COUNTRY'] = data_df['COUNTRY'].apply(lambda col: pd.factorize(col, sort=True)[0])
    # all_category = data_df['CATEGORY'].unique()

    avg_followers = data_df['FOLLOWERS'].mean()
    std_followers = data_df['FOLLOWERS'].std()
    max_followers = data_df['FOLLOWERS'].max()
    min_followers = data_df['FOLLOWERS'].min()

    avg_following = data_df['FOLLOWING'].mean()
    std_following = data_df['FOLLOWING'].std()
    max_following = data_df['FOLLOWING'].max()
    min_following = data_df['FOLLOWING'].min()

    avg_posts = data_df['POSTS'].mean()
    std_posts = data_df['POSTS'].std()
    max_posts = data_df['POSTS'].max()
    min_posts = data_df['POSTS'].min()

    data_df['FOLLOWER_NORMALIZED'] = data_df['FOLLOWERS'].apply(
        lambda x: (x - min_followers) / (max_followers - min_followers))
    data_df['FOLLOWING_NORMALIZED'] = data_df['FOLLOWING'].apply(
        lambda x: (x - min_followers) / (max_followers - min_followers))
    data_df['POSTS_NORMALIZED'] = data_df['POSTS'].apply(
        lambda x: (x - min_followers) / (max_followers - min_followers))

    data_df['BULLISH_FOLLOWER_WEIGHTED'] = data_df['BULLISH'] * data_df['FOLLOWER_NORMALIZED']
    data_df['BULLISH_FOLLOWING_WEIGHTED'] = data_df['BULLISH'] * data_df['FOLLOWING_NORMALIZED']
    data_df['BULLISH_POSTS_WEIGHTED'] = data_df['BULLISH'] * data_df['POSTS_NORMALIZED']

    data_df['BEARISH_FOLLOWER_WEIGHTED'] = data_df['BEARISH'] * data_df['FOLLOWER_NORMALIZED']
    data_df['BEARISH_FOLLOWING_WEIGHTED'] = data_df['BEARISH'] * data_df['FOLLOWING_NORMALIZED']
    data_df['BEARISH_POSTS_WEIGHTED'] = data_df['BEARISH'] * data_df['POSTS_NORMALIZED']

    data_df['NEUTRAL_FOLLOWER_WEIGHTED'] = data_df['NEUTRAL'] * data_df['FOLLOWER_NORMALIZED']
    data_df['NEUTRAL_FOLLOWING_WEIGHTED'] = data_df['NEUTRAL'] * data_df['FOLLOWING_NORMALIZED']
    data_df['NEUTRAL_POSTS_WEIGHTED'] = data_df['NEUTRAL'] * data_df['POSTS_NORMALIZED']

    data_df['CATEGORY'] = data_df[['BULLISH', 'BEARISH', 'NEUTRAL']].idxmax(axis=1)
    for freq in ['5MIN', '15MIN', '30MIN', '1H', '2H', '6H', '12H']:
        print(f"getting {freq} bucket data...")
        this_data_batch = data_df.resample(freq).sum()
        this_data_batch_count = data_df.resample(freq)['URL'].count()
        this_data_batch['TWEETS_COUNT'] = this_data_batch_count
        this_data_batch['IN_TRADING_HOUR'] = this_data_batch.index.map(lambda x:in_trading_hour(x.time()))
        this_data_batch['BULLISH_COUNT'] = data_df.loc[data_df['CATEGORY'] == 'BULLISH'].resample(freq)['URL'].count()
        this_data_batch['BEARISH_COUNT'] = data_df.loc[data_df['CATEGORY'] == 'BEARISH'].resample(freq)['URL'].count()
        this_data_batch['NEUTRAL_COUNT'] = data_df.loc[data_df['CATEGORY'] == 'NEUTRAL'].resample(freq)['URL'].count()
        this_data_batch.to_sql(con=mysql_con.engine, if_exists='replace', index=True, name=f'{stocks}_{freq}',
                  chunksize=500)
    freq = '1D'
    print(f"getting {freq} in trading hour bucket data...")
    data_df['IN_TRADING_HOUR'] = data_df.index.map(lambda x: in_trading_hour(x.time()))
    this_data_batch = data_df.loc[data_df['IN_TRADING_HOUR']].resample(freq).sum()
    this_data_batch['TWEETS_COUNT'] = this_data_batch_count
    this_data_batch.to_sql(con=mysql_con.engine, if_exists='replace', index=True, name=f'{stocks}_{freq}_IN_TRADING_HOUR',
                           chunksize=500)
    print(f"getting {freq} out trading hour bucket data...")
    this_data_batch = data_df.loc[data_df['IN_TRADING_HOUR'] == False].resample(freq).sum()
    this_data_batch['TWEETS_COUNT'] = this_data_batch_count


