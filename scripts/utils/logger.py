# scripts/utils/logger.py
#
# This file sets up logging for the entire project.
# Every other script will import from here to write log messages.
#
# We use the 'loguru' library because it produces much cleaner
# and more readable output than Python's built-in logging module.

import sys
from loguru import logger
from config.settings import LOGS_DIR
import os

# Create the logs folder if it doesn't exist yet
os.makedirs(LOGS_DIR, exist_ok=True)

# Remove the default loguru handler so we can set up our own
logger.remove()

# Handler 1: Print to the terminal
# This lets us see what's happening in real time while the program runs
# Format: time | level | message
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO",
    colorize=True,
)

# Handler 2: Write to a log file
# This saves a permanent record of everything that happens
# The file rotates (starts a new file) when it reaches 10 MB
# Old log files are kept for 7 days then automatically deleted
logger.add(
    os.path.join(LOGS_DIR, "pipeline.log"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
)

# This makes the logger importable by other files like this:
# from scripts.utils.logger import logger
__all__ = ["logger"]