class RuntimeReport:

    def __init__(self):

        self.steps = []

    def add(

        self,

        step,

        success

    ):

        self.steps.append(

            {

                "step": step,

                "success": success

            }

        )

    def print(self):

        print()

        print("=" * 60)

        print("HALALIA Runtime Report")

        print("=" * 60)

        for item in self.steps:

            status = "PASS"

            if not item["success"]:

                status = "FAIL"

            print(

                f"{status:5} | {item['step']}"

            )

        print("=" * 60)