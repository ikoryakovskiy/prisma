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


def convert_to_codes(country_names):
    country_codes = []
    for name in country_names:
        codes = pycountry.countries.search_fuzzy(name)
        if not codes:
            raise ValueError
        country_codes.append(codes[0].alpha_2)
    return country_codes