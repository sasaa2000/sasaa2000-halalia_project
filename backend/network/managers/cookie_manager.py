class CookieManager:

    def __init__(self):

        self.cookies = {}

    def update(self, cookies):

        if cookies:

            self.cookies.update(cookies)

    def get(self):

        return self.cookies

    def clear(self):

        self.cookies = {}