# -*- coding: utf-8 -*-
import pandas as pd
from prisma.utils import convert_countries_to_codes, find_name


class Rule:
    def __init__(self, name=""):
        self.name = name


class TextBasedRule(Rule):
    def __init__(
        self,
        strong_growing=None,
        fair_growing=None,
        fair_decline=None,
        strong_decline=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        # TODO: check that no intersection happens
        self.strong_growing = strong_growing or []
        self.fair_growing = fair_growing or []
        self.fair_decline = fair_decline or []
        self.strong_decline = strong_decline or []

    def evaluate_single(self, data, prediction, multiplier):
        score = 0
        for categoty in data:
            if categoty in prediction:
                if isinstance(data, dict):
                    score += data[categoty]
                else:
                    score += 1.0 / len(data)
        return multiplier * score

    def evaluate(self, data):
        score = 0
        score += self.evaluate_single(data, self.strong_growing, 1)
        score += self.evaluate_single(data, self.fair_growing, 0.5)
        score += self.evaluate_single(data, self.fair_decline, -0.5)
        score += self.evaluate_single(data, self.strong_decline, -1)
        return score

    def calculate_scores(self, symbols, data):
        scores = []
        for symbol in symbols:
            score = self.evaluate(data[symbol])
            scores.append(score)
        return pd.Series(scores, name=self.name, index=symbols)


class SectorRule(TextBasedRule):
    def __init__(self, **kwargs):
        super().__init__(name="SectorScore", **kwargs)

    def __call__(self, portfolio):
        symbols = portfolio.stat.index
        return self.calculate_scores(symbols, portfolio.sectors)


class CountryRule(TextBasedRule):
    def __init__(self, **kwargs):
        super().__init__(name="CountryScore", **kwargs)
        self.strong_growing = convert_countries_to_codes(self.strong_growing)
        self.fair_growing = convert_countries_to_codes(self.fair_growing)
        self.fair_decline = convert_countries_to_codes(self.fair_decline)
        self.strong_decline = convert_countries_to_codes(self.strong_decline)

    def __call__(self, portfolio):
        symbols = portfolio.stat.index
        return self.calculate_scores(symbols, portfolio.countries)


class PePsRule(Rule):
    def __init__(self, **kwargs):
        super().__init__(name="PePsScore", **kwargs)

    def process(self, pe, ps):
        new_column = pd.Series(0, index=pe.index, name=self.name)
        new_column[(pe < 20) & (ps < 2)] = 0.5
        only_one = ((pe >= 20) & (ps < 2)) | ((pe < 20) & (ps >= 2))
        new_column[only_one] = 0.25
        new_column[(pe >= 20) & (ps >= 2)] = 0.0
        return new_column

    def __call__(self, portfolio):
        pe = portfolio.stat["P/E"]
        ps = portfolio.stat["P/S"]
        return self.process(pe, ps)


class TerRule(Rule):
    def __init__(self, **kwargs):
        super().__init__(name="TerScore", **kwargs)

    def process(self, column):
        new_column = pd.Series(0, index=column.index, name=self.name)
        new_column[column < 0.2] = 0.2
        new_column[(column >= 0.2) & (column < 0.5)] = 0.1
        new_column[column >= 0.5] = 0.0
        return new_column

    def __call__(self, portfolio):
        data = portfolio.stat["TER"]
        return self.process(data)


class DeclineRule(Rule):
    def __init__(self, **kwargs):
        super().__init__(name="DeclineScore", **kwargs)

    def process(self, m1, m3, y5):
        new_column = pd.Series(0, index=m1.index, name=self.name)

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

    def __call__(self, portfolio):
        name_1m = portfolio.stat["1M"]
        name_3m = portfolio.stat["3M"]
        name_5y = portfolio.stat["5Y"]
        return self.process(name_1m, name_3m, name_5y)


class LtgRule(Rule):
    def __init__(self, **kwargs):
        super().__init__(name="LtgScore", **kwargs)

    def process(self, y):
        max_y = y.max()
        return y / max_y

    def __call__(self, table, instruments):
        name_5y = find_name(table, "5y")
        new_column = self.process(table[name_5y])
        table[self.name] = new_column


class StgRule(LtgRule):
    def __init__(self, **kwargs):
        super().__init__(name="StgScore", **kwargs)

    def __call__(self, table, instruments):
        name_1y = find_name(table, "1y")
        new_column = self.process(table[name_1y])
        table[self.name] = new_column
