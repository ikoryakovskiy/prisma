import os
import requests
import json
from functools import partial
import yfinance
from yahoofinance import HistoricalPrices
from urllib.request import urlopen
from collections import OrderedDict
import logging

from prisma.interfaces.cache import Cache
from prisma.interfaces.wallet import Wallet
from prisma.utils import convert_countries_to_codes, percent_to_float, none_if_zero, read_dict
from prisma.constants import WALLET_FILE, RAPIDAPI_SECTORS_MAP


class Interface:
    def __init__(self, name, allow_outdated=False, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.allow_outdated = allow_outdated
        self.wallet = Wallet(WALLET_FILE)
        self.cache = Cache()

    def get_response(self, name, symbol, region, request_fn):
        query = {"symbol": symbol, "region": region}
        cache_filename = self.cache.get_filename(query, name)
        if os.path.isfile(cache_filename):
            # if fresh record is found, then use it
            logging.debug("Reading the up-to-date record %s", cache_filename)
            return self.cache.load_cahced_response(cache_filename)
        elif self.allow_outdated:
            # else try to search the older record if wanted
            older_cache_filename = self.cache.get_older_filename(query, name)
            if older_cache_filename:
                logging.debug("Reading the outdated record %s", older_cache_filename)
                return self.cache.load_cahced_response(older_cache_filename)
        # else ask server for a response
        logging.debug("Requesting %s info about %s %s asset", name, symbol, region)
        data = request_fn(query)
        self.cache.cache_response(data, cache_filename)
        return data


class RapidApiInterface(Interface):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.headers = {
            "x-rapidapi-key": self.wallet.read_key("rapidapi"),
            "x-rapidapi-host": "apidojo-yahoo-finance-v1.p.rapidapi.com",
        }

    def request(self, url, query):
        response = requests.request("GET", url, headers=self.headers, params=query)
        return json.loads(response.text)


class RapidApiStatisticsInterface(RapidApiInterface):
    def __init__(self, **kwargs):
        super().__init__(name="rapidapi_statistics", **kwargs)
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v2/get-statistics"
        self.request_fn = partial(self.request, url)

    def pull(self, symbol, region):
        response = self.get_response(self.name, symbol, region, self.request_fn)

        # Single-number statistics
        stat = OrderedDict()
        stat["Symbol"] = symbol
        shortName = read_dict(response, ["quoteType", "shortName"], none_to_zero=False)
        longName = read_dict(response, ["quoteType", "longName"], none_to_zero=False) or shortName
        # sometimes, long name is shorter :)
        stat["Name"] = shortName if len(shortName) < len(longName) else longName
        stat["P/E"] = read_dict(response, ["topHoldings", "equityHoldings", "priceToEarnings", "raw"])
        stat["P/S"] = read_dict(response, ["topHoldings", "equityHoldings", "priceToSales", "raw"])
        stat["Yield"] = read_dict(response, ["defaultKeyStatistics", "yield", "raw"])
        stat["Volume"] = read_dict(response, ["price", "averageDailyVolume3Month", "raw"])
        stat["TER"] = read_dict(response, ["fundProfile", "feesExpensesInvestment", "annualReportExpenseRatio", "raw"])

        stat["Price"] = read_dict(response, ["price", "regularMarketPrice", "raw"])
        stat["50MA"] = read_dict(response, ["summaryDetail", "fiftyDayAverage", "raw"])
        stat["200MA"] = read_dict(response, ["summaryDetail", "twoHundredDayAverage", "raw"])

        # Sectors and percentages
        sector_weights = read_dict(response, ["topHoldings", "sectorWeightings"])
        sectors = {}
        if sector_weights:
            for holding_info in sector_weights:
                for sector in holding_info:
                    sectors[sector] = holding_info[sector]["raw"]
            sectors = {RAPIDAPI_SECTORS_MAP[name]: weight for name, weight in sectors.items()}
        return stat, sectors


class RapidApiHistoryInterface(RapidApiInterface):
    def __init__(self, **kwargs):
        super().__init__(name="rapidapi_history", **kwargs)
        url = "https://apidojo-yahoo-finance-v1.p.rapidapi.com/stock/v3/get-historical-data"
        self.request_fn = partial(self.request, url)

    def pull(self, symbol, region):
        # not tested
        pass


class YahooFinanceHistoryInterface(Interface):
    def __init__(self, **kwargs):
        """
        yahoofinance package stopped working as of now
        """
        super().__init__(name="yahoofinance_history", **kwargs)

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


class YFinanceHistoryInterface(Interface):
    def __init__(self, **kwargs):
        """
        Alternative package that works
        """
        super().__init__(name="yfinance_history", **kwargs)

    def request(self, start_date, end_date, query):
        return yfinance.download(query["symbol"], start=start_date, end=end_date, progress=False)

    def send_request(self, symbol, region, start_date, end_date):
        request_fn = partial(self.request, start_date, end_date)
        return self.get_response(self.name, symbol, region, request_fn=request_fn)

    def pull(self, symbol, region, start_date, end_date):
        response = self.send_request(symbol, "US", start_date, end_date)
        close_price = response["Close"]
        return close_price


class FmpCountryInterface(Interface):
    def __init__(self, **kwargs):
        super().__init__(name="fmp", **kwargs)
        self.key = self.wallet.read_key("financialmodelingprep")
        self.url = "https://financialmodelingprep.com/api/v3/etf-country-weightings"

    def request(self, query):
        symbol = query["symbol"]
        full_url = f"{self.url}/{symbol}?apikey={self.key}"
        response = urlopen(full_url)
        data = response.read().decode("utf-8")
        return json.loads(data)

    def pull(self, symbol, region):
        """
        Information seem to be outdated, e.g. LIT info is wrong
        """
        response = self.get_response(self.name, symbol, region, request_fn=self.request)
        countries = {}
        for item in response:
            name = item["country"]
            weight = percent_to_float(item["weightPercentage"])
            countries[name] = weight
        return convert_countries_to_codes(countries)
