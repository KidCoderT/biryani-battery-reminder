import sys
import os
import json

APP_NAME = "Battery Reminder"
CONFIG_FILE_NAME = f"{APP_NAME.lower().replace(' ', '_')}_config.json"

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
        # If running as a script
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE_NAME
        )


def load_config():
    """
    Loads the configuration from the JSON file.
    If the file doesn't exist, it creates it with default values.
    Returns the configuration as a dictionary.
    """
    config_path = get_config_path()
    print(f"Loading config from: {config_path}")

    # Define default configuration data
    default_config_data = {
        "PROC_SETTINGS": {
            "run_on_startup": False,
            "alert_when_charger_plugged": True,
            "alert_when_charger_removed": True,
            "low_charge_percent": 10,
            "high_charge_percent": 95,
            "remind_low_charge_time": 5,  # minutes
            "remind_high_charge_time": 10,  # minutes
        },
        "GUI_SETTINGS": {"theme": "system"},
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as config_file:
                config = json.load(config_file)

            for section, settings in default_config_data.items():
                if section not in config:
                    config[section] = {}
                for key, default_value in settings.items():
                    if key not in config[section]:
                        config[section][key] = default_value

            if config != json.load(open(config_path, "r")):  # Check if config changed
                save_config(config)

        except json.JSONDecodeError:
            print(f"Error decoding JSON from {config_path}. Creating default config.")
            config = default_config_data
            save_config(config)
    else:
        print(f"Config file not found at {config_path}. Creating default.")
        config = default_config_data
        save_config(config)  # Create the default config file

    return config


def save_config(config):
    """
    Saves the given configuration dictionary to the JSON file.
    """
    config_path = get_config_path()
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=4)
    print(f"Config saved to: {config_path}")


__all__ = ["get_app_name", "load_config", "save_config"]
