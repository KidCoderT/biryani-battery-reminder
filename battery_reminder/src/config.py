from pathlib import Path
import sys
import os
import json
from typing import Literal, TypedDict

APP_NAME = "battery-reminder"
CONFIG_FILE_NAME = f"{APP_NAME.lower().replace('-', '_').replace(' ', '_')}_config.json"

"""
Expected structure for the config.json file:

{
    "PROC_SETTINGS": {
        "run_on_startup": false,
        "alert_when_charger_plugged": true,
        "alert_when_charger_removed": true,
        "low_charge_percent": 10,
        "high_charge_percent": 95,
        "remind_low_charge_time": 5,
        "remind_high_charge_time": 10
    },
    "GUI_SETTINGS": {
        "theme": "system"
    }
}

"""

# -------------------------------------- TYPE HINTS


# Define the type hints for the nested dictionaries
class ProcSettings(TypedDict):
    """Type definition for the PROC_SETTINGS section."""

    run_on_startup: bool
    alert_when_charger_plugged: bool
    alert_when_charger_removed: bool
    low_charge_percent: int
    high_charge_percent: int
    remind_low_charge_time: int
    remind_high_charge_time: int


class GUISettings(TypedDict):
    """Type definition for the GUI_SETTINGS section."""

    theme: Literal["dark", "light", "system"]  # "dark" | "light" | "system"


class AppConfig(TypedDict):
    """Overall type definition for the entire application configuration."""

    PROC_SETTINGS: ProcSettings
    GUI_SETTINGS: GUISettings


DEFAULT_CONFIG_DATA: AppConfig = {
    "PROC_SETTINGS": {
        "run_on_startup": False,
        "alert_when_charger_plugged": True,
        "alert_when_charger_removed": True,
        "low_charge_percent": 10,
        "high_charge_percent": 50,
        "remind_low_charge_time": 3,  # 5,  # minutes
        "remind_high_charge_time": 3,  # 5,  # minutes
    },
    "GUI_SETTINGS": {"theme": "system"},
}

# -------------------------------------------------


def get_app_name():
    return APP_NAME


def get_config_path():
    """
    Returns the path to the configuration file.
    On Windows, typically in %APPDATA%.
    On Linux/macOS, typically in ~/.config or ~/.your_app_name.
    For simplicity, we'll put it next to the executable for PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # If running as a PyInstaller bundle
        return os.path.join(os.path.dirname(sys.executable), CONFIG_FILE_NAME)
    else:
        # If running as a script make the config outside
        return Path(os.path.abspath(__file__)).parent.parent / CONFIG_FILE_NAME


def load_config() -> AppConfig:
    """
    Loads the configuration from the JSON file.
    If the file doesn't exist, it creates it with default values.
    Returns the configuration as a dictionary.
    """
    config_path = get_config_path()
    print(f"Loading config from: {config_path}")

    config: AppConfig

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as config_file:
                # Load the raw dictionary first, then cast to AppConfig
                loaded_config_raw: dict = json.load(config_file)

            config = DEFAULT_CONFIG_DATA.copy()  # Start with a copy of defaults
            for section_key, section_defaults in DEFAULT_CONFIG_DATA.items():
                if section_key in loaded_config_raw and isinstance(
                    loaded_config_raw[section_key], dict
                ):
                    # Update section with loaded values, preserving defaults for missing keys
                    config[section_key].update(loaded_config_raw[section_key])
                else:
                    print(
                        f"Warning: Section '{section_key}' missing or malformed in config file. Using defaults."
                    )

            # Check if the loaded config needed any updates from defaults and save if so
            # To do a proper comparison, we need to reload the file after potential updates
            # This is a bit redundant but ensures we only save if truly modified.
            # A more efficient way might involve a flag set during the update loop.
            original_file_content = ""
            with open(config_path, "r") as f:
                original_file_content = f.read()

            # Compare the string representation of the potentially updated config with the original
            # This is a simple way to detect if a save is needed due to migration.
            # A more robust check would involve deep comparison of dictionaries.
            temp_config_str = json.dumps(config, indent=4)
            if temp_config_str != original_file_content.strip():
                save_config(config)

        except json.JSONDecodeError:
            print(f"Error decoding JSON from {config_path}. Creating default config.")
            config = DEFAULT_CONFIG_DATA
            save_config(config)
    else:
        print(f"Config file not found at {config_path}. Creating default.")
        config = DEFAULT_CONFIG_DATA
        save_config(config)  # Create the default config file

    return config


def save_config(config: AppConfig):
    """
    Saves the given configuration dictionary to the JSON file.
    """
    config_path = get_config_path()
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)
    print(f"Config saved to: {config_path}")


__all__ = [
    "get_app_name",
    "load_config",
    "save_config",
    "AppConfig",
    "DEFAULT_CONFIG_DATA",
]
