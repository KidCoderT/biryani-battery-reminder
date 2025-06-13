import sys
import random
from pathlib import Path
from PIL import Image
import typing

if getattr(sys, "frozen", False):
    # If running as a PyInstaller bundle, assets are unpacked into sys._MEIPASS
    # and we added them to a folder named 'assets' within that bundle's root.
    ASSETS_FOLDER = Path(sys._MEIPASS) / "assets"
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

EMOJI_TYPES = typing.Literal[
    "happy", "oh-no", "perfect", "plain", "too-much", "yes", "hehe", "too-much-2"
]
EMOJI: dict[EMOJI_TYPES, Path] = {
    emoji: EMOJIS_FOLDER / f"{emoji}.png" for emoji in typing.get_args(EMOJI_TYPES)
}


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


__all__ = ["APP_ICONS", "get_emoji"]
