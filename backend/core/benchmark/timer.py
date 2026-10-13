import time


class Timer:

    def __init__(self):

        self.start_time = None

    def start(self):

        self.start_time = time.perf_counter()

    def stop(self):

        if self.start_time is None:

            return 0.0

        return time.perf_counter() - self.start_time