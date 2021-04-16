# -*- coding: utf-8 -*-
import pandas as pd
from prisma.utils import convert_countries_to_codes, find_name


class TextBasedRule:
    def __init__(
        self,
        strong_growing=None,
        fair_growing=None,
        fair_decline=None,
        strong_decline=None,
    ):
        # TODO: check that no intersection happens
        self.strong_growing = strong_growing or []
        self.fair_growing = fair_growing or []
        self.fair_decline = fair_decline or []
        self.strong_decline = strong_decline or []

    def evaluate_single(self, categories, prediction, multiplier):
        score = 0
        for cat in categories:
            if cat in prediction:
                if isinstance(categories, dict):
                    score += categories[cat]
                else:
                    score += 1.0 / len(categories)
        return multiplier * score

    def evaluate(self, instrument):
        if "sector" in self.name.lower():
            categories = instrument.sectors.copy()
            industries = {ind: 1.0 for ind in instrument.industries}
            categories.update(industries)
        elif "countr" in self.name.lower():
            categories = instrument.country_codes
        score = 0
        score += self.evaluate_single(categories, self.strong_growing, 1)
        score += self.evaluate_single(categories, self.fair_growing, 0.5)
        score += self.evaluate_single(categories, self.fair_decline, -0.5)
        score += self.evaluate_single(categories, self.strong_decline, -1)
        return score

    def process(self, instrument_names, instruments):
        scores = []
        for name in instrument_names:
            score = self.evaluate(instruments[name])
            scores.append(score)
        # return pd.Series(dict(zip(instrument_names, scores)), name=self.name)
        return pd.Series(scores, name=self.name, index=instrument_names.index)

    def __call__(self, table, instruments):
        new_column = self.process(table["Symbol"], instruments)
        table[new_column.name] = new_column


class SectorRule(TextBasedRule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "SectorScore"


class CountryRule(TextBasedRule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "CountryScore"
        self.strong_growing = convert_countries_to_codes(self.strong_growing)
        self.fair_growing = convert_countries_to_codes(self.fair_growing)
        self.fair_decline = convert_countries_to_codes(self.fair_decline)
        self.strong_decline = convert_countries_to_codes(self.strong_decline)


class PePsRule:
    def __init__(self):
        self.name = "PePsScore"

    def process(self, pe, ps):
        new_column = pe.copy()
        new_column.name = self.name
        new_column[(pe < 20) & (ps < 2)] = 0.5
        only_one = ((pe >= 20) & (ps < 2)) | ((pe < 20) & (ps >= 2))
        new_column[only_one] = 0.25
        new_column[(pe >= 20) & (ps >= 2)] = 0.0
        return new_column

    def __call__(self, table, instruments):
        pe = find_name(table, "P/E")
        ps = find_name(table, "P/S")
        new_column = self.process(table[pe], table[ps])
        table[new_column.name] = new_column


class TerRule:
    def __init__(self):
        self.name = "TerScore"

    def process(self, column):
        new_column = column.copy()
        new_column.name = self.name
        new_column[column < 0.2] = 0.2
        new_column[(column >= 0.2) & (column < 0.5)] = 0.1
        new_column[column >= 0.5] = 0.0
        return new_column

    def __call__(self, table, instruments):
        column_name = find_name(table, "ter")
        new_column = self.process(table[column_name])
        table[new_column.name] = new_column


class DeclineRule:
    def __init__(self):
        self.name = "DeclineScore"

    def process(self, m1, m3, y5):
        new_column = pd.DataFrame([0] * len(m1), columns=[self.name], index=m1.index)

        y5_per_month = y5.copy() / 12
        m3_per_month = m3.copy() / 3

        long_term_grouth = y5 > 15  # average groth > 15 %
        m1_m3_below_y5 = (y5_per_month > m3_per_month) | (y5_per_month > m1)
        m1_m3_neg = (m1 < 0) & (m3 < 0)

        m1_pos_little_m3_neg = (m1 > 0) & (m3 < 0) & (m1 + m3 < 5)
        m1_pos_much_m3_neg = (m1 > 0) & (m3 < 0) & (m1 + m3 >= 5)

        # temporary decline is a good signal for buying
        new_column[m1_m3_neg & m1_m3_below_y5 & long_term_grouth] = 0.25
        new_column[m1_pos_much_m3_neg & m1_m3_below_y5 & long_term_grouth] = 0.25
        new_column[m1_pos_little_m3_neg & m1_m3_below_y5 & long_term_grouth] = 0.5
        return new_column

    def __call__(self, table, instruments):
        name_1m = find_name(table, "1m")
        name_3m = find_name(table, "3m")
        name_5y = find_name(table, "5y")
        new_column = self.process(table[name_1m], table[name_3m], table[name_5y])
        table[self.name] = new_column


class LtgRule:
    def __init__(self):
        self.name = "LtgScore"

    def process(self, y):
        max_y = y.max()
        return y / max_y

    def __call__(self, table, instruments):
        name_5y = find_name(table, "5y")
        new_column = self.process(table[name_5y])
        table[self.name] = new_column


class StgRule(LtgRule):
    def __init__(self):
        self.name = "StgScore"

    def __call__(self, table, instruments):
        name_1y = find_name(table, "1y")
        new_column = self.process(table[name_1y])
        table[self.name] = new_column
