import argparse
from ruamel.yaml import YAML
from pathlib import Path
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


# Useful information
# https://www.etfbreakdown.com/

# Useful APIs
# https://financialmodelingprep.com/developer/docs/dashboard
# https://finnhub.io/docs/api/etfs-country-exposure
# https://etf-data.com/


class Portfolio:
    def __init__(self, filename, update_missing):
        path = Path(filename)
        yaml = YAML(typ="safe")
        config = yaml.load(path)
        assets = self.reload_and_update(config, update_missing)
        assert assets, "Assets were not found"
        self.format_and_store(assets)

    def reload_and_update(self, asset_config, update_missing):
        assets = []
        asset_classes = {"ETF": ETF}
        for asset_class, asset_constructor in asset_classes.items():
            config = asset_config.get(asset_class)
            if config:
                for asset in config:
                    if isinstance(asset, str):
                        assets.append(asset_constructor(asset, update_missing))
                    elif isinstance(asset, dict):
                        for name, kwargs in asset.items():
                            assets.append(asset_constructor(name, update_missing, **kwargs))
        return assets

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


# def analyze_portfolio():
# instruments = convert_to_dict(instruments)

# sectors_rule = SectorRule(
#     strong_growing=["F", "I", "Semi"],
#     fair_growing=["CS", "EV", "H", "CD", "Comod"],
#     fair_decline=["M", "E", "R"],
#     strong_decline=["T"],
# )

# countries_rule = CountryRule(
#     strong_growing=["china", "us",  "hk"],
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prisma is a software tool that helps you to disintegrate and analyze stocks on a market."
    )
    parser.add_argument("assets", help="A protfolio file with assets to open")
    parser.add_argument(
        "--update-missing",
        action="store_true",
        default=False,
        help="Update assets that are missing in the database records"
        "(for all existing assets use the latest available record).",
    )
    args = parser.parse_args()

    portfolio = Portfolio(args.assets, args.update_missing)
    portfolio.display(by="Symbol")
