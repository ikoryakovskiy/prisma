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
from prisma.constants import HEADER_FORMAT


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
        self.stat = pd.DataFrame(stat_data).set_index("Symbol")

    def display(self, by=None):
        if by:
            stat = self.stat.sort_values(by=by)
        else:
            stat = self.stat

        headers_new_name = {}
        for header in list(stat):
            if header in HEADER_FORMAT:
                if "data" in HEADER_FORMAT[header]:
                    stat[header] = stat[header].apply(HEADER_FORMAT[header]["data"])
                if "header" in HEADER_FORMAT[header]:
                    headers_new_name[header] = HEADER_FORMAT[header]["header"](header)
        stat.rename(columns=headers_new_name, inplace=True)

        table = tabulate(stat, headers="keys", tablefmt="psql", numalign="right", stralign="right")
        print(table)


# Useful information
# https://www.etfbreakdown.com/


# https://financialmodelingprep.com/developer/docs/dashboard
# https://finnhub.io/docs/api/etfs-country-exposure
# https://etf-data.com/
assets = [
    ETF("IVV"),
    ETF("LIT", industries={"EV": 1}),
    ETF("SOXX", industries={"Semi": 1}),
    #    ETF("XDEV"),
    ETF("VTV"),
    ETF("VBR"),
    ETF("IWN"),
    ETF("RSP"),
    ETF("VFH"),
    ETF("DEM"),
    ETF("KBE"),
    ETF("KRE"),
    ETF("VWO"),
    ETF("CHIQ"),
    ETF("THD"),
    ETF("VNM"),
    ETF("XME"),
    ETF("VAW"),
    #    ETF("EXSA"),
    #    ETF("EXV1"),
    #    ETF("SX7PEX"),
    ETF("DIA"),
    ETF("CQQQ"),
]

portfolio = Portfolio(assets)
portfolio.display(by="Symbol")

# instruments = convert_to_dict(instruments)

# sectors_rule = SectorRule(
#     strong_growing=["F", "I", "Semi"],
#     fair_growing=["CS", "EV", "H", "CD"],
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
