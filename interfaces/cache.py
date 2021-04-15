import os
from datetime import date
import pickle
import glob
import logging

from prisma.constants import CACHE_DIR


class Cache:
    def get_short_name(self, query, data_type):
        symbol = query["symbol"]
        region = query["region"]
        return f"{region}-{symbol}-{data_type}"

    def get_full_name(self, query, data_type, date):
        name = self.get_short_name(query, data_type)
        return f"{name}-{date}.pkl"

    def get_filename(self, query, data_type):
        today = date.today()
        full_name = self.get_full_name(query, data_type, today)
        filename = os.path.join(CACHE_DIR, full_name)
        return filename

    def get_older_filename(self, query, data_type):
        full_name = self.get_full_name(query, data_type, "*")
        filename = os.path.join(CACHE_DIR, full_name)
        files = glob.glob(filename)
        if files:
            return sorted(files)[-1]  # take the latest
        return None

    def cache_response(self, data, filename):
        with open(filename, "wb") as file:
            pickle.dump(data, file)

    def load_cahced_response(self, filename):
        with open(filename, "rb") as file:
            return pickle.load(file)

    def clean(self):
        files = glob.glob(os.path.join(CACHE_DIR, "*.pkl"))
        today = date.today()
        for filename in files:
            if not str(today) in filename:
                logging.debug("Removing file %s", filename)
                os.remove(filename)
