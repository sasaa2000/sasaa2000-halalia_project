class HealthReport:

    def __init__(self):

        self.components = []

    def add(self, component):

        self.components.append(component)

    def is_healthy(self):

        return all(

            item.status == "HEALTHY"

            for item in self.components

        )

    def summary(self):

        return {

            "healthy": len(

                [

                    c

                    for c in self.components

                    if c.status == "HEALTHY"

                ]

            ),

            "failed": len(

                [

                    c

                    for c in self.components

                    if c.status == "FAILED"

                ]

            )

        }