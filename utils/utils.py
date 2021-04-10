#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr  4 09:04:21 2021

@author: ivan
"""
import math
import pycountry
import pandas as pd


class Gaussian:
    def __init__(self, mean, std):
        self.mean = mean
        self.sq_std2 = 2 * (std ** 2)
        self.norm = math.sqrt(2 * math.pi) * std

    def __call__(self, x):
        return math.e ** ( - ((x - self.mean) ** 2) / self.sq_std2 ) / self.norm


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