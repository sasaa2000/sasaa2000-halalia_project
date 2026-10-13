from backend.network.managers.session_manager import SessionManager
from backend.network.managers.proxy_manager import ProxyManager
from backend.network.managers.cookie_manager import CookieManager

from backend.network.engines.retry_engine import RetryEngine


class RequestEngine:

    def __init__(self):

        self.session = SessionManager().get()

        self.proxy_manager = ProxyManager()

        self.cookie_manager = CookieManager()

    def get(

        self,

        url,

        **kwargs

    ):

        def request():

            proxy = self.proxy_manager.get_proxy()

            cookies = self.cookie_manager.get()

            response = self.session.get(

                url,

                proxies=proxy,

                cookies=cookies,

                timeout=30,

                **kwargs

            )

            self.cookie_manager.update(

                response.cookies.get_dict()

            )

            print("=" * 60)
            print("STATUS :", response.status_code)
            print("URL    :", response.url)
            print("SIZE   :", len(response.text))
            print("=" * 60)

            response.raise_for_status()

            return response

        return RetryEngine.execute(request)