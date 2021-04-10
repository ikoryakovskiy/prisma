#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd

from finance.instruments import ETF
from finance.utils import find_name
from finance.rules import SectorRule, CountryRule, PePsRule, TerRule, DeclineRule, LtgRule, StgRule
from screeners import Screener


def convert_to_table(instruments):
    columns = [
        "symbol", "name", "countries", "sectors", "ter", "P/E", "P/S",
        "volume", "yield", "1M", "3M", "1Y", "5Y"
    ]
    columns = [find_name(instruments, name) for name in columns]

    data = []
    for inst in instruments:
        row = []
        for name in columns:
            row.append(inst.data[name])
        data.append(row)
    return pd.DataFrame(data, columns=columns)

def convert_to_dict(instruments):
    instr = {}
    for instrument in instruments:
        instr[instrument.symbol] = instrument
    return instr

# Useful information
# https://www.etfbreakdown.com/


# https://financialmodelingprep.com/developer/docs/dashboard
# https://finnhub.io/docs/api/etfs-country-exposure
# https://etf-data.com/
instruments = [
    ETF("IVV", top_countries=["us"]),
    ETF("LIT", top_countries=["china", "us", "kr"], industries=["EV"]),
    ETF("SOXX", top_countries=["us"], industries=["Semi"]),
#    ETF("XDEV", top_countries=["us", "japan", "uk"]),
    ETF("VTV", top_countries=["us"]),
    ETF("VBR", top_countries=["us"]),
    ETF("IWN", top_countries=["us"]),
    ETF("RSP", top_countries=["us"]),
    ETF("VFH", top_countries=["us"]),
    ETF("DEM", top_countries=["taiwan", "china", "russia"]),
    ETF("KBE", top_countries=["us"]),
    ETF("KRE", top_countries=["us"]),
    ETF("VWO", top_countries=["china", "taiwan", "india"]),
    ETF("CHIQ", top_countries=["china"]),
    ETF("THD", top_countries=["thailand"]),
    ETF("VNM", top_countries=["vietnam"]),
    ETF("XME", top_countries=["us"]),
    ETF("VAW", top_countries=["us"]),
#    ETF("EXSA", top_countries=["EU"]),
#    ETF("EXV1", top_countries=["EU"]),
#    ETF("SX7PEX", top_countries=["EU"]),
    ETF("DIA", top_countries=["us"]),
    ETF("CQQQ", top_countries=["china"]),
]

table = convert_to_table(instruments)
#print(table.sort_values(by="Symbol").to_string(index=False))

instruments = convert_to_dict(instruments)

sectors_rule = SectorRule(
    strong_growing = ["F", "H", "CD", "Semi"],
    fair_growing = ["CS", "EV", "I"],
    fair_decline = ["M", "E", "R"],
    strong_decline = ["T"],
)

countries_rule = CountryRule(
    strong_growing = ["china", "us"],
    fair_growing = ["EU", "russia", "india", "taiwan", "kr", "japan", "uk", "thailand", "vietnam"],
)

screener = Screener(
    rules = [
        TerRule(), PePsRule(), countries_rule, sectors_rule,
        DeclineRule(), LtgRule(), StgRule()
    ]
)

screener(table, instruments)
table = table.sort_values(by="TotalScore", ascending=False)

old_columns = table.columns
new_columns = [name.replace("Score", "S") for name in old_columns]
table.rename(columns=dict(zip(old_columns, new_columns)), inplace = True)

print(table.to_string(index=False)) #, float_format="%.2f"))



