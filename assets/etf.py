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
    SECTORS_COUNTRIES_DISPLAY_NUM,
    SECTORS_COUNTRIES_MIN_WEIGHT,
    STD_DAYS_1M,
    STD_DAYS_3M,
    STD_DAYS_1Y,
    STD_DAYS_5Y,
    WINDOW_MULTIPLIER,
)
from prisma.utils import ConvDateSeries, convert_countries_to_codes


class DataProcessor:
    def get_history_span(self):
        end_date = date.today()
        half_window = WINDOW_MULTIPLIER * STD_DAYS_5Y
        start_date = end_date - relativedelta(years=5) - relativedelta(days=half_window)
        return start_date, end_date

    def append(self, lhs, rhs):
        if rhs:
            for name, weight in rhs.items():
                if name in lhs:
                    lhs[name] = max(lhs[name], weight)
                else:
                    lhs[name] = weight

    def find_top(self, x, nlargest=SECTORS_COUNTRIES_DISPLAY_NUM, min_weight=SECTORS_COUNTRIES_MIN_WEIGHT):
        largest = x.nlargest(nlargest, "weight")
        largest = largest[largest.weight > min_weight]

        top_selection = []
        if len(largest) == 1:
            top_selection.append(largest.index[0])
        else:
            for name, weight in largest.itertuples():
                str_weight = f"{weight:.1f}".strip("0")
                top_selection.append(f"{name}{str_weight}")
        return " ".join(top_selection)

    def filter_price(self, price):
        back_5y = date.today() - relativedelta(years=5)
        back_1y = date.today() - relativedelta(years=1)
        back_3m = date.today() - relativedelta(month=3)
        back_1m = date.today() - relativedelta(month=1)
        today = date.today()

        dates = [back_1m, back_3m, back_1y, back_5y]
        stds = [STD_DAYS_1M, STD_DAYS_3M, STD_DAYS_1Y, STD_DAYS_5Y]
        names = ["1M", "3M", "1Y", "5Y"]
        months = [1, 3, 12, 60]
        price_change = {}
        for m, day, std, name in zip(months, dates, stds, names):
            price_filter = ConvDateSeries()
            price_old = price_filter(price, day, std)
            price_today = price_filter(price, today, std)
            change = (price_today - price_old) / price_old
            if m > 12:
                change *= 12 / m
            price_change[name] = change
        return price_change


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
        self.append(self.countries, convert_countries_to_codes(countries))

        self.stat["Sectors"] = self.find_top(self.sectors)
        self.stat["Countries"] = self.find_top(self.countries)

        price_change = self.filter_price(self.price)
        self.stat.update(price_change)