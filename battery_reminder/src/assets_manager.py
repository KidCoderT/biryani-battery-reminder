from pathlib import Path
import typing

ASSETS_FOLDER = Path("./assets").absolute()
assert ASSETS_FOLDER.exists()

ICON = ASSETS_FOLDER / "icon.ico"
EMOJIS_FOLDER = ASSETS_FOLDER / "emojis"

EMOJI_TYPES = typing.Literal["happy", "oh-no", "perfect", "plain", "too-much", "yes"]
EMOJI: dict[EMOJI_TYPES, Path] = {
    emoji: EMOJIS_FOLDER / f"{emoji}.png" for emoji in typing.get_args(EMOJI_TYPES)
}


def app_icon():
    return ICON


def get_emoji(type: EMOJI_TYPES):
    icon = EMOJI[type]
    assert icon.exists(), f"ICON '{type}' DOESNT EXITS IN ASSETS FOLDER"
    assert icon.is_file(), f"ICON '{type}' IS INVALID TYPE!!"
    return icon


__all__ = ["app_icon", "get_emoji"]
