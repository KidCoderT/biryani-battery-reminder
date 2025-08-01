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
import random
from pathlib import Path
from PIL import Image
import typing
from battery_reminder.src.logger_config import logger

if getattr(sys, "frozen", False):
    # PyInstaller sets _MEIPASS, cx_Freeze does not
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    base_path = os.path.dirname(__file__)

if getattr(sys, "frozen", False):
    # If running as a PyInstaller bundle, assets are unpacked into sys._MEIPASS
    # and we added them to a folder named 'assets' within that bundle's root.
    ASSETS_FOLDER = Path(base_path) / "assets"
else:
    # If running as a script (e.g., via `python -m battery_reminder`)
    # `__file__` refers to the current script (assets_manager.py).
    # Its path is: battery-reminder/battery_reminder/assets_manager.py
    # We need to go up two levels to the project root (battery-reminder/)
    # and then down into the 'assets' folder.
    current_script_dir = Path(__file__).parent  # battery-reminder/battery_reminder
    project_root_dir = current_script_dir.parent.parent  # battery-reminder/
    ASSETS_FOLDER = project_root_dir / "assets"

ASSETS_FOLDER = ASSETS_FOLDER.absolute()
assert ASSETS_FOLDER.exists()


def load_image(path: Path):
    assert path.exists(), f"IMAGE '{path}' DOESNT EXIST"
    assert path.is_file(), f"IMAGE '{path}' IS INVALID TYPE!!"
    return Image.open(path)


APP_ICONS = {  # BASED ON THE APP PROCESS STATE IF ITS WORKING OR NOT
    True: load_image(ASSETS_FOLDER / "working.ico"),
    False: load_image(ASSETS_FOLDER / "not-working-yet.ico"),
}

EMOJIS_FOLDER = ASSETS_FOLDER / "emojis"
SOUND_FOLDER = ASSETS_FOLDER / "sounds"

EMOJI_TYPES = typing.Literal[
    "happy", "oh-no", "perfect", "plain", "too-much", "yes", "hehe", "too-much-2"
]
EMOJI: dict[EMOJI_TYPES, Path] = {
    emoji: EMOJIS_FOLDER / f"{emoji}.png" for emoji in typing.get_args(EMOJI_TYPES)
}

SOUND_TYPES = typing.Literal["too-low", "perfect-battery", "battery-overflow"]


def get_default_sound(sound_type: SOUND_TYPES):
    return str(SOUND_FOLDER / f"{sound_type}.mp3")


def get_tkinter_icon():
    return ASSETS_FOLDER / "icon.png"


def app_icon(background_proc_state: bool):
    return APP_ICONS[background_proc_state]


def get_emoji(type: EMOJI_TYPES | list[EMOJI_TYPES]):
    if isinstance(type, list):
        icon = EMOJI[random.choice(type)]
    else:
        icon = EMOJI[type]

    assert icon.exists(), f"ICON '{type}' DOESNT EXITS IN ASSETS FOLDER"
    assert icon.is_file(), f"ICON '{type}' IS INVALID TYPE!!"
    return icon


__all__ = ["APP_ICONS", "get_emoji", "SOUND_TYPES", "get_default_sound"]
