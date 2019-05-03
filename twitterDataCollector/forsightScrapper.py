# -*- coding: utf-8 -*-

import requests
import pandas as pd
import datetime
import mysqlClient
import time
from configparser import RawConfigParser
import pymysql
import sqlalchemy

['AAPL', 'AMD', 'AMZN', 'FB', 'GOOG', 'MSFT']

NAME = 'MSFT'

mysql_con = mysqlClient.mysql_connection()
mysql_con.init_engine('tweets')
# engine = sqlalchemy.create_engine("mysql+pymysql://{user}:{pass}@{host}/tweets?charset=utf8mb4")
total_row = 0
config = RawConfigParser()
config.read('credentials/config.ini')

with requests.Session() as s:
    payload = {'username': config['forsight']['username'], 'password': config['forsight']['password'], 'remember-me': 'on'}
    url = 'https://forsight.crimsonhexagon.com/ch/login'
    p = s.post(url, data=payload)
    # print(p.text)

    for date in pd.date_range('2019-04-01', '2019-04-30'):
        from_date = str(date)[:10]
        to_date = str(date + datetime.timedelta(days=1))[:10]
        url = f"https://forsight.crimsonhexagon.com/ch/api/monitor/9926354559/postlist/bulkexport?monitorId=17244489159&startDate={from_date}&endDate={to_date}"
        # An authorised request.
        r = s.get(url)
        # print(r.text)
        file_name = f'twitterDataCollector/data/chunck_{from_date}_{to_date}.xls'
        open(file_name, 'wb').write(r.content)
        df = pd.read_excel(file_name, skiprows=1)
        df.columns = ['GUID', 'DATETIME', 'URL', 'CONTENTS', 'AUTHOR', 'NAME', 'COUNTRY', 'STATE/REGION',
                      'CITY/URBAN_AREA', 'CATEGORY', 'EMOTION', 'SOURCE', 'GENDER', 'POSTS', 'FOLLOWERS', 'FOLLOWING',
                      'POST_TITLES', 'POST_TYPE', 'IMAGE_URL', 'BRAND']
        # df['NAME']=df['NAME'].apply(lambda x: bytes(x, 'utf-8').decode('utf-8', 'ignore'))
        print(f"length of data from {from_date} to {to_date} is {len(df)}.")
        assert len(df) < 9999

        df.to_sql(con=mysql_con.engine, if_exists='append', index=False, name=NAME)
        # df.to_sql(con=engine, if_exists='append', index=False, name='MSFT',
        #           chunksize=500)
        total_row += len(df)
        time.sleep(1)


