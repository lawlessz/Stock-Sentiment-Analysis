# this is just a link to start twitterListener/start_tweets_listener.py
from twitterListener.listener import *
try:
    if __name__ == '__main__':
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s')
        main()
except KeyboardInterrupt:
    sys.exit()
except tweepy.TweepError as e:
    print('Below is the printed exception')
    print(e)
    if '401' in e:
        # not sure if this will even work
        print('Below is the response that came in')
        print(e)
        sleep(60)
        pass
    else:
        email_worker.sendEmailMIME(['luoy2@hotmail.com'], 'CS498 Tweets Collector Unhandled Tweepy Exception', str(e))
        print(e)
        # raise an exception if another status code was returned, we don't like other kinds
        raise e
except Exception as e:
    email_worker.sendEmailMIME(['luoy2@hotmail.com'], 'CS498 Tweets Collector Unhandled Exception', str(e))
    print('Unhandled exception')
    raise e

