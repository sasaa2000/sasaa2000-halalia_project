import requests

from backend.network.managers.header_manager import HeaderManager


class SessionManager:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update(
            HeaderManager.build()
        )

    def get(self):

        return self.session