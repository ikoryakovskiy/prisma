import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

from prisma.interfaces import (
    RapidApiStatisticsInterface,
    YahooFinanceHistoryInterface,
    FmpCountryInterface,
)
from prisma.wrappers import ToMillions, Percent
from constants import (
    SECTORS_MAP,
    MAX_SECTORS,
    STD_DAYS_1M,
    STD_DAYS_3M,
    STD_DAYS_1Y,
    STD_DAYS_5Y,
    WINDOW_MULTIPLIER,
)
from prisma.utils import Gaussian, convert_to_codes


class DataProcessor:
    def get_history_span(self):
        end_date = date.today()
        half_window = WINDOW_MULTIPLIER * STD_DAYS_5Y
        start_date = end_date - relativedelta(years=5) - relativedelta(days=half_window)
        return start_date, end_date

    def append(self, where, what):
        pass

    def convert_to_area_codes(self, countries):
        pass


class ETF(DataProcessor):
    def __init__(self, symbol, countries=None, industries=None):
        super().__init__()
        self.symbol = symbol

        istat = RapidApiStatisticsInterface()
        self.stat, self.sectors = istat.pull(self.symbol, "US")

        ihistory = YahooFinanceHistoryInterface()
        start_date, end_date = self.get_history_span()
        self.price = ihistory.pull(self.symbol, "US", start_date, end_date)

        icountries = FmpCountryInterface()
        self.countries = icountries.pull(self.symbol, "US")

        # append user-defined knowledge
        self.append(self.sectors, industries)
        self.convert_to_area_codes(self.countries)
        self.convert_to_area_codes(countries)
        self.append(self.countries, countries)

        self.process_statistics(stat, symbol, top_countries, industries)

        hist = self.ihistory.get(symbol, start_date, end_date)

        self.process_history(hist, symbol)

    def process_statistics(self, stat, symbol, top_countries, industries):
        pass

    def get_sectors(self, stat, industries):
        sectors = {}
        for holding_info in stat["topHoldings"]["sectorWeightings"]:
            for sector in holding_info:
                sectors[sector] = holding_info[sector]["raw"]
        sectors = pd.DataFrame.from_dict(sectors, orient="index", columns=["weight"])
        sectors = sectors.rename(index=SECTORS_MAP)
        top_sectors = sectors.nlargest(MAX_SECTORS, "weight")
        top_sectors = top_sectors[top_sectors.weight > 0.05]

        top_sectors_encoded = industries.copy()
        if len(top_sectors) == 1:
            top_sectors_encoded.append(top_sectors.index[0])
        else:
            for sector, row in top_sectors.iterrows():
                weight = row["weight"]
                weight = f"{weight:.1f}".strip("0")
                top_sectors_encoded.append(f"{sector}{weight}")

        return sectors, " ".join(top_sectors_encoded[:MAX_SECTORS])

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + relativedelta(days=n)

    def gaussian_filter(self, price, mean, std):
        half_window = WINDOW_MULTIPLIER * std
        start_date = mean - relativedelta(days=half_window)
        end_date = mean + relativedelta(days=half_window)

        x = -half_window
        g = Gaussian(mean=0, std=std)
        norm = 0
        filtered_price = 0
        for day in self.daterange(start_date, end_date):
            x += 1
            if str(day) in price.index:
                p = price[str(day)]
                c = g(x)
                filtered_price += p * c
                norm += c
        return filtered_price / norm

    def process_history(self, close_price):
        back_5y = date.today() - relativedelta(years=5)
        back_1y = date.today() - relativedelta(years=1)
        back_3m = date.today() - relativedelta(month=3)
        back_1m = date.today() - relativedelta(month=1)
        today = date.today()

        dates = [back_1m, back_3m, back_1y, back_5y]
        stds = [STD_DAYS_1M, STD_DAYS_3M, STD_DAYS_1Y, STD_DAYS_5Y]
        names = ["1M, %", "3M, %", "1Y, %", "5Y, %"]
        months = [1, 3, 12, 60]
        for m, day, std, name in zip(months, dates, stds, names):
            price_old = self.gaussian_filter(close_price, day, std)
            price_today = self.gaussian_filter(close_price, today, std)
            change = (price_today - price_old) / price_old
            if m > 12:
                change *= 12 / m
            self.data[name] = Percent(change, decimal_digits=1)
