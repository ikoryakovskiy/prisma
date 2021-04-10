# -*- coding: utf-8 -*-
import pandas as pd


class Screener:
    def __init__(self, rules):
        self.rules = rules

    def __call__(self, table, instruments):
        for rule in self.rules:
            rule(table, instruments)

        total_score = pd.DataFrame([0]*len(table), columns=["TotalScore"], index=table.index)
        for column in table.columns:
            if "Score" in column:
                total_score["TotalScore"] += table[column]
        table["TotalScore"] = total_score["TotalScore"]