from pathlib import Path

from .formatter import LogFormatter

from .log_levels import LogLevel


class HalaliaLogger:

    def __init__(self):

        self.log_dir = Path("backend/logs")

        self.log_dir.mkdir(

            parents=True,

            exist_ok=True

        )

        self.log_file = (

            self.log_dir /

            "runtime.log"

        )

    # ===================================

    def write(

        self,

        level,

        component,

        message

    ):

        line = LogFormatter.format(

            level,

            component,

            message

        )

        print(line)

        with open(

            self.log_file,

            "a",

            encoding="utf-8"

        ) as file:

            file.write(

                line + "\n"

            )

    # ===================================

    def debug(

        self,

        component,

        message

    ):

        self.write(

            LogLevel.DEBUG,

            component,

            message

        )

    # ===================================

    def info(

        self,

        component,

        message

    ):

        self.write(

            LogLevel.INFO,

            component,

            message

        )

    # ===================================

    def warning(

        self,

        component,

        message

    ):

        self.write(

            LogLevel.WARNING,

            component,

            message

        )

    # ===================================

    def error(

        self,

        component,

        message

    ):

        self.write(

            LogLevel.ERROR,

            component,

            message

        )

    # ===================================

    def critical(

        self,

        component,

        message

    ):

        self.write(

            LogLevel.CRITICAL,

            component,

            message

        )