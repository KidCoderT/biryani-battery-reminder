# Copyright (C) 2025 Tejas
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the LICENSE file for more details.

import sys
from pathlib import Path
from loguru import logger


def _get_log_dir() -> Path:
    # Anchor logs next to the exe when frozen, or at the package root when running from source.
    # A relative Path("logs") would write to wherever the CWD happens to be (e.g. C:\Windows\System32
    # when auto-launched from Startup), which makes logs impossible to find.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "logs"
    return Path(__file__).parent.parent / "logs"


def setup_logger():
    # Create logs directory if it doesn't exist
    log_dir = _get_log_dir()
    log_dir.mkdir(exist_ok=True)

    # Remove default logger
    logger.remove()

    # Add console logger with colors - minimal info for privacy
    if not getattr(sys, "frozen", False):
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="INFO",
            colorize=True,
        )

    # Add file logger with rotation - detailed for debugging
    logger.add(
        str(log_dir / "debug.log"),
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
        str(log_dir / "error.log"),
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


logger = setup_logger()

__all__ = ["logger", "setup_logger"]
