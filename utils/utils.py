import pycountry
import pandas as pd


def find_name(instruments, query):
    if instruments is not None:
        if isinstance(instruments, list):
            all_keys = instruments[0].data.keys()
        elif isinstance(instruments, pd.DataFrame):
            all_keys = instruments.columns
        min_distance = float("inf")
        query = query.lower()

        for key in all_keys:
            if query in key.lower():
                distance = len(key) - len(query)
                if distance < min_distance:
                    min_distance = distance
                    name = key

        return name


def convert_countries_to_codes(countries):
    if countries and isinstance(countries, dict):
        codes = {}
        for name, weight in countries.items():
            matches = pycountry.countries.search_fuzzy(name)
            if not matches:
                raise ValueError
            codes[matches[0].alpha_2] = weight
        return codes
    elif countries and isinstance(countries, list):
        codes = []
        for name in countries:
            matches = pycountry.countries.search_fuzzy(name)
            if not matches:
                raise ValueError
            codes.append(matches[0].alpha_2)
        return codes
    return {}


def percent_to_float(x):
    return float(x.strip("%")) / 100


def none_if_zero(x):
    return x if x != 0 else None


def read_dict(data, names, none_to_zero=True):
    if not names:
        return none_if_zero(data) if none_to_zero else data
    if names[0] in data:
        return read_dict(data[names[0]], names[1:], none_to_zero=none_to_zero)
    return 0 if none_to_zero else None
