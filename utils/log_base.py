import logging
import sys

COLORS = {
    "DEBUG": "\033[92m",  # Green
    "INFO": "",  # No color, use default
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
    "CRITICAL": "\033[91;1m",  # Bold red
    "RESET": "\033[0m",  # Reset color
}


class ColorFormatter(logging.Formatter):
    """Custom color log formatter"""

    def format(self, record):
        color = COLORS.get(record.levelname, COLORS["RESET"])
        message = super().format(record)
        return f"{color}{message}{COLORS['RESET']}"


# Configure logging system
def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        ColorFormatter(
            "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )

    logger.addHandler(console_handler)
    return logger


logger = setup_logger()
