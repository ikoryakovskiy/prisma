import argparse
from ruamel.yaml import YAML
from pathlib import Path
import pandas as pd
from tabulate import tabulate
import logging

from prisma.assets import ETF
from prisma.utils import find_name
from prisma.interfaces.cache import Cache
from prisma.screener import Screener
from prisma.constants import HEADER_FORMAT

logging.basicConfig(level=logging.DEBUG)


# Useful information
# https://www.etfbreakdown.com/

# Useful APIs
# https://financialmodelingprep.com/developer/docs/dashboard
# https://finnhub.io/docs/api/etfs-country-exposure
# https://etf-data.com/


class Portfolio:
    def __init__(self, settings_file, assets_file, allow_outdated):
        self.settings = self.read_yaml(settings_file)
        assets_config = self.read_yaml(assets_file)
        assets = self.reload_and_update(assets_config, allow_outdated)
        assert assets, "Assets were not found"
        self.format_and_store(assets)

    def read_yaml(self, filename):
        path = Path(filename)
        yaml = YAML(typ="safe")
        return yaml.load(path)

    def reload_and_update(self, asset_config, allow_outdated):
        assets = []
        asset_classes = {"ETF": ETF}
        for asset_class, asset_constructor in asset_classes.items():
            config = asset_config.get(asset_class)
            if config:
                for asset in config:
                    if isinstance(asset, str):
                        assets.append(asset_constructor(asset, allow_outdated))
                    elif isinstance(asset, dict):
                        for name, kwargs in asset.items():
                            assets.append(asset_constructor(name, allow_outdated, **kwargs))
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
        stat = self.stat.copy()

        if by:
            stat = stat.sort_values(by=by)

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prisma is a software tool that helps you to disintegrate and analyze stocks on a market."
    )
    parser.add_argument("assets", help="A protfolio file with assets to open")
    parser.add_argument(
        "--allow-outdated", action="store_true", default=False, help="Allow using outdated asset records"
    )
    parser.add_argument("--clean-cache", action="store_true", default=False, help="Remove all outdated records")
    args = parser.parse_args()

    if args.clean_cache:
        Cache().clean()

    portfolio = Portfolio("settings.yaml", args.assets, args.allow_outdated)

    screener = Screener(rules=portfolio.settings["Rules"])
    asset_scores = screener(portfolio)

    portfolio.stat = portfolio.stat.reindex(asset_scores.index)
    # portfolio.stat = portfolio.stat.head(15)
    # asset_scores = asset_scores.head(15)
    portfolio.display()

    table = tabulate(asset_scores, headers="keys", tablefmt="psql", numalign="right", stralign="right")
    print(table)
