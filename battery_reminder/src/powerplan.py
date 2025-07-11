# __author__ = "Temal" @ https://github.com/temal32/powerplan
# Tejas (Updated this)"

import subprocess
from typing import Literal
from battery_reminder.src.logger_config import logger


def _check_ultimate_performance_exists() -> bool:
    """Check if the Ultimate Performance power plan exists on the system.

    Returns:
        bool: True if Ultimate Performance plan exists, False otherwise
    """
    try:
        # Use powercfg /list to get all available power schemes
        output = subprocess.check_output(["powercfg", "/list"], stderr=subprocess.PIPE)

        # Check if Ultimate Performance GUID exists in the output
        ultimate_performance_guid = b"e9a42b02-d5df-448d-aa00-03f14749eb61"
        return ultimate_performance_guid in output

    except subprocess.CalledProcessError as error:
        logger.error(f"Failed to list power schemes: {error}")
        return False
    except FileNotFoundError:
        logger.error("powercfg command not found - this feature is Windows-only")
        return False
    except Exception as error:
        logger.error(f"Unexpected error checking for Ultimate Performance: {error}")
        return False


def get_current_scheme_name():
    output = b""

    try:
        output = subprocess.check_output(
            ["powercfg", "-getactivescheme"], stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as error:
        logger.error(f"Failed to get active power scheme: {error}")
        return "UNKNOWN"
    except FileNotFoundError:
        logger.error("powercfg command not found - this feature is Windows-only")
        return "UNKNOWN"
    except Exception as error:
        logger.error(f"Unexpected error getting power scheme: {error}")
        return "UNKNOWN"

    if b"a1841308-3541-4fab-bc81-f71556f20b4a" in output:
        current_powerplan_guid = "a1841308-3541-4fab-bc81-f71556f20b4a"
        current_powerplan_name = "Power saver"
        gotten = True

    elif b"381b4222-f694-41f0-9685-ff5bb260df2e" in output:
        current_powerplan_guid = "381b4222-f694-41f0-9685-ff5bb260df2e"
        current_powerplan_name = "Balanced"
        gotten = True

    elif b"8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c" in output:
        current_powerplan_guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
        current_powerplan_name = "High performance"
        gotten = True

    elif b"e9a42b02-d5df-448d-aa00-03f14749eb61" in output:
        current_powerplan_guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
        current_powerplan_name = "Ultimate performance"
        gotten = True

    elif b"Ult" in output:
        current_powerplan_guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
        current_powerplan_name = "Ultimate performance"
        gotten = True

    else:
        gotten = False
        current_powerplan_guid = "UNKNOWN"
        current_powerplan_name = "UNKNOWN"

    logger.debug(f"Current power scheme: {current_powerplan_name}")
    return current_powerplan_name


def change_current_scheme_to_powersaver():
    try:
        result = subprocess.run(
            ["powercfg", "/s", "a1841308-3541-4fab-bc81-f71556f20b4a"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("Successfully changed power scheme to Power Saver")
        return True
    except subprocess.CalledProcessError as error:
        logger.error(f"Failed to change to Power Saver: {error.stderr}")
        return False
    except FileNotFoundError:
        logger.error("powercfg command not found - this feature is Windows-only")
        return False
    except Exception as error:
        logger.error(f"Unexpected error changing to Power Saver: {error}")
        return False


def change_current_scheme_to_balanced():
    try:
        result = subprocess.run(
            ["powercfg", "/s", "381b4222-f694-41f0-9685-ff5bb260df2e"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("Successfully changed power scheme to Balanced")
        return True
    except subprocess.CalledProcessError as error:
        logger.error(f"Failed to change to Balanced: {error.stderr}")
        return False
    except FileNotFoundError:
        logger.error("powercfg command not found - this feature is Windows-only")
        return False
    except Exception as error:
        logger.error(f"Unexpected error changing to Balanced: {error}")
        return False


def change_current_scheme_to_high():
    try:
        result = subprocess.run(
            ["powercfg", "/s", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("Successfully changed power scheme to High Performance")
        return True
    except subprocess.CalledProcessError as error:
        logger.error(f"Failed to change to High Performance: {error.stderr}")
        return False
    except FileNotFoundError:
        logger.error("powercfg command not found - this feature is Windows-only")
        return False
    except Exception as error:
        logger.error(f"Unexpected error changing to High Performance: {error}")
        return False


def set_default_power_plan(
    power_plan_name: Literal[
        "Power saver",
        "Balanced",
        "High performance",
        "Ultimate performance",
    ],
) -> bool:
    """Set the default power plan.

    Args:
        power_plan_name: The name of the power plan to set as default

    Returns:
        bool: True if successful, False otherwise
    """
    power_plan_guids = {
        "Power saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
        "Balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
        "High performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "Ultimate performance": "e9a42b02-d5df-448d-aa00-03f14749eb61",
    }

    if power_plan_name not in power_plan_guids:
        logger.error(f"Unknown power plan: {power_plan_name}")
        return False

    guid = power_plan_guids[power_plan_name]

    try:
        result = subprocess.run(
            ["powercfg", "/s", guid],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info(f"Successfully set default power scheme to {power_plan_name}")
        return True
    except subprocess.CalledProcessError as error:
        logger.error(
            f"Failed to set default power plan to {power_plan_name}: {error.stderr}"
        )
        return False
    except FileNotFoundError:
        logger.error("powercfg command not found - this feature is Windows-only")
        return False
    except Exception as error:
        logger.error(f"Unexpected error setting default power plan: {error}")
        return False


def get_available_power_plans() -> list[str]:
    """Get a list of available power plans.

    Returns:
        list[str]: List of available power plan names
    """
    available_plans = ["Power saver", "Balanced", "High performance"]

    # Check if Ultimate Performance exists and add it to the list
    if _check_ultimate_performance_exists():
        available_plans.append("Ultimate performance")
        logger.debug(
            "Ultimate Performance power plan found and added to available plans"
        )
    else:
        logger.debug("Ultimate Performance power plan not found on this system")

    return available_plans
