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

import time
import atexit
from pathlib import Path
from typing import Literal
from batteryinfo import Battery, TimeFormat
from desktop_notifier import Urgency, Button
from battery_reminder.src.app_config_manager import (
    DEFAULT_CONFIG_DATA,
    get_app_name,
    load_config,
    AppConfig,
)
from battery_reminder.src.assets_manager import get_emoji
from battery_reminder.src.logger_config import setup_logger
from battery_reminder.src.utils import SingletonMeta
from battery_reminder.src import powerplan

import multiprocessing
from multiprocessing.sharedctypes import SynchronizedBase, Value
from ctypes import c_bool

# Initialize logger
logger = setup_logger()

NOTIFICATION_TIMEOUT = -1

BATTERY_STATE = {
    "OVERLFLOW": "IN OVERFLOW",
    "HIGH": "IN HIGH STATE",
    "NORMAL": "Between LOW and HIGH",
    "LOW": "LOW STATE",
}

EVENTS = Literal["overflow", "high", "min"]

POWER_STATES = {
    "UNKOWN": lambda: print("Unknown power state"),
    "Power saver": powerplan.change_current_scheme_to_powersaver,
    "Balanced": powerplan.change_current_scheme_to_balanced,
    "High performance": powerplan.change_current_scheme_to_high,
    "Ultimate performance": powerplan.change_current_scheme_to_high,
}


# MESSAGES SIGNALS: TODO: LATER
# CHARGE_TO_100_MSG = "Charge to 100%"

# MESSAGES
MESSAGES = {}


class BatteryDataManager(metaclass=SingletonMeta):
    def __init__(self, _class=Battery):
        self.battery: Battery = _class(time_format=TimeFormat.Human)

    def get_battery_data(self):
        logger.debug("Fetching battery data")
        self.battery.refresh()
        return {
            "vendor": self.battery.vendor,
            "model": self.battery.model,
            "energy_rate": self.battery.energy_rate,
            "technology": self.battery.technology,
            "voltage": self.battery.voltage,
            "temperature": self.battery.temperature or "Not Available",
            # PERCENTAGE GOOD OF BATERY
            "capacity": self.battery.capacity,
            # ENERGY
            "energy": self.battery.energy,
            "energy_full": self.battery.energy_full,
            "energy_full_design": self.battery.energy_full_design,
        }


