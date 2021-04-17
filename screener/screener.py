# -*- coding: utf-8 -*-
import pandas as pd
from prisma.rules import rule_cls


class Screener:
    def __init__(self, rules):
        self.rules = []
        for rule in rules:
            if isinstance(rule, dict):
                for class_name, kwargs in rule.items():
                    assert class_name in rule_cls, f"Rule {class_name} is not available"
                    dynamically_created_rule = rule_cls[class_name](**kwargs)
                    self.rules.append(dynamically_created_rule)
            else:
                assert rule in rule_cls, f"Rule {rule} is not available"
                dynamically_created_rule = rule_cls[rule]()
                self.rules.append(dynamically_created_rule)

    def __call__(self, portfolio):
        columns = []
        for rule in self.rules:
            columns.append(rule(portfolio))

        scores = pd.concat(columns, axis=1, keys=[col.name for col in columns])
        scores["TotalScore"] = scores.sum(axis=1)
        return scores
