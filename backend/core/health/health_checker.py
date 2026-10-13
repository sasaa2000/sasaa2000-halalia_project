from backend.core.health.health_report import HealthReport


from backend.core.health.component_check import ComponentCheck

from backend.core.health.health_status import HealthStatus


class HealthChecker:

    def __init__(self):

        self.report = HealthReport()

        def check(

                self,

                name,

                condition,

                success_message,

                failed_message

        ):
            status = (

                HealthStatus.HEALTHY

                if condition

                else HealthStatus.FAILED

            )

            message = (

                success_message

                if condition

                else failed_message

            )

            self.report.add(

                ComponentCheck(

                    name=name,

                    status=status,

                    message=message

                )

            )

            def run(self):
                return self.report
