class InspectionReport:

    def __init__(self):

        self.events = []

    def add(self, event):

        self.events.append(event)

    def summary(self):

        return {

            "events": len(self.events),

            "errors": len(

                [

                    e

                    for e in self.events

                    if not e.success

                ]

            )

        }