class BackgroundProcessManager:
    def __init__(
        self,
        notification_queue: multiprocessing.Queue,
        critical_notifications_queue: multiprocessing.Queue,
        app_name=get_app_name(),
        _class=Battery,
    ) -> None:
        logger.info("Initializing background process manager...")
        self.battery: Battery = _class(time_format=TimeFormat.Human)
        self.current_charger_state = self.battery.state
        self.current_battery_state = BATTERY_STATE["NORMAL"]
        self.timers = {}

        # Power stuff
        self.default_power_state = powerplan.get_current_scheme_name()
        self.power_state_changed = False

        self.notification_queue = notification_queue
        self.critical_notifications_queue = critical_notifications_queue
        self.config = load_config()
        logger.info("Background process manager initialized successfully")

        self.can_change_power_state = (
            self.default_power_state
            not in [
                "Power saver",
                "UNKNOWN",
            ]
            and self.config["PROC_SETTINGS"]["save_power_state_at_percent"]
        )

    def get_battery_state(self):
        charge_amount = self.battery.percent.value
        state = BATTERY_STATE["NORMAL"]

        if charge_amount >= self.config["PROC_SETTINGS"]["overflow_percent"]:  # 2 min
            state = BATTERY_STATE["OVERLFLOW"]
        elif charge_amount >= self.config["PROC_SETTINGS"]["high_charge_percent"]:
            state = BATTERY_STATE["HIGH"]
        elif charge_amount <= self.config["PROC_SETTINGS"]["low_charge_percent"]:
            state = BATTERY_STATE["LOW"]

        logger.debug(f"Battery state: {state} (Charge: {charge_amount}%)")
        return state

    @property
    def time_to_full(self):
        return self.battery.time_to_full

    @property
    def time_to_empty(self):
        return self.battery.time_to_empty

    @property
    def percentage(self) -> float:
        return self.battery.percent.value

    @property
    def is_charging(self):
        return self.battery.state == "Charging"

    def send_welcome_message(self):
        logger.info("Sending welcome message")
        if self.is_charging:
            message = f"You are currently charging your laptop. It's {self.percentage:.1f}% charged. {self.time_to_full} until 100% charge!"
        else:
            message = f"You have {self.percentage:.1f}% charge remaining, which amounts to {self.time_to_empty} of battery life!"

        self.notification_queue.put_nowait(
            dict(
                title="Battery Monitor Started!",
                message="Hello! I've started monitoring your battery. " + message,
                icon="plain",
                timeout=NOTIFICATION_TIMEOUT,
                urgency=Urgency.Critical,
                # buttons=[("Open Settings", "msg")],
                # sound=
            )
        )

        logger.debug("Welcome message sent successfully")

    def send_charging_message(self):
        logger.info("Sending charging message")
        if self.current_battery_state == BATTERY_STATE["OVERLFLOW"]:
            self.notification_queue.put_nowait(
                dict(
                    title="Please STOP Charging",
                    message=f"You are already {self.percentage:.1f}% Charged!! Any longer and you could ruin your battery! You dont need to charge any further!",
                    icon="too-much-2",
                    timeout=NOTIFICATION_TIMEOUT,
                    urgency=Urgency.Critical,
                )
            )
            self.reminder_time_passed("high", 0, True)
        elif self.current_battery_state == BATTERY_STATE["HIGH"]:
            self.notification_queue.put_nowait(
                dict(
                    title="You dont need to Charge",
                    message=f"You are already {self.percentage:.1f}% Charged! You dont need to charge any further",
                    icon="hehe",
                    timeout=NOTIFICATION_TIMEOUT,
                    urgency=Urgency.Normal,
                )
            )
            self.reminder_time_passed("high", 0, True)
        elif self.config["PROC_SETTINGS"]["alert_when_charger_plugged"]:
            self.notification_queue.put_nowait(
                dict(
                    title="Started Charging!",
                    message=f"It will take another {self.time_to_full or ''} to fully charge! Currently its {self.percentage:.1f}% full",
                    icon="happy",
                    timeout=NOTIFICATION_TIMEOUT,
                    urgency=Urgency.Normal,
                )
            )

        logger.debug("Charging message sent successfully")

    def send_discharging_message(self):
        logger.info("Sending discharging message")
        if self.current_battery_state == BATTERY_STATE["LOW"]:
            self.notification_queue.put_nowait(
                dict(
                    title="Dont Stop Charging!",
                    message=f"You have {self.time_to_empty or ''} of Charge Left! Currently there is {self.percentage:.1f}% charge left. You need to charge some more!",
                    icon="oh-no",
                    timeout=NOTIFICATION_TIMEOUT,
                    urgency=Urgency.Critical,
                )
            )
            self.reminder_time_passed("min", 0, True)
        elif self.config["PROC_SETTINGS"]["alert_when_charger_removed"]:
            self.notification_queue.put_nowait(
                dict(
                    title="Charger Disconnected",
                    message=f"Charging stopped. You have {self.time_to_empty or 'unknown time'} of battery life remaining. Current level: {self.percentage:.1f}%",
                    icon="happy",
                    timeout=NOTIFICATION_TIMEOUT,
                    urgency=Urgency.Normal,
                )
            )
        logger.debug("Discharging message sent successfully")

    def send_removal_warning(self):
        logger.info("Sending removal warning")
        self.notification_queue.put_nowait(
            dict(
                title=f"Its {self.percentage:.1f}% Full",
                message=f"You should remove the charger now! There is {self.time_to_full or ''} of time left until full charge! Better to not spoil your battery!",
                icon="perfect",
                timeout=NOTIFICATION_TIMEOUT,
                urgency=Urgency.Normal,
            )
        )

        logger.debug("Removal warning sent successfully")

    def send_overflow_warning(self):
        logger.info("Sending overflow warning")
        if self.percentage >= 100:
            self.notification_queue.put_nowait(
                dict(
                    title="Please Stop Charging!",
                    message="It's 100% charged! To not ruin your computer battery turn off the charger!",
                    icon="too-much",
                    timeout=NOTIFICATION_TIMEOUT,
                    urgency=Urgency.Critical,
                )
            )
        else:
            self.notification_queue.put_nowait(
                dict(
                    title="Please Stop Charging!",
                    message=f"It's {self.percentage:.1f}% charged! To not ruin your computer battery turn off the charger!",
                    icon="too-much",
                    timeout=NOTIFICATION_TIMEOUT,
                    urgency=Urgency.Critical,
                )
            )

        logger.debug("Overflow warning sent successfully")

    def send_charge_reminder(self):
        logger.info("Sending charge reminder")
        self.notification_queue.put_nowait(
            dict(
                title="Battery too low!",
                message=f"You have only {self.percentage:.1f}% battery left which will last for {self.time_to_empty}. Charge quickly!",
                icon="oh-no",
                timeout=NOTIFICATION_TIMEOUT,
                urgency=Urgency.Critical,
            )
        )

        logger.debug("Charge reminder sent successfully")

    @staticmethod
    def send_updated_settings_message(critical_notifications_queue):
        logger.info("Sending settings update message")
        critical_notifications_queue.put_nowait(
            dict(
                title="Settings Updated Successfully!",
                message="Your battery monitoring settings have been saved and applied.",
                icon="yes",
                timeout=NOTIFICATION_TIMEOUT,
                urgency=Urgency.Normal,
            )
        )

        logger.debug("Settings update message sent successfully")

    def reminder_time_passed(
        self,
        event_name: EVENTS,
        elapsed_time_in_seconds: int,
        reset_timer: bool = False,
    ) -> bool:
        if reset_timer:
            self.timers[event_name] = time.time()
            logger.debug(f"Reset timer for event: {event_name}")
            return False

        if event_name not in self.timers:
            self.timers[event_name] = time.time()
            logger.debug(f"Initialized timer for event: {event_name}")
            return True

        out = time.time() - self.timers[event_name] >= elapsed_time_in_seconds
        if out:
            self.timers[event_name] = time.time()
            logger.debug(f"Timer passed for event: {event_name}")
        return out

    def send_power_state_changed_message(self):
        logger.info("Sending power state changed message")
        self.notification_queue.put_nowait(
            dict(
                title="⚡ Power Mode Changed",
                message="Your laptop has been switched to Power Saver mode to extend battery life.",
                icon="yes",
                timeout=NOTIFICATION_TIMEOUT,
                urgency=Urgency.Normal,
            )
        )

    def send_power_state_reset_message(self):
        logger.info("Sending power state reset message")
        # Use the configured default power plan for the message
        default_power_plan = self.config["PROC_SETTINGS"]["default_power_plan"]
        self.notification_queue.put_nowait(
            dict(
                title="⚡ Power Mode Restored",
                message=f"Your laptop has been restored to {default_power_plan} mode as battery level has improved.",
                icon="yes",
                timeout=NOTIFICATION_TIMEOUT,
                urgency=Urgency.Normal,
            )
        )

    def update(self):
        try:
            self.battery.refresh()
            self.current_battery_state = self.get_battery_state()
            logger.debug(
                f"Battery state: {self.current_battery_state}, Charger state: {self.current_charger_state}"
            )

            if self.battery.state != self.current_charger_state:
                new_state = self.battery.state
                logger.info(
                    f"Charger state changed from {self.current_charger_state} to {new_state}"
                )
                if new_state == "Charging":
                    if self.config["PROC_SETTINGS"]["alert_when_charger_plugged"]:
                        self.send_charging_message()
                else:
                    if self.config["PROC_SETTINGS"]["alert_when_charger_removed"]:
                        self.send_discharging_message()

                self.current_charger_state = new_state
                logger.debug("state changed")

            elif self.current_charger_state == "Charging":
                charge_amount = self.battery.percent.value
                pause_time = self.config["PROC_SETTINGS"]["remind_high_charge_time"]

                if charge_amount >= self.config["PROC_SETTINGS"][
                    "overflow_percent"
                ] and self.reminder_time_passed(
                    "overflow",
                    self.config["PROC_SETTINGS"]["remind_overflow_charge_time"],
                ):  # 2 min
                    self.send_overflow_warning()
                elif charge_amount >= self.config["PROC_SETTINGS"][
                    "high_charge_percent"
                ] and self.reminder_time_passed("high", pause_time):
                    self.send_removal_warning()

            elif self.current_charger_state == "Discharging":
                charge_amount = self.battery.percent.value
                pause_time = self.config["PROC_SETTINGS"]["remind_low_charge_time"]

                if charge_amount <= self.config["PROC_SETTINGS"][
                    "low_charge_percent"
                ] and self.reminder_time_passed("min", pause_time):
                    self.send_charge_reminder()

            if self.can_change_power_state:
                if (
                    self.config["PROC_SETTINGS"]["save_power_state_at_percent"]
                    is not None
                    and not self.power_state_changed
                ):
                    charge_amount = self.battery.percent.value

                    if (
                        charge_amount
                        <= self.config["PROC_SETTINGS"]["save_power_state_at_percent"]
                    ):
                        powerplan.change_current_scheme_to_powersaver()
                        self.send_power_state_changed_message()
                        self.power_state_changed = True

                if (
                    self.power_state_changed
                    and self.config["PROC_SETTINGS"]["save_power_state_at_percent"]
                ):
                    charge_amount = self.battery.percent.value

                    if (
                        charge_amount
                        > self.config["PROC_SETTINGS"]["save_power_state_at_percent"]
                    ):
                        # Use the configured default power plan instead of the original power state
                        default_power_plan = self.config["PROC_SETTINGS"][
                            "default_power_plan"
                        ]
                        if default_power_plan in POWER_STATES:
                            POWER_STATES[default_power_plan]()
                        else:
                            # Fallback to original power state if configured plan is not available
                            POWER_STATES[self.default_power_state]()
                        self.send_power_state_reset_message()
                        self.power_state_changed = False

        except Exception as e:
            logger.exception("Error in battery update process")
            raise

    def update_config(self, config: AppConfig):
        logger.info("Updating background process configuration")
        self.default_power_state = powerplan.get_current_scheme_name()

        # Only reset power state if we haven't changed it ourselves
        if not self.power_state_changed:
            try:
                # Use the configured default power plan instead of current power state
                default_power_plan = config["PROC_SETTINGS"]["default_power_plan"]
                if default_power_plan in POWER_STATES:
                    POWER_STATES[default_power_plan]()
                    logger.debug(f"Reset power state to: {default_power_plan}")
                else:
                    # Fallback to current power state if configured plan is not available
                    POWER_STATES[self.default_power_state]()
                    logger.debug(f"Reset power state to: {self.default_power_state}")
            except KeyError:
                logger.warning(f"Unknown power state: {self.default_power_state}")
            except Exception as e:
                logger.error(f"Failed to reset power state: {e}")

        self.can_change_power_state = (
            self.default_power_state
            not in [
                "Power saver",
                "UNKNOWN",
            ]
            and self.config["PROC_SETTINGS"]["save_power_state_at_percent"]
        )

        self.config = config
        self.send_updated_settings_message(self.critical_notifications_queue)
        logger.debug("Configuration updated successfully")


