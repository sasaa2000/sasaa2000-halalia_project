import random


class ProxyManager:

    def __init__(self):

        self.proxies = []

    def add_proxy(self, proxy):

        self.proxies.append(proxy)

    def get_proxy(self):

        if not self.proxies:

            return None

        return random.choice(self.proxies)

    def clear(self):

        self.proxies.clear()