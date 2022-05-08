from dotenv import load_dotenv
import os
from binance.client import Client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# symbol = "ETHUSDT"
# interval = "1d"

class DataLoader():
    
    def __init__(self):
        load_dotenv()
        self.client = Client(api_key = os.getenv('API_KEY'), api_secret=os.getenv('SECRET_KEY'), tld="com", testnet=True)
        #self.earliest_timestamp = self.client._get_earliest_valid_timestamp(symbol=self.symbol, interval=self.interval)

    def get_history(self, symbol, interval, start = None, end=None):
        # print(self.client.get_account_status())
        # print(self)
        bars = self.client.get_historical_klines(symbol = symbol, interval=interval, start_str=start,end_str = end, limit=1000)
        df = pd.DataFrame(bars)
        df["Date"] = pd.to_datetime(df.iloc[:,0], unit="ms")
        df.columns = ["Open time", "Open","High", "Low", "Close", "Volume", "Close Time", "Quote Asset Volume", "Number of trades", "Taker Buy Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date"]
        df = df[["Date", "Open", "High", "Low", "Close","Volume"]].copy()
        df.set_index("Date", inplace=True)
        for column in df.columns:
            df[column]=pd.to_numeric(df[column], errors = "coerce")
        return df