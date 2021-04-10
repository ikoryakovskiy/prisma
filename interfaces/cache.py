import os
from datetime import date
import pickle

from prisma.constants import CACHE_DIR


class Cache:
    def get_short_name(self, query, data_type):
        symbol = query["symbol"]
        region = query["region"]
        return f"{region}-{symbol}-{data_type}"

    def get_full_name(self, query, data_type):
        name = self.get_short_name(query, data_type)
        today = date.today()
        return f"{name}-{today}.pkl"

    def get_filename(self, query, data_type):
        full_name = self.get_full_name(query, data_type)
        filename = os.path.join(CACHE_DIR, full_name)
        return filename

    def cache_responce(self, data, filename):
        with open(filename, "wb") as file:
            pickle.dump(data, file)

    def load_cahced_responce(self, filename):
        with open(filename, "rb") as file:
            return pickle.load(file)

    def clean(self):
        # TODO: implement
        pass