import os
import requests
import json
from functools import partial
from yahoofinance import HistoricalPrices
from urllib.request import urlopen

from prisma.interfaces.cache import Cache
from prisma.interfaces.wallet import Wallet


class Interface:
    def __init__(self):
        super().__init__()
        self.wallet = Wallet("wallet.json")
        self.cache = Cache()

    def read_write_cache(self, query, filename, request_fn):
        if os.path.isfile(filename):
            return self.cache.load_cahced_responce(filename)
        else:
            data = request_fn(query)
            self.cache.cache_responce(data, filename)
            return data

    def get(self, name, symbol, region, request_fn):
        query = {"symbol": symbol, "region": region}
        filename = self.cache.get_filename(query, name)
        request_fn = request_fn or request_fn
        return self.read_write_cache(query, filename, request_fn)


class RapidApiInterface(Interface):
    def __init__(self):
        super().__init__()
        self.headers = {
            "x-rapidapi-key": self.wallet.read_key("rapidapi"),
            "x-rapidapi-host": "apidojo-yahoo-finance-v1.p.rapidapi.com",
        }

    def request(self, url, query):
        response = requests.request("GET", url, headers=self.headers, params=query)
        return json.loads(response.text)


class RapidApiStatisticsInterface(Interface):
    def __init__(self, name="rapidapi_statistics"):
        super().__init__()
        self.name = name
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-statistics"
        self.request_fn = partial(self.request, url)


class RapidApiHistoryInterface(Interface):
    def __init__(self, name="rapidapi_history"):
        super().__init__()
        self.name = name
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v3/get-historical-data"
        self.request_fn = partial(self.request, url)


class YahooFinanceHistoryInterface(Interface):
    def __init__(self, name="yfinance_history"):
        super().__init__()
        self.name = name

    def request(self, start_date, end_date, query):
        req = HistoricalPrices(
            query["symbol"], start_date=start_date, end_date=end_date
        )
        return req.to_dfs()

    def get(self, symbol, region, start_date, end_date):
        request_fn = partial(self.request, start_date, end_date)
        return super().get(symbol, region, request_fn=request_fn)


class FmpCountryInterface(Interface):
    def __init__(self, name="fmp"):
        super().__init__()
        self.name = name
        self.key = self.wallet.read_key("financialmodelingprep")
        self.url = "https://financialmodelingprep.com/api/v3/etf-country-weightings"

    def request(self, query):
        symbol = query["symbol"]
        full_url = f"{self.url}/{symbol}?apikey={self.key}"
        response = urlopen(full_url)
        data = response.read().decode("utf-8")
        return json.loads(data)
