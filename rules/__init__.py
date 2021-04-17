from prisma.rules.rules import (
    SectorRule,
    CountryRule,
    PePsRule,
    TerRule,
    DeclineRule,
    LtgRule,
    StgRule,
)

rule_cls = {
    "SectorRule": SectorRule,
    "CountryRule": CountryRule,
    "PePsRule": PePsRule,
    "TerRule": TerRule,
    "DeclineRule": DeclineRule,
    "LtgRule": LtgRule,
    "StgRule": StgRule,
}

__all__ = list(rule_cls.keys())
