# -*- coding: utf-8 -*-
import pandas as pd
from prisma.utils import convert_countries_to_codes, find_name


class Rule:
    def __init__(self, name="", weight=1.0):
        self.name = name
        self.weight = weight


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
                score += data[categoty]
                # if isinstance(data, dict):
                #     score += data[categoty]
                # else:
                #     score += 1.0 / len(data)
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
    def __init__(self, name="Sector", **kwargs):
        super().__init__(name=name, **kwargs)

    def __call__(self, portfolio):
        symbols = portfolio.stat.index
        return self.calculate_scores(symbols, portfolio.sectors) * self.weight


class CountryRule(TextBasedRule):
    def __init__(self, name="Country", **kwargs):
        super().__init__(name=name, **kwargs)
        self.strong_growing = convert_countries_to_codes(self.strong_growing)
        self.fair_growing = convert_countries_to_codes(self.fair_growing)
        self.fair_decline = convert_countries_to_codes(self.fair_decline)
        self.strong_decline = convert_countries_to_codes(self.strong_decline)

    def __call__(self, portfolio):
        symbols = portfolio.stat.index
        return self.calculate_scores(symbols, portfolio.countries) * self.weight


class PePsRule(Rule):
    def __init__(self, name="P/E P/S", **kwargs):
        super().__init__(name=name, **kwargs)

    def process_single(self, x, threshold):
        # x_score = pd.Series(0, index=x.index, name=x.name)
        # norm_x = x.copy().fillna(threshold) / threshold
        # idx = norm_x < 1
        # x_score[idx] = 1 - norm_x[idx]
        # return x_score
        return 1 - x / threshold

    def process(self, pe, ps):
        PE_THRESHOLD = 20.0
        PS_THRESHOLD = 2.0

        pe_score = self.process_single(pe, PE_THRESHOLD)
        ps_score = self.process_single(ps, PS_THRESHOLD)

        pe_score = pe_score.fillna(ps_score)
        ps_score = ps_score.fillna(pe_score)
        mean_score = (pe_score + ps_score) / 2.0
        mean_score.name = self.name
        return mean_score

    def __call__(self, portfolio):
        pe = portfolio.stat["P/E"]
        ps = portfolio.stat["P/S"]
        return self.process(pe, ps) * self.weight


class TerRule(Rule):
    def __init__(self, name="TER", **kwargs):
        super().__init__(name=name, **kwargs)

    def process(self, column):
        new_column = pd.Series(0, index=column.index, name=self.name)
        # new_column[column < 0.002] = 0.2
        # new_column[(column >= 0.002) & (column < 0.005)] = 0.1
        # new_column[column >= 0.005] = 0.0
        # return new_column
        idx = column < 0.01
        new_column[idx] = 0.01 - column[idx]
        return new_column * 100 * self.weight

    def __call__(self, portfolio):
        data = portfolio.stat["TER"]
        return self.process(data)


class DeclineRule(Rule):
    def __init__(self, name="Decline score", **kwargs):
        super().__init__(name=name, **kwargs)

    def process(self, m1, m3, y5):
        MINIMUM_EXPECTED_YEARLY_GROUTH = 0.15  # in %
        LARGE_REBOUND_MULTIPLIER = 1.5
        SMALL_REBOUND_MULTIPLIER = 2.0

        new_column = pd.Series(0, index=m1.index, name=self.name)

        y5_per_month = y5.copy() / 12
        m3_per_month = m3.copy() / 3

        long_term_grouth = y5 > MINIMUM_EXPECTED_YEARLY_GROUTH

        m1_m3_below_y5 = (y5_per_month > m3_per_month) | (y5_per_month > m1)
        m1_m3_average = (m3_per_month + m1) / 2
        m1_m3_average[m1_m3_average < 0] = 0

        m1_pos_little_m3_neg = (m1 > 0) & (m3 < 0) & (m1 < 0.05)
        m1_pos_much_m3_neg = (m1 > 0) & (m3 < 0) & (m1 < 0.10)

        # temporary decline is a good signal for buying
        new_column[m1_m3_below_y5 & long_term_grouth] = MINIMUM_EXPECTED_YEARLY_GROUTH - m1_m3_average
        new_column[m1_pos_much_m3_neg & m1_m3_below_y5 & long_term_grouth] = (
            MINIMUM_EXPECTED_YEARLY_GROUTH * LARGE_REBOUND_MULTIPLIER
        )
        new_column[m1_pos_little_m3_neg & m1_m3_below_y5 & long_term_grouth] = (
            MINIMUM_EXPECTED_YEARLY_GROUTH * SMALL_REBOUND_MULTIPLIER
        )
        return new_column / (MINIMUM_EXPECTED_YEARLY_GROUTH * SMALL_REBOUND_MULTIPLIER)

    def __call__(self, portfolio):
        price_change_1m = portfolio.stat["1M"]
        price_change_3m = portfolio.stat["3M"]
        price_change_5y = portfolio.stat["5Y"]
        return self.process(price_change_1m, price_change_3m, price_change_5y) * self.weight


class LtgRule(Rule):
    def __init__(self, name="Long-term grouth", **kwargs):
        super().__init__(name=name, **kwargs)

    def process(self, y):
        return pd.Series(y / y.max(), index=y.index, name=self.name)

    def __call__(self, portfolio):
        price_change_5y = portfolio.stat["5Y"]
        return self.process(price_change_5y) * self.weight


class StgRule(LtgRule):
    def __init__(self, name="Short-term grouth", **kwargs):
        super().__init__(name=name, **kwargs)

    def __call__(self, portfolio):
        price_change_1y = portfolio.stat["1Y"]
        return self.process(price_change_1y) * self.weight
