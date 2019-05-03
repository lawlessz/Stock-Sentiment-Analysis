import json
import mysqlClient

db_helper = mysqlClient.mysql_connection()
for stock in ['AAPL', 'AMD', 'AMZN', 'FB', 'GOOG', 'MSFT']:
    try:
        file_path = f'stockDataCollector/5m_data/{stock}2.json'
        with open(file_path, 'r') as f:
            data_unload = json.load(f)
            prices = data_unload['Time Series (5min)']
            insert_query = "replace into stock_prices.{} values ".format(stock)
            for k, v in prices.items():
                ts = k
                _open = v['1. open']
                high = v['2. high']
                low = v['3. low']
                _close = v['4. close']
                vol = v['5. volume']
                insert_query += f"('{ts}', {_open}, {high}, {low}, {_close}, {vol}),"
            insert_query = insert_query[:-1]
            insert_query += ';'
            print(insert_query)
            db_helper.commit_query(insert_query)
    except:
        pass
