from datetime import datetime


class LogFormatter:

    @staticmethod
    def format(

        level,

        component,

        message

    ):

        timestamp = datetime.now().strftime(

            "%Y-%m-%d %H:%M:%S"

        )

        return (

            f"[{timestamp}] "

            f"[{level}] "

            f"[{component}] "

            f"{message}"

        )