# -*- coding: utf-8 -*-
import logging
import json


class Wallet:
    def __init__(self, filename):
        with open(filename, 'r') as file:
            wallet_data = file.read()
        self.keys = json.loads(wallet_data)

    def read_key(self, name):
        if name in self.keys:
            return self.keys[name]
        logging.warn('Key %s not found in the wallet', name)
