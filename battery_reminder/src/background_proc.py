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
import asyncio
import atexit
from pathlib import Path
from typing import Literal
from batteryinfo import Battery, TimeFormat
from battery_reminder.src.app_config_manager import (
    DEFAULT_CONFIG_DATA,
    AppConfig,
    get_app_name,
    load_config,
)
from battery_reminder.src.assets_manager import get_emoji
from battery_reminder.src.utils import SingletonMeta
from battery_reminder.src.logger_config import setup_logger

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
        queue: multiprocessing.Queue,
        app_name=get_app_name(),
        _class=Battery,
    ) -> None:
        logger.info("Initializing background process manager...")
        self.battery: Battery = _class(time_format=TimeFormat.Human)
        # self.notifier = DesktopNotifier(app_name=app_name, notification_limit=5)
        self.current_charger_state = self.battery.state
        self.current_battery_state = BATTERY_STATE["NORMAL"]
        self.timers = {}

        self.notification_queue = queue
        self.config = load_config()
        logger.info("Background process manager initialized successfully")

        self.notifications_to_send = []

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
            message = f"You are currently charging your laptop, Its {self.percentage:.1f}%. {self.time_to_full} until 100% charge!"
        else:
            message = f"You have {self.percentage:.1f}% charge which amount to {self.time_to_empty} of time left!"

        self.notification_queue.put_nowait(
            dict(
                title="Process Started!",
                message="Hello I have started the battery monitoring process! "
                + message,
                icon="plain",
                timeout=NOTIFICATION_TIMEOUT,
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
                )
            )
            self.reminder_time_passed("high", 0, True)
        else:
            self.notification_queue.put_nowait(
                dict(
                    title="Started Charging!",
                    message=f"It will take another {self.time_to_full or ''} to fully charge! Currently its {self.percentage:.1f}% full",
                    icon="happy",
                    timeout=NOTIFICATION_TIMEOUT,
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
                )
            )
            self.reminder_time_passed("min", 0, True)
        else:
            self.notification_queue.put_nowait(
                dict(
                    title="Stopped Charging!",
                    message=f"You have {self.time_to_empty or ''} of Charge Left! Currently there is {self.percentage:.1f}% charge left",
                    icon="happy",
                    timeout=NOTIFICATION_TIMEOUT,
                )
            )
        logger.debug("Discharging message sent successfully")

    def send_removal_warning(self):
        logger.info("Sending removal warning")
        # TODO: URGENCY
        self.notification_queue.put_nowait(
            dict(
                title=f"Its {self.percentage:.1f}% Full",
                message=f"You should remove the charger now! There is {self.time_to_full or ''} of time left until full charge! Better to not spoil your battery!",
                icon="perfect",
                timeout=NOTIFICATION_TIMEOUT,
            )
        )

        logger.debug("Removal warning sent successfully")

    def send_overflow_warning(self):
        logger.info("Sending overflow warning")
        if self.percentage == 100:
            self.notification_queue.put_nowait(
                dict(
                    title="Please Stop Charging!",
                    message="It's 100% charged! To not ruin your computer battery turn off the charger!",
                    icon="too-much",
                    timeout=NOTIFICATION_TIMEOUT,
                )
            )
        else:
            self.notification_queue.put_nowait(
                dict(
                    title="Please Stop Charging!",
                    message=f"It's {self.percentage}% charged! To not ruin your computer battery turn off the charger!",
                    icon="too-much",
                    timeout=NOTIFICATION_TIMEOUT,
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
            )
        )

        logger.debug("Charge reminder sent successfully")

    def send_updated_settings_message(self):
        logger.info("Sending settings update message")
        self.notification_queue.put_nowait(
            dict(
                title="Settings Updated!",
                message="The settings has been changed and saved successfuly!",
                icon="yes",
                timeout=0,
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

    def update(self):
        try:
            self.battery.refresh()
            self.current_battery_state = self.get_battery_state()
            logger.debug(
                f"Battery state: {self.current_battery_state}, Charger state: {self.current_charger_state}"
            )

            # if self.notifications_to_send:
            #     await self.notifications_to_send.pop(0)()

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

            # if len(self.notifications) > 5:
            #     await self.notifier.clear(self.notifications[0])
            #     self.notifications.pop(0)
        except Exception as e:
            logger.exception("Error in battery update process")
            raise

    # def clear_all_messages(self):
    #     logger.info("Clearing all notifications")
    #     await self.notifier.clear_all()
    #     self.notifications.clear()
    #     logger.debug("All notifications cleared")

    def update_config(self, config: AppConfig):
        logger.info("Updating background process configuration")
        self.config = config
        self.send_updated_settings_message()
        logger.debug("Configuration updated successfully")


# atexit.register(lambda: asyncio.run(clear_all_messages()))


def main(
    notifications_queue: multiprocessing.Queue,
    stop_bg_proc_flag: SynchronizedBase,
    settings_updated_flag: SynchronizedBase,
):
    try:
        logger.info("Starting background process main loop")
        new_proc = BackgroundProcessManager(notifications_queue)

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
