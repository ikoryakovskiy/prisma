import os
import requests
import json
from functools import partial
from yahoofinance import HistoricalPrices
from urllib.request import urlopen
import pandas as pd
from collections import OrderedDict

from prisma.interfaces.cache import Cache
from prisma.interfaces.wallet import Wallet
from prisma.utils import convert_countries_to_codes, percent_to_float
from prisma.constants import WALLET_FILE, RAPIDAPI_SECTORS_MAP


class Interface:
    def __init__(self):
        super().__init__()
        self.wallet = Wallet(WALLET_FILE)
        self.cache = Cache()

    def get_response(self, name, symbol, region, request_fn):
        query = {"symbol": symbol, "region": region}
        cache_filename = self.cache.get_filename(query, name)
        if os.path.isfile(cache_filename):
            return self.cache.load_cahced_response(cache_filename)
        else:
            data = request_fn(query)
            self.cache.cache_response(data, cache_filename)
            return data


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


class RapidApiStatisticsInterface(RapidApiInterface):
    def __init__(self, name="rapidapi_statistics"):
        super().__init__()
        self.name = name
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-statistics"
        self.request_fn = partial(self.request, url)

    def pull(self, symbol, region):
        response = self.get_response(self.name, symbol, region, self.request_fn)

        # Single-number statistics
        stat = OrderedDict()
        stat["Symbol"] = symbol
        stat["Name"] = response["quoteType"]["shortName"]
        stat["P/E"] = response["topHoldings"]["equityHoldings"]["priceToEarnings"]["raw"]
        stat["P/S"] = response["topHoldings"]["equityHoldings"]["priceToSales"]["raw"]
        stat["Yield"] = response["defaultKeyStatistics"]["yield"]["raw"]
        stat["Volume"] = response["price"]["averageDailyVolume3Month"]["raw"]
        stat["TER"] = response["fundProfile"]["feesExpensesInvestment"]["annualReportExpenseRatio"]["raw"]

        # Sectors and percentages
        sectors = {}
        for holding_info in response["topHoldings"]["sectorWeightings"]:
            for sector in holding_info:
                sectors[sector] = holding_info[sector]["raw"]
        sectors = {RAPIDAPI_SECTORS_MAP[name]: weight for name, weight in sectors.items()}
        return stat, sectors


class RapidApiHistoryInterface(RapidApiInterface):
    def __init__(self, name="rapidapi_history"):
        super().__init__()
        self.name = name
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v3/get-historical-data"
        self.request_fn = partial(self.request, url)

    def pull(self, symbol, region):
        # not tested
        pass


class YahooFinanceHistoryInterface(Interface):
    def __init__(self, name="yfinance_history"):
        super().__init__()
        self.name = name

    def request(self, start_date, end_date, query):
        req = HistoricalPrices(query["symbol"], start_date=start_date, end_date=end_date)
        return req.to_dfs()

    def send_request(self, symbol, region, start_date, end_date):
        request_fn = partial(self.request, start_date, end_date)
        return self.get_response(self.name, symbol, region, request_fn=request_fn)

    def pull(self, symbol, region, start_date, end_date):
        response = self.send_request(symbol, "US", start_date, end_date)
        close_price = response["Historical Prices"]["Close"]
        return close_price


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

    def pull(self, symbol, region):
        response = self.get_response(self.name, symbol, region, request_fn=self.request)
        countries = {}
        for item in response:
            name = item["country"]
            weight = percent_to_float(item["weightPercentage"])
            countries[name] = weight
        return convert_countries_to_codes(countries)
        # return pd.DataFrame.from_dict(countries, orient="index", columns=["weight"])
