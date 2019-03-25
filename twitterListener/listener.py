import datetime
import tweepy
import logging
import pandas as pd
from configparser import RawConfigParser

#TODO:
# 1. continuously store json file into local
# 2. make a data writer thread to read stored json file to database
# 3. automatic re-connect twitter listener

import threading
lock = threading.Lock()

# 1. twitter break ->
# 2. sql server break -> queue => pickle to pick up


#https://www.dataquest.io/blog/streaming-data-python/
class StreamListener(tweepy.StreamListener):
    def __init__(self):
        super(StreamListener,self).__init__()
        self.file_name = datetime.datetime.now().strftime("%Y-%m-%d") + '.json'
        self.file_handler = open('tweetsCache/' + self.file_name, 'w+')


    def on_status(self, status):
        result_dict = {
            'description': status.user.description,
            'loc': status.user.location,
            'text': status.text,
            'coords': status.coordinates,
            'name': status.user.screen_name,
            'user_created_at': status.user.created_at,
            'followers': status.user.followers_count,
            'id_str': status.id_str,
            'created_time': status.created_at,
            'retweets': status.retweet_count,
            'bg_color': status.user.profile_background_color,
        }
        print(result_dict)


    def on_error(self, status_code):
        logging.warning(status_code)
        if status_code == 420:
            self.file_handler.close()
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
    stream = tweepy.Stream(auth=api.auth, listener=stream_listener)
    logging.info("starting twitter listener...")
    stream.filter(track=['$' + i for i in get_stock_ticks()], languages=['en'])

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s')
    main()
