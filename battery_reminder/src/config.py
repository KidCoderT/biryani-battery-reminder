import json
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Literal, TypedDict

from battery_reminder.src.logger_config import setup_logger

# Initialize logger
logger = setup_logger()

APP_NAME = "biryani-battery-reminder"
CONFIG_FILE_NAME = (
    f"{APP_NAME.split('-')[0].lower().replace('-', '_').replace(' ', '_')}_config.json"
)
SHORTCUT_NAME = "Biryani Battery Reminder"

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
    overflow_percent: int

    remind_low_charge_time: int  # IN SECONDS
    remind_high_charge_time: int  # IN SECONDS
    remind_overflow_charge_time: int  # IN SECONDS


class GUISettings(TypedDict):
    """Type definition for the GUI_SETTINGS section."""

    theme: Literal["dark", "light"]  # "dark" | "light" | "system"


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
        "high_charge_percent": 90,
        "overflow_percent": 98,
        "remind_low_charge_time": 1 * 60 + 30,
        "remind_high_charge_time": 3 * 60,
        "remind_overflow_charge_time": 1 * 60,
    },
    "GUI_SETTINGS": {"theme": "light"},
}


def get_default_config():
    logger.debug("Retrieving default configuration")
    return DEFAULT_CONFIG_DATA


# -------------------------------------------------


def get_app_name():
    return APP_NAME


if getattr(sys, "frozen", False):
    # If running as a PyInstaller bundle
    config_path = os.path.join(os.path.dirname(sys.executable), CONFIG_FILE_NAME)
else:
    # If running as a script make the config outside
    config_path = Path(os.path.abspath(__file__)).parent.parent / CONFIG_FILE_NAME

logger.debug(f"Config path: {config_path}")


def load_config() -> AppConfig:
    """
    Loads the configuration from the JSON file.
    If the file doesn't exist, it creates it with default values.
    Returns the configuration as a dictionary.
    """
    logger.info(f"Loading config from: {config_path}")

    config: AppConfig

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as config_file:
                # Load the raw dictionary first, then cast to AppConfig
                loaded_config_raw: dict = json.load(config_file)
                logger.debug("Successfully loaded config file")

            config = deepcopy(DEFAULT_CONFIG_DATA)  # Use deepcopy instead of copy
            for section_key, section_defaults in DEFAULT_CONFIG_DATA.items():
                if section_key in loaded_config_raw and isinstance(
                    loaded_config_raw[section_key], dict
                ):
                    # Update section with loaded values, preserving defaults for missing keys
                    config[section_key].update(loaded_config_raw[section_key])
                else:
                    logger.warning(
                        f"Section '{section_key}' missing or malformed in config file. Using defaults."
                    )

            # Check if the loaded config needed any updates from defaults and save if so
            original_file_content = ""
            with open(config_path, "r") as f:
                original_file_content = f.read()

            temp_config_str = json.dumps(config, indent=4)
            if temp_config_str != original_file_content.strip():
                logger.info("Config file needs updating with new defaults")
                save_config(config)

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {config_path}: {str(e)}")
            logger.info("Creating default config due to JSON decode error")
            config = deepcopy(DEFAULT_CONFIG_DATA)  # Use deepcopy here too
            save_config(config)
    else:
        logger.info(f"Config file not found at {config_path}. Creating default.")
        config = deepcopy(DEFAULT_CONFIG_DATA)  # And here
        save_config(config)  # Create the default config file

    return config


def save_config(config: AppConfig):
    """
    Saves the given configuration dictionary to the JSON file.
    """
    try:
        with open(config_path, "w") as config_file:
            json.dump(config, config_file, indent=4)
        logger.info(f"Config saved successfully to: {config_path}")
    except Exception as e:
        logger.error(f"Error saving config to {config_path}: {str(e)}")
        raise


__all__ = [
    "get_app_name",
    "load_config",
    "save_config",
    "AppConfig",
    # "DEFAULT_CONFIG_DATA",
    "get_default_config",
]
