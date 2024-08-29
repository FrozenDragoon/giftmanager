import logging
import datetime

import coloredlogs  # type: ignore[import-untyped, import-not-found]

from tap import Tap  # type: ignore

# Globals
logger: logging.Logger
#


def logging_setup(
    logLevel: int = logging.DEBUG,
    logToConsole: bool = True,
    logToFile: bool = False,
    logPath: str = "",
) -> None:
    """Configure logging"""
    global logger

    # https://stackoverflow.com/a/35804945
    def addLoggingLevel(levelName, levelNum, methodName=None):  # noqa
        """
        Comprehensively adds a new logging level to the `logging` module and the
        currently configured logging class.

        `levelName` becomes an attribute of the `logging` module with the value
        `levelNum`. `methodName` becomes a convenience method for both `logging`
        itself and the class returned by `logging.getLoggerClass()` (usually just
        `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
        used.

        To avoid accidental clobberings of existing attributes, this method will
        raise an `AttributeError` if the level name is already an attribute of the
        `logging` module or if the method name is already present

        Example
        -------
        >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
        >>> logging.getLogger(__name__).setLevel("TRACE")
        >>> logging.getLogger(__name__).trace('that worked')
        >>> logging.trace('so did this')
        >>> logging.TRACE
        5

        """
        if not methodName:
            methodName = levelName.lower()

        if hasattr(logging, levelName):
            raise AttributeError(
                "{} already defined in logging module".format(levelName)
            )
        if hasattr(logging, methodName):
            raise AttributeError(
                "{} already defined in logging module".format(methodName)
            )
        if hasattr(logging.getLoggerClass(), methodName):
            raise AttributeError(
                "{} already defined in logger class".format(methodName)
            )

        # This method was inspired by the answers to Stack Overflow post
        # http://stackoverflow.com/q/2183233/2988730, especially
        # http://stackoverflow.com/a/13638084/2988730
        def logForLevel(self, message, *args, **kwargs):  # fmt: skip; # noqa:ANN001, ANN002, ANN003, ANN201
            if self.isEnabledFor(levelNum):
                self._log(levelNum, message, args, **kwargs)

        def logToRoot(message, *args, **kwargs):  # fmt: skip # noqa:ANN001, ANN002, ANN003, ANN201
            logging.log(levelNum, message, *args, **kwargs)

        logging.addLevelName(levelNum, levelName)
        setattr(logging, levelName, levelNum)
        setattr(logging.getLoggerClass(), methodName, logForLevel)
        setattr(logging, methodName, logToRoot)
        return

    # Must be root logger
    # https://jdhao.github.io/2020/04/24/python_logging_for_multiple_modules/
    logger = logging.getLogger()
    if logToFile:
        file_handler = logging.FileHandler(
            f'{datetime.datetime.now().strftime("%Y%m%d")}.log'
        )

    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter(
        "%(asctime)s :: %(levelname)-8s :: %(funcName)-17s - %(message)s"
    )
    if logToFile:
        file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    if logToFile:
        logger.addHandler(file_handler)

    addLoggingLevel("SPAM", 5)
    addLoggingLevel("SUCCESS", 35)

    ###
    # Use "stacklevel=2" to prevent logging this caller name... sometimes?
    # https://stackoverflow.com/a/74507376
    # Example:
    # logging.log(5, 'this might not work', stacklevel=2)
    ###

    logger.setLevel(logLevel)

    coloredlogs.install(
        level=logger.level,
        logger=logger,
        fmt="%(asctime)s :: %(levelname)-8s :: %(funcName)-17s - %(message)s",
        field_styles={
            "asctime": {"color": "green"},
            "levelname": {"bold": True, "color": "black"},
            "funcName": {"color": "blue"},
            "thread": {"color": "black"},
        },
    )

    return


def get_log_level(levelInput: str | int) -> int:
    log_level_int: int

    try:
        levelInput = int(levelInput)  # Cast str to int, if possible
    except (TypeError, ValueError):
        pass  # don't change anything

    if isinstance(levelInput, int):
        log_level_int = levelInput
    elif isinstance(levelInput, str):
        if levelInput.lower() in [
            "spam",
            "debug",
            "info",
            "warning",
            "success",
            "error",
            "critical",
        ]:
            if levelInput.lower() == "spam":
                log_level_int = 5
            elif levelInput.lower() == "debug":
                log_level_int = 10
            elif levelInput.lower() == "info":
                log_level_int = 20
            elif levelInput.lower() == "warning":
                log_level_int = 30
            elif levelInput.lower() == "success":
                log_level_int = 35
            elif levelInput.lower() == "error":
                log_level_int = 40
            elif levelInput.lower() == "critical":
                log_level_int = 50
        else:
            raise SystemExit(f"ERROR: '{levelInput}' is not a valid log level string.")
    else:
        raise SystemExit(
            "ERROR: --log-level should be an integer or valid log level string."
        )

    return log_level_int


def log_level_type(log_level):
    return log_level


class LoggingArgs(Tap):
    log_level: int = logging.INFO  # Can be Int level or String word
    logToFile: bool = False

    def configure(self):
        self.add_argument("--log-level", type=log_level_type)

    def process_args(self):
        # Validate arguments
        self.log_level = get_log_level(self.log_level)


if __name__ == "__main__":
    logArgs = LoggingArgs(underscores_to_dashes=True).parse_args()
    logging_setup(logLevel=logArgs.log_level, logToFile=logArgs.logToFile)
    logger.log(35, "Logging setup completed")
    logger.info("INFO logging enabled")
    logger.debug("DEBUG logging enabled")
    logger.log(5, "SPAM logging enabled")

    logger.debug("logArgs: %s", logArgs)
