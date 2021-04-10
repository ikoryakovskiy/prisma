import math
from constants import WINDOW_MULTIPLIER
from dateutil.relativedelta import relativedelta
from datetime import datetime


class Gaussian:
    def __init__(self, mean, std):
        self.mean = mean
        self.sq_std2 = 2 * (std ** 2)
        self.norm = math.sqrt(2 * math.pi) * std

    def __call__(self, x):
        return math.e ** (-((x - self.mean) ** 2) / self.sq_std2) / self.norm


class ConvDateSeries:
    def __call__(self, x, mean, std, filter="gaussian"):
        if filter == "gaussian":
            filter = Gaussian(0, std)  # will calculate in days

        half_window = WINDOW_MULTIPLIER * std
        start_date = mean - relativedelta(days=half_window)
        end_date = mean + relativedelta(days=half_window)

        windowed_x = x[(x.index >= str(start_date)) & (x.index <= str(end_date))]

        norm = 0
        filtered_x = 0
        for day, value in windowed_x.iteritems():
            days_to_mean = (datetime.strptime(day, "%Y-%m-%d").date() - mean).days
            weight = filter(days_to_mean)
            filtered_x += value * weight
            norm += weight
        return filtered_x / norm
