import datetime
import tweepy
import logging
import pandas as pd
import json
from textblob import TextBlob
from configparser import RawConfigParser
from pprint import pprint

# TODO:
# 1. continuously store json file into local -- Done
# 2. make a data writer thread to read stored json file to database
# 3. automatic re-connect twitter listener

import threading

lock = threading.Lock()


# 1. twitter break ->
# 2. sql server break -> queue => pickle to pick up


# https://www.dataquest.io/blog/streaming-data-python/
class StreamListener(tweepy.StreamListener):
    def __init__(self):
        super(StreamListener, self).__init__()
        self.tweets_list = []
        # self.file_handler = open('tweetsCache/tweets', 'w+')
        # self.conn = sqlite3.connect('tweetsCache/tweets.db')
        # check if table exists
        # self.cursor = self.conn.cursor()
        # check_query = "select name from sqlite_master where type = 'table';"
        # self.cursor.execute(check_query)
        # tables = self.cursor.fetchall()
        # if "tweets" not in tables:
        #     self.cursor.execute('''
        #     CREATE TABLE tweets
        #              (description text, loc text, text text, coordinates real, price real)
        #              ''')

    def on_status(self, status):
        # print(type(data))
        try:
            tweets_data = status._json
            try:
                tweets_data['text'] = status.extended_tweet['full_text']
            except AttributeError:
                pass
            sentiment = TextBlob(tweets_data['text']).sentiment
            tweets_data['sentiment'] = {}
            tweets_data['sentiment']['polarity'] = sentiment.polarity
            tweets_data['sentiment']['subjectivity'] = sentiment.subjectivity
            self.tweets_list.append(tweets_data)
            # pprint(tweets_data)
            print(tweets_data['text'], tweets_data['sentiment'])
            if len(self.tweets_list) > 100:
                print("saving cache....")
                now = datetime.datetime.utcnow()
                filename = now.strftime("tweetsCache/%Y%m%dT%H%M%S.json")
                with open(filename, 'w+') as f:
                    json.dump(self.tweets_list, f)
                self.tweets_list = []
            return True
        except BaseException as e:
            print("Error on_status: %s" % str(e))
        return True


    def on_error(self, status_code):
        logging.warning(status_code)
        if status_code == 420:
            # self.file_handler.close()
            # returning False in on_data disconnects the stream
            return False


def get_stock_ticks():
    stock_data = pd.read_csv('high_volume_ticks.csv')
    return [i for i in stock_data['Symbol']]


def main():
    config = RawConfigParser()
    config.read('credentials/config.ini')
    CONSUMER_KEY = config['twitter']['consumer_key']
    CONSUMER_SECRET = config['twitter']['consumer_secret']
    ACCESS_TOEKN_KEY = config['twitter']['access_token_key']
    ACCESS_TOKEN_SECRET = config['twitter']['access_token_secret']

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOEKN_KEY, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    stream_listener = StreamListener()
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener, tweet_mode='extended')
    logging.info("starting twitter listener...")
    stream.filter(track=['$' + i for i in get_stock_ticks()], languages=['en'], is_async=True)



'''
read data:
file_name = 'tweetsCache/20190325T211635.json'
with open(file_name, 'r') as f:
    w=json.load(f)
'''

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    main()
