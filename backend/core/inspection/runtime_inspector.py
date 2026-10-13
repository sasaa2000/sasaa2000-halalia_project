from .inspection_event import InspectionEvent
from .inspection_report import InspectionReport

class RuntimeInspector:

    def __init__(self):

        self.report = InspectionReport()

        def log(

                self,

                stage,

                message,

                success=True

        ):
            event = InspectionEvent(

                stage=stage,

                message=message,

                success=success

            )

            self.report.add(event)

            def print_report(self):

                print()

                print("=" * 70)

                print("HALALIA Runtime Inspector")

                print("=" * 70)

                for event in self.report.events:

                    status = "OK"

                    if not event.success:
                        status = "FAIL"

                    print(

                        f"{status:5}"

                        f" | "

                        f"{event.stage:20}"

                        f" | "

                        f"{event.message}"

                    )

                print("=" * 70)

                