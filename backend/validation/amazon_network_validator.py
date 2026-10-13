import time

from .network_report import NetworkReport

from .response_snapshot import ResponseSnapshot

class AmazonNetworkValidator:

    def __init__(self, request_engine):

        self.request_engine = request_engine

        def validate(self, url):
            start = time.perf_counter()
            response = self.request_engine.get(url)
            elapsed = time.perf_counter() - start
            size = len(response.text)
            html = response.text

            html_size = len(

                html.encode("utf-8")

            )

            redirected = (

                    response.url != url

            )

            blocked_keywords = (

                "captcha",

                "robot check",

                "sorry",

                "enter the characters",

                "automated access"

            )

            blocked = any(

                keyword in html.lower()

                for keyword in blocked_keywords

            )

            success = (

                    response.status_code == 200

                    and

                    not blocked

            )

            snapshot = ResponseSnapshot(

                url=response.url,

                html=html,

                response_headers=dict(

                    response.headers

                )

            )

            report = NetworkReport(

                status_code=response.status_code,

                response_time=elapsed,

                html_size=html_size,

                blocked=blocked,

                redirected=redirected,

                success=success,

                message=(

                    "Network Validation Passed"

                    if success

                    else

                    "Amazon Blocked Request"

                )

            )

            return report