# atexit.register(lambda: asyncio.run(clear_all_messages()))


def main(
    notifications_queue: multiprocessing.Queue,
    critical_notifications_queue: multiprocessing.Queue,
    stop_bg_proc_flag: SynchronizedBase,
    settings_updated_flag: SynchronizedBase,
):
    try:
        logger.info("Starting background process main loop")
        new_proc = BackgroundProcessManager(
            notifications_queue,
            critical_notifications_queue,
        )

        new_proc.send_welcome_message()

        # with stop_bg_proc_flag.get_lock():

        while not stop_bg_proc_flag.value:
            try:
                if settings_updated_flag.value:
                    new_proc.update_config(load_config())
                    settings_updated_flag.value = False

                new_proc.update()
                time.sleep(1)
            except Exception as e:
                logger.exception("Error in main loop iteration")
                time.sleep(5)  # Wait a bit longer after an error

        logger.info("Background process stopping...")

        # await clear_all_messages()
        # await app.send_process_stopped_message()

        logger.info("Background process stopped successfully")
    except Exception as e:
        logger.exception("Fatal error in background process")
        raise


def run_background_process(
    notifications_queue: multiprocessing.Queue,
    critical_notifications_queue: multiprocessing.Queue,
    stop_bg_proc_flag: SynchronizedBase,
    settings_updated_flag: SynchronizedBase,
):
    try:
        logger.info("Starting background Process")

        proc = multiprocessing.Process(
            target=main,
            daemon=True,
            args=(
                notifications_queue,
                critical_notifications_queue,
                stop_bg_proc_flag,
                settings_updated_flag,
            ),
        )
        proc.start()

        logger.info("Background process started successfully")

        return proc
    except Exception as e:
        logger.exception("Fatal error in background Process")
        raise
