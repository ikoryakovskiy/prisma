import math

class Gaussian:
    def __init__(self, mean, std):
        self.mean = mean
        self.sq_std2 = 2 * (std ** 2)
        self.norm = math.sqrt(2 * math.pi) * std

    def __call__(self, x):
        return math.e ** ( - ((x - self.mean) ** 2) / self.sq_std2 ) / self.norm