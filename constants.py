#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  3 22:26:15 2021

@author: ivan
"""
import os

CACHE_DIR  = os.path.join("interface", "cache")
WALLET_FILE = os.path.join("interface", "wallet.json")


SECTORS_MAP = {
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

MAX_SECTORS = 3

# Standard deviation for filtering at specific time back (in days)
WINDOW_MULTIPLIER = 3
STD_DAYS_5Y = 60  # 12 month window
STD_DAYS_1Y = 12  # 2.4 month window
STD_DAYS_3M = 3   # 18 days window
STD_DAYS_1M = 1   # 6 days window
