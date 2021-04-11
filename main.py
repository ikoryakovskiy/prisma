import pandas as pd
from tabulate import tabulate

from prisma.assets import ETF
from prisma.utils import find_name
from prisma.rules import (
    Screener,
    SectorRule,
    CountryRule,
    PePsRule,
    TerRule,
    DeclineRule,
    LtgRule,
    StgRule,
)


class Portfolio:
    def __init__(self, assets):
        self.format_and_store(assets)

    def format_and_store(self, assets):
        self.countries = {}
        self.sectors = {}
        stat_data = []
        for asset in assets:
            stat_data.append(asset.stat)
            self.countries[asset.symbol] = asset.countries
            self.sectors[asset.symbol] = asset.sectors
        self.stat = pd.DataFrame(stat_data)

    def display(self, by=None):
        if by:
            stat = self.stat.sort_values(by=by).reset_index(drop=True)
        else:
            stat = self.stat
        table = tabulate(stat, headers="keys", tablefmt="psql")
        print(table)


# Useful information
# https://www.etfbreakdown.com/


# https://financialmodelingprep.com/developer/docs/dashboard
# https://finnhub.io/docs/api/etfs-country-exposure
# https://etf-data.com/
assets = [
    ETF("IVV"),
    # ETF("LIT", top_countries=["china", "us", "kr"], industries=["EV"]),
    # ETF("SOXX", top_countries=["us"], industries=["Semi"]),
    # #    ETF("XDEV", top_countries=["us", "japan", "uk"]),
    # ETF("VTV", top_countries=["us"]),
    # ETF("VBR", top_countries=["us"]),
    # ETF("IWN", top_countries=["us"]),
    # ETF("RSP", top_countries=["us"]),
    # ETF("VFH", top_countries=["us"]),
    # ETF("DEM", top_countries=["taiwan", "china", "russia"]),
    # ETF("KBE", top_countries=["us"]),
    # ETF("KRE", top_countries=["us"]),
    # ETF("VWO", top_countries=["china", "taiwan", "india"]),
    # ETF("CHIQ", top_countries=["china"]),
    # ETF("THD", top_countries=["thailand"]),
    # ETF("VNM", top_countries=["vietnam"]),
    # ETF("XME", top_countries=["us"]),
    # ETF("VAW", top_countries=["us"]),
    # #    ETF("EXSA", top_countries=["EU"]),
    # #    ETF("EXV1", top_countries=["EU"]),
    # #    ETF("SX7PEX", top_countries=["EU"]),
    # ETF("DIA", top_countries=["us"]),
    # ETF("CQQQ", top_countries=["china"]),
]

portfolio = Portfolio(assets)
portfolio.display(by="Symbol")

# instruments = convert_to_dict(instruments)

# sectors_rule = SectorRule(
#     strong_growing=["F", "H", "CD", "Semi"],
#     fair_growing=["CS", "EV", "I"],
#     fair_decline=["M", "E", "R"],
#     strong_decline=["T"],
# )

# countries_rule = CountryRule(
#     strong_growing=["china", "us"],
#     fair_growing=[
#         "EU",
#         "russia",
#         "india",
#         "taiwan",
#         "kr",
#         "japan",
#         "uk",
#         "thailand",
#         "vietnam",
#     ],
# )

# screener = Screener(
#     rules=[
#         TerRule(),
#         PePsRule(),
#         countries_rule,
#         sectors_rule,
#         DeclineRule(),
#         LtgRule(),
#         StgRule(),
#     ]
# )

# screener(table, instruments)
# table = table.sort_values(by="TotalScore", ascending=False)

# old_columns = table.columns
# new_columns = [name.replace("Score", "S") for name in old_columns]
# table.rename(columns=dict(zip(old_columns, new_columns)), inplace=True)

# print(table.to_string(index=False))  # , float_format="%.2f"))
