# -*- coding: utf-8 -*-
import sys, inspect
import pandas as pd
from prisma.rules.rules import *


class Screener:
    def __init__(self, rules):
        clsmembers_tuples = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        clsmembers = {member[0]: member[1] for member in clsmembers_tuples}
        self.rules = []
        for rule in rules:
            if isinstance(rule, dict):
                for class_name, kwargs in rule.items():
                    assert class_name in clsmembers, f"Rule {class_name} is not available"
                    dynamically_created_rule = clsmembers[class_name](**kwargs)
                    self.rules.append(dynamically_created_rule)
            else:
                assert rule in clsmembers, f"Rule {rule} is not available"
                dynamically_created_rule = clsmembers[rule]()
                self.rules.append(dynamically_created_rule)

    def __call__(self, portfolio):
        columns = []
        for rule in self.rules:
            columns = rule(portfolio)

        total_score = pd.DataFrame([0] * len(table), columns=["TotalScore"], index=table.index)
        for column in table.columns:
            if "Score" in column:
                total_score["TotalScore"] += table[column]
        table["TotalScore"] = total_score["TotalScore"]