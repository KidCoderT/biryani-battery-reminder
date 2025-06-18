import time
import asyncio
import atexit
from pathlib import Path
from typing import Literal
from batteryinfo import Battery, TimeFormat
from desktop_notifier import DesktopNotifier, Icon, Urgency
from battery_reminder.src.config import (
    DEFAULT_CONFIG_DATA,
    AppConfig,
    get_app_name,
    load_config,
)
from battery_reminder.src.assets_manager import get_emoji
from battery_reminder.src.utils import SingletonMeta
from battery_reminder.src.logger_config import setup_logger

import threading

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


class BackgroundProcessManager(metaclass=SingletonMeta):
    def __init__(self, app_name=get_app_name(), _class=Battery) -> None:
        logger.info("Initializing background process manager...")
        self.battery: Battery = _class(time_format=TimeFormat.Human)
        self.notifier = DesktopNotifier(app_name=app_name, notification_limit=5)
        self.current_charger_state = self.battery.state
        self.current_battery_state = BATTERY_STATE["NORMAL"]
        self.timers = {}

        self.notifications = []
        self.config = load_config()
        logger.info("Background process manager initialized successfully")

        self.notifications_to_send = []

    def get_battery_data(self):
        logger.debug("Fetching battery data")
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

    async def send_welcome_message(self):
        logger.info("Sending welcome message")
        if self.is_charging:
            message = f"You are currently charging your laptop, Its {self.percentage:.1f}%. {self.time_to_full} until 100% charge!"
        else:
            message = f"You have {self.percentage:.1f}% charge which amount to {self.time_to_empty} of time left!"

        notification = await self.notifier.send(
            title="Process Started!",
            message="Hello I have started the battery monitoring process! " + message,
            icon=Icon(get_emoji("plain")),
            timeout=NOTIFICATION_TIMEOUT,
        )

        self.notifications.append(notification)
        logger.debug("Welcome message sent successfully")

    async def send_charging_message(self):
        logger.info("Sending charging message")
        if self.current_battery_state == BATTERY_STATE["OVERLFLOW"]:
            notification = await self.notifier.send(
                title="Please STOP Charging",
                message=f"You are already {self.percentage:.1f}% Charged!! Any longer and you could ruin your battery! You dont need to charge any further!",
                icon=Icon(get_emoji("too-much-2")),
                timeout=NOTIFICATION_TIMEOUT,
            )
            self.reminder_time_passed("high", 0, True)
        elif self.current_battery_state == BATTERY_STATE["HIGH"]:
            notification = await self.notifier.send(
                title="You dont need to Charge",
                message=f"You are already {self.percentage:.1f}% Charged! You dont need to charge any further",
                icon=Icon(get_emoji("hehe")),
                timeout=NOTIFICATION_TIMEOUT,
            )
            self.reminder_time_passed("high", 0, True)
        else:
            notification = await self.notifier.send(
                title="Started Charging!",
                message=f"It will take another {self.time_to_full or ''} to fully charge! Currently its {self.percentage:.1f}% full",
                icon=Icon(get_emoji("happy")),
                timeout=NOTIFICATION_TIMEOUT,
            )

        self.notifications.append(notification)
        logger.debug("Charging message sent successfully")

    async def send_discharging_message(self):
        logger.info("Sending discharging message")
        if self.current_battery_state == BATTERY_STATE["LOW"]:
            notification = await self.notifier.send(
                title="Dont Stop Charging!",
                message=f"You have {self.time_to_empty or ''} of Charge Left! Currently there is {self.percentage:.1f}% charge left. You need to charge some more!",
                icon=Icon(get_emoji("oh-no")),
                timeout=NOTIFICATION_TIMEOUT,
            )
            self.reminder_time_passed("min", 0, True)
        else:
            notification = await self.notifier.send(
                title="Stopped Charging!",
                message=f"You have {self.time_to_empty or ''} of Charge Left! Currently there is {self.percentage:.1f}% charge left",
                icon=Icon(get_emoji("happy")),
                timeout=NOTIFICATION_TIMEOUT,
            )
        self.notifications.append(notification)
        logger.debug("Discharging message sent successfully")

    async def send_removal_warning(self):
        logger.info("Sending removal warning")
        notification = await self.notifier.send(
            title=f"Its {self.percentage:.1f}% Full",
            message=f"You should remove the charger now! There is {self.time_to_full or ''} of time left until full charge! Better to not spoil your battery!",
            icon=Icon(get_emoji("perfect")),
            timeout=NOTIFICATION_TIMEOUT,
            urgency=Urgency.Critical,
        )

        self.notifications.append(notification)
        logger.debug("Removal warning sent successfully")

    async def send_overflow_warning(self):
        logger.info("Sending overflow warning")
        if self.percentage == 100:
            notification = await self.notifier.send(
                title="Please Stop Charging!",
                message="It's 100% charged! To not ruin your computer battery turn off the charger!",
                icon=Icon(get_emoji("too-much")),
                urgency=Urgency.Critical,
                timeout=NOTIFICATION_TIMEOUT,
            )
        else:
            notification = await self.notifier.send(
                title="Please Stop Charging!",
                message=f"It's {self.percentage}% charged! To not ruin your computer battery turn off the charger!",
                icon=Icon(get_emoji("too-much")),
                urgency=Urgency.Critical,
                timeout=NOTIFICATION_TIMEOUT,
            )

        self.notifications.append(notification)
        logger.debug("Overflow warning sent successfully")

    async def send_charge_reminder(self):
        logger.info("Sending charge reminder")
        notification = await self.notifier.send(
            title="Battery too low!",
            message=f"You have only {self.percentage:.1f}% battery left which will last for {self.time_to_empty}. Charge quickly!",
            icon=Icon(get_emoji("oh-no")),
            timeout=NOTIFICATION_TIMEOUT,
            urgency=Urgency.Critical,
        )

        self.notifications.append(notification)
        logger.debug("Charge reminder sent successfully")

    async def send_updated_settings_message(self):
        logger.info("Sending settings update message")
        notification = await self.notifier.send(
            title="Settings Updated!",
            message="The settings has been changed and saved successfuly!",
            icon=Icon(get_emoji("yes")),
            timeout=0,
        )

        self.notifications.append(notification)
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

    async def update(self):
        try:
            self.battery.refresh()
            self.current_battery_state = self.get_battery_state()
            logger.debug(
                f"Battery state: {self.current_battery_state}, Charger state: {self.current_charger_state}"
            )

            if self.notifications_to_send:
                await self.notifications_to_send.pop(0)()

            if self.battery.state != self.current_charger_state:
                new_state = self.battery.state
                logger.info(
                    f"Charger state changed from {self.current_charger_state} to {new_state}"
                )
                if new_state == "Charging":
                    if self.config["PROC_SETTINGS"]["alert_when_charger_plugged"]:
                        await self.send_charging_message()
                else:
                    if self.config["PROC_SETTINGS"]["alert_when_charger_removed"]:
                        await self.send_discharging_message()

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
                    await self.send_overflow_warning()
                elif charge_amount >= self.config["PROC_SETTINGS"][
                    "high_charge_percent"
                ] and self.reminder_time_passed("high", pause_time):
                    await self.send_removal_warning()

            elif self.current_charger_state == "Discharging":
                charge_amount = self.battery.percent.value
                pause_time = self.config["PROC_SETTINGS"]["remind_low_charge_time"]

                if charge_amount <= self.config["PROC_SETTINGS"][
                    "low_charge_percent"
                ] and self.reminder_time_passed("min", pause_time):
                    await self.send_charge_reminder()

            if len(self.notifications) > 5:
                await self.notifier.clear(self.notifications[0])
                self.notifications.pop(0)
        except Exception as e:
            logger.exception("Error in battery update process")
            raise

    async def clear_all_messages(self):
        logger.info("Clearing all notifications")
        await self.notifier.clear_all()
        self.notifications.clear()
        logger.debug("All notifications cleared")

    def update_config(self, config: AppConfig):
        logger.info("Updating background process configuration")
        self.notifications_to_send.append(self.send_updated_settings_message)
        self.config = config
        logger.debug("Configuration updated successfully")

    async def send_process_stopped_message(self):
        logger.info("Sending stop message")

        notification = await self.notifier.send(
            title="Background Process Stopped!",
            message="Be ware I will no longer remind you if you overcharge your battery!",
            icon=Icon(get_emoji("oh-no")),
            timeout=0,
        )

        await asyncio.sleep(1)

        logger.debug("Stop message sent successfully")


