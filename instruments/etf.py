#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

from finance.interfaces import RapidApiStatisticsInterface, YahooFinanceHistoryInterface, FmpCountryInterface
from wrappers import ToMillions, Percent
from constants import SECTORS_MAP, MAX_SECTORS, STD_DAYS_1M, STD_DAYS_3M, STD_DAYS_1Y, STD_DAYS_5Y, WINDOW_MULTIPLIER
from utils import Gaussian, convert_to_codes



class ETF:
    def __init__(self, symbol, top_countries=None, industries=None):
        super().__init__()
        self.symbol = symbol

        self.istat = RapidApiStatisticsInterface()
        self.ihistory = YahooFinanceHistoryInterface()
        self.icountries = FmpCountryInterface()

        stat = self.istat.get(symbol)

        self.process_statistics(stat, symbol, top_countries, industries)

        end_date = date.today()
        half_window = WINDOW_MULTIPLIER * STD_DAYS_5Y
        start_date = end_date  - relativedelta(years=5) - relativedelta(days=half_window)
        hist = self.ihistory.get(symbol, start_date, end_date)

        self.process_history(hist, symbol)

    def process_statistics(self, stat, symbol, top_countries, industries):
        holdings = stat["topHoldings"]["equityHoldings"]
        key_statistics = stat["defaultKeyStatistics"]
        profile = stat["fundProfile"]

        self.data["Name"] = stat["quoteType"]["shortName"]
        self.data["P/E"] = holdings["priceToEarnings"]["raw"]
        self.data["P/S"] = holdings["priceToSales"]["raw"]
        self.data["Yield, %"] = Percent(key_statistics["yield"]["raw"], decimal_digits=1)
        self.data["Volume"] = ToMillions(stat["price"]["averageDailyVolume3Month"]["raw"])
        self.data["TER, %"] = Percent(
            profile["feesExpensesInvestment"]["annualReportExpenseRatio"]["raw"], decimal_digits=2
        )

        industries = industries or []
        sectors, self.data["Top sectors"] = self.get_sectors(stat, industries)

        self.industries = industries
        self.sectors = sectors.to_dict()["weight"]

        self.country_codes = convert_to_codes(top_countries)
        self.data["Top countries"] = " ".join(self.country_codes[:MAX_SECTORS])

    def get_sectors(self, stat, industries):
        sectors = {}
        for holding_info in stat["topHoldings"]["sectorWeightings"]:
            for sector in holding_info:
                sectors[sector] = holding_info[sector]["raw"]
        sectors = pd.DataFrame.from_dict(sectors, orient="index", columns=["weight"])
        sectors = sectors.rename(index=SECTORS_MAP)
        top_sectors = sectors.nlargest(MAX_SECTORS, "weight")
        top_sectors =  top_sectors[top_sectors.weight > 0.05]

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

        x = - half_window
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


    def process_history(self, hist, symbol):
        close_price = hist["Historical Prices"]["Close"]

        back_5y = date.today() - relativedelta(years=5)
        back_1y = date.today() - relativedelta(years=1)
        back_3m = date.today() - relativedelta(month=3)
        back_1m = date.today() - relativedelta(month=1)
        today = date.today()

        dates = [back_1m, back_3m, back_1y, back_5y]
        stds = [STD_DAYS_1M, STD_DAYS_3M, STD_DAYS_1Y, STD_DAYS_5Y]
        names = ["1M, %", "3M, %", "1Y, %", "5Y, %"]
        months = [1, 3,  12, 60]
        for m, day, std, name in zip(months, dates, stds, names):
            price_old = self.gaussian_filter(close_price, day, std)
            price_today = self.gaussian_filter(close_price, today, std)
            change = (price_today - price_old) / price_old
            if m > 12:
                change *= 12 / m
            self.data[name] = Percent(change, decimal_digits=1)

