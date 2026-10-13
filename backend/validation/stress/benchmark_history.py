class BenchmarkHistory:

    def __init__(self):

        self.times = []

    def add(self, value):

        self.times.append(value)

    @property
    def average(self):

        return sum(self.times) / len(self.times)

    @property
    def minimum(self):

        return min(self.times)

    @property
    def maximum(self):

        return max(self.times)