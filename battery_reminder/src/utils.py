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

from battery_reminder.src.app_config_manager import MUTEX_NAME


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


def check_and_setup_mutex():
    """
    Check if another instance is running using Windows mutex.
    Returns:
        True: Another instance is already running (current app should exit)
        False: No other instance, mutex created successfully (current app should continue)
    """
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32

        # Constants
        ERROR_ALREADY_EXISTS = 183

        # Create/open mutex (local to current user session)
        mutex_name = MUTEX_NAME
        mutex_handle = kernel32.CreateMutexW(None, False, mutex_name)

        if mutex_handle == 0:
            logger.warning("Failed to create mutex - assuming no other instance")
            return False  # Graceful degradation: allow app to continue

        # Check if mutex already existed
        already_exists = kernel32.GetLastError() == ERROR_ALREADY_EXISTS

        if already_exists:
            # Another instance is running, close handle and signal to exit
            kernel32.CloseHandle(mutex_handle)
            logger.debug(
                "Another instance detected via mutex - current app should exit"
            )
            return True
        else:
            # First instance - create and keep mutex alive for app duration
            global _mutex_handle
            _mutex_handle = mutex_handle
            logger.debug("First instance - mutex created and stored globally")
            return False

    except Exception as e:
        logger.warning(f"Mutex check failed: {e} - allowing app to continue")
        # Graceful degradation: if mutex fails, assume no other instance
        return False


# def cleanup_mutex():
#     """
#     Optional: Explicitly clean up mutex on app shutdown.
#     Note: Windows will automatically clean up when process exits.
#     """
#     global _mutex_handle
#     if _mutex_handle:
#         try:
#             import ctypes
#
#             kernel32 = ctypes.windll.kernel32
#             kernel32.CloseHandle(_mutex_handle)
#             logger.debug("Mutex handle closed explicitly")
#         except Exception as e:
#             logger.error(f"Error closing mutex handle: {e}")
#         finally:
#             _mutex_handle = None
#

# Global variable to keep mutex handle alive for app duration
_mutex_handle = None
