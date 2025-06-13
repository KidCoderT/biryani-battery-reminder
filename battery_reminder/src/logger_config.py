import sys
from pathlib import Path
from loguru import logger


def setup_logger():
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Remove default logger
    logger.remove()

    # Add console logger with colors - minimal info for privacy
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # Add file logger with rotation - detailed for debugging
    logger.add(
        "logs/debug.log",
        rotation="2 MB",  # Rotate when file reaches 2MB
        retention="2 weeks",  # Keep logs for 2 weeks
        compression="zip",  # Compress rotated logs
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        backtrace=True,  # Show full exception traceback
        diagnose=True,  # Show variable values in traceback
        filter=lambda record: "password"
        not in record["message"].lower(),  # Filter out sensitive data
    )

    # Add error log file for critical errors
    logger.add(
        "logs/error.log",
        rotation="2 MB",  # Rotate when file reaches 2MB
        retention="1 month",  # Keep error logs longer
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        backtrace=True,
        diagnose=True,
        filter=lambda record: "password"
        not in record["message"].lower(),  # Filter out sensitive data
    )

    return logger
