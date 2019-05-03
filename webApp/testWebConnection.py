import requests
import time
import datetime

i=1
start_time = datetime.datetime.now()
while 1:
    print(datetime.datetime.now(), f'trying request time {i}')
    result = requests.get('http://usdb.yikangquant.club:3000/#')
    i = i+1
    time.sleep(1)