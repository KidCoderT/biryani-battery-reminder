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

import os
import sys
from threading import Lock, Thread

from loguru import logger


class SingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}

    _lock: Lock = Lock()
    """
    We now have a lock object that will be used to synchronize threads during
    first access to the Singleton.
    """

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        # Now, imagine that the program has just been launched. Since there's no
        # Singleton instance yet, multiple threads can simultaneously pass the
        # previous conditional and reach this point almost at the same time. The
        # first of them will acquire lock and will proceed further, while the
        # rest will wait here.
        with cls._lock:
            # The first thread to acquire the lock, reaches this conditional,
            # goes inside and creates the Singleton instance. Once it leaves the
            # lock block, a thread that might have been waiting for the lock
            # release may then enter this section. But since the Singleton field
            # is already initialized, the thread won't create a new object.
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


def is_frozen():
    """Check if the application is running as a frozen executable (cx_Freeze)."""
    return getattr(sys, "frozen", False)  # True if frozen, False otherwise[1][6]


def is_already_running():
    """Check if another instance of this executable is running."""
    import psutil  # Requires 'psutil' package

    current_pid = os.getpid()
    exe_name = os.path.basename(sys.executable if is_frozen() else sys.argv[0])
    count = 0
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] == exe_name and proc.info["pid"] != current_pid:
                logger.debug(
                    f"Process {proc.info['pid']} - {proc.info['name']} already running"
                )
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return count > 0
