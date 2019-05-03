import operator
import mysqlClient
import pandas as pd
import spacy
from pathlib import Path
import sqlalchemy
# spacy.prefer_gpu()
model_path = Path('tweetsClassifier/spacyTrainingModel')
# test the saved model
print("Loading from", model_path)
nlp_model = spacy.load(model_path)


# mysql_con.init_engine('tweets')
# engine = mysql_con.engine


for stocks in ['AAPL', 'AMD', 'AMZN', 'FB', 'GOOG','MSFT']:
    print(f'getting {stocks} tweets...')
    mysql_con = mysqlClient.mysql_connection()
    data = mysql_con.select_query(f"SELECT * from tweets.{stocks};")
    tweets_df = pd.DataFrame(list(data), columns=['GUID', 'DATETIME', 'URL', 'CONTENTS', 'AUTHOR', 'NAME', 'COUNTRY', 'STATE/REGION',
                      'CITY/URBAN_AREA', 'CATEGORY', 'EMOTION', 'SOURCE', 'GENDER', 'POSTS', 'FOLLOWERS', 'FOLLOWING',
                      'POST_TITLES', 'POST_TYPE', 'IMAGE_URL', 'BRAND', 'BULLISH', 'BEARISH', 'NEUTRAL'])
    print(f"numbers of tweets: {len(tweets_df)}")
    tweets_df['BULLISH'] = tweets_df['CONTENTS'].apply(lambda x:nlp_model(x).cats['Bullish'])
    print("evaluating bullish score...")
    tweets_df['BEARISH'] = tweets_df['CONTENTS'].apply(lambda x: nlp_model(x).cats['Bearish'])
    print("evaluating bearish score...")
    tweets_df['NEUTRAL'] = tweets_df['CONTENTS'].apply(lambda x: nlp_model(x).cats['Neutral'])
    print("evaluating neutral score...")
    mysql_con = mysqlClient.mysql_connection()
    mysql_con.init_engine('tweets_features')
    tweets_df.to_sql(con=mysql_con.engine, if_exists='append', index=False, name=f'{stocks}_CLASSIFIED',
              chunksize=500)
