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
import os
from pathlib import Path
from battery_reminder.src.logger_config import logger
from battery_reminder.src.app_config_manager import SHORTCUT_NAME


def get_startup_folder():
    """Get the user's Startup folder."""
    return os.path.join(
        os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup"
    )


def get_exe_path():
    """Get the path to the current executable."""
    if getattr(sys, "frozen", False):
        return sys.executable
    else:
        return os.path.abspath(sys.argv[0])


def get_shortcut_path(shortcut_name=SHORTCUT_NAME):
    """Get the full path to the shortcut in the Startup folder."""
    if shortcut_name is None:
        shortcut_name = os.path.splitext(os.path.basename(get_exe_path()))[0]
    return os.path.join(get_startup_folder(), f"{shortcut_name}.lnk")


def create_shortcut(shortcut_path, target_path, icon_path=None):
    """Create a Windows shortcut (.lnk) at the given path."""
    from win32com.client import Dispatch

    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    if icon_path:
        shortcut.IconLocation = icon_path
    shortcut.save()


def add_to_startup(shortcut_name=SHORTCUT_NAME, icon_path=None):
    """Add the application to system startup (user-level, no admin required)."""
    shortcut_path = get_shortcut_path(shortcut_name)
    exe_path = get_exe_path()
    create_shortcut(shortcut_path, exe_path, icon_path)
    logger.info("Added to startup.")
    return True


def is_in_startup(shortcut_name=SHORTCUT_NAME):
    """Check if the shortcut exists in the Startup folder."""
    shortcut_path = get_shortcut_path(shortcut_name)
    return os.path.exists(shortcut_path)


def remove_from_startup(shortcut_name=SHORTCUT_NAME):
    """Remove the shortcut from the Startup folder."""
    shortcut_path = get_shortcut_path(shortcut_name)
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
        logger.info("Removed from startup.")
    return True