async def clear_all_messages():
    try:
        logger.info("Clearing all messages")
        app = BackgroundProcessManager()
        await app.clear_all_messages()
        logger.debug("All messages cleared successfully")
    except Exception as e:
        logger.exception("Error clearing messages")
        raise


# atexit.register(lambda: asyncio.run(clear_all_messages()))

stop_background_process_flag = threading.Event()


async def main():
    try:
        logger.info("Starting background process main loop")
        app = BackgroundProcessManager()
        print(await app.notifier.has_authorisation())
        if not await app.notifier.has_authorisation():
            await app.notifier.request_authorisation()
        await clear_all_messages()

        await app.send_welcome_message()

        while not stop_background_process_flag.is_set():
            try:
                await app.update()
                await asyncio.sleep(1)
            except Exception as e:
                logger.exception("Error in main loop iteration")
                await asyncio.sleep(5)  # Wait a bit longer after an error

        logger.info("Background process stopping...")

        await clear_all_messages()
        await app.send_process_stopped_message()

        logger.info("Background process stopped successfully")
    except Exception as e:
        logger.exception("Fatal error in background process")
        raise


def run_background_process():
    try:
        logger.info("Starting background process thread")
        asyncio.run(main())
    except Exception as e:
        logger.exception("Fatal error in background process thread")
        raise
