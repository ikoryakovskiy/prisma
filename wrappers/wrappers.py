#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr  3 22:24:54 2021

@author: ivan
"""

class Comparison:
    def __lt__(self, other):
        return self.value < other
    def __le__(self, other):
        return self.value <= other
    def __eq__(self, other):
        return self.value == other
    def __ne__(self, other):
        return self.value != other
    def __gt__(self, other):
        return self.value > other
    def __ge__(self, other):
        return self.value >= other
    def __add__(self, other):
        if isinstance(other, Comparison):
            return other.value
        return self.value + other
    def __div__(self, other):
        if isinstance(other, Comparison):
            return self.value / other.value
        return self.value / other
    def __floordiv__(self, other):
        return self.value // other
#    def __mod__(self, other):
#        return self.value + other
    def __mul__(self, other):
        return self.value * other
    def __sub__(self, other):
        return self.value - other
    def __truediv__(self, other):
        return self.__div__(other)
    def __neg__(self):
        return -self.value


class ToMillions(Comparison):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"{self.value/1000000:.1f}M"


class Percent(Comparison):
    def __init__(self, value, decimal_digits=0):
        self.value = value * 100
        self.decimal_digits = decimal_digits

    def __repr__(self):
        value = round(self.value, self.decimal_digits)
        if self.decimal_digits > 0:
            return str(value)
        else:
            return  str(int(value))
