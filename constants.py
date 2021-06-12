import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = "data"
CACHE_DIR = os.path.join(PROJECT_DIR, DATA_DIR, "cache")
WALLET_FILE = os.path.join(PROJECT_DIR, DATA_DIR, "wallet.json")


RAPIDAPI_SECTORS_MAP = {
    "realestate": "R",
    "consumer_cyclical": "CD",
    "basic_materials": "M",
    "consumer_defensive": "CS",
    "technology": "T",
    "communication_services": "C",
    "financial_services": "F",
    "utilities": "U",
    "industrials": "I",
    "energy": "E",
    "healthcare": "H",
}


def format_as_million(num):
    if num is not None:
        return f"{num/1000000:.2f}M"


def format_as_percent(num, decimal_digits=1):
    if num is not None:
        return round(num * 100, decimal_digits)


HEADER_FORMAT = {
    "Yield": {
        "header": "{}, %".format,
        "data": format_as_percent,
    },
    "Volume": {
        "data": format_as_million,
    },
    "TER": {
        "header": "{}, %".format,
        "data": lambda x: format_as_percent(x, decimal_digits=2),
    },
    "1M": {
        "header": "{}, %".format,
        "data": format_as_percent,
    },
    "3M": {
        "header": "{}, %".format,
        "data": format_as_percent,
    },
    "1Y": {
        "header": "{}, %".format,
        "data": format_as_percent,
    },
    "5Y": {
        "header": "{}, %".format,
        "data": format_as_percent,
    },
}

SECTORS_COUNTRIES_DISPLAY_NUM = 3  # In counts
SECTORS_COUNTRIES_MIN_WEIGHT = 0.1  # In %

# Standard deviation for filtering at specific time back (in days)
WINDOW_MULTIPLIER = 1
STD_DAYS_5Y = 60  # 121 * WINDOW_MULTIPLIER days window
STD_DAYS_1Y = 12  # 25 * WINDOW_MULTIPLIER days window
STD_DAYS_3M = 3  # 7 * WINDOW_MULTIPLIER days window
STD_DAYS_1M = 1  # 3 * WINDOW_MULTIPLIER days window
