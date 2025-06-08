import time
import asyncio
import atexit
from pathlib import Path
from typing import Literal
from batteryinfo import Battery, TimeFormat
from desktop_notifier import DesktopNotifier, Icon, Urgency
from .config import DEFAULT_CONFIG_DATA, AppConfig, get_app_name, load_config
from .assets_manager import get_emoji
from .utils import SingletonMeta

import threading
from concurrent.futures import ThreadPoolExecutor

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich import print


NOTIFICATION_TIMEOUT = -1

BATTERY_STATE = {
    "OVERLFLOW": "IN OVERFLOW",
    "HIGH": "IN HIGH STATE",
    "NORMAL": "Between LOW and HIGH",
    "LOW": "LOW STATE",
}

EVENTS = Literal["overflow", "high", "min"]


class _Battery:
    class Measurement:
        def __init__(self, value, unit="%"):
            self._value = value
            self._unit = unit

        @property
        def value(self):
            return self._value

        @property
        def unit(self):
            return self._unit

        def __str__(self):
            return f"{self.value}{self.unit}"

    def __init__(self):
        # We still initialize the real Battery object if you need its other properties
        self.battery = Battery(time_format=TimeFormat.Human)
        # This will be our controlled percentage for testing
        self._test_percentage = 0.0
        # This will store the state (Charging/Discharging) for testing
        self._test_state = "Discharging"

    @property
    def state(self):
        return self._test_state

    @property
    def percent(self):
        # Now, `percent` will return a Measurement object based on your manually set value
        return _Battery.Measurement(self._test_percentage, "%")

    # Method to set the percentage for testing
    def set_test_percentage(self, value: float):
        if not (0 <= value <= 100):
            raise ValueError("Percentage value must be between 0 and 100.")
        self._test_percentage = value

    # # Method to set the charger state for testing
    def set_test_state(self, state: Literal["Charging", "Discharging"]):
        if state not in ["Charging", "Discharging"]:
            raise ValueError("State must be 'Charging', 'Discharging', or 'Full'.")
        self._test_state = state

    # We keep __getattr__ for other attributes that you might still want from the real battery,
    # or for attributes that are not explicitly mocked or set for testing.
    def __getattr__(self, item):
        # This will still attempt to get attributes from the real battery object
        # if they are not defined in _Battery directly (like percent or state are now).
        return getattr(self.battery, item)


class BackgroundProcessManager(metaclass=SingletonMeta):
    def __init__(self, app_name=get_app_name()) -> None:
        self.battery = _Battery()  # Battery(time_format=TimeFormat.Human)
        self.notifier = DesktopNotifier(app_name=app_name, notification_limit=5)
        self.current_charger_state = self.battery.state
        self.current_battery_state = BATTERY_STATE["NORMAL"]
        self.timers = {}

        self.notifications = []

    def get_battery_data(self):
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

    def get_battery_state(self, config: AppConfig):
        charge_amount = self.battery.percent.value
        state = BATTERY_STATE["NORMAL"]

        if charge_amount >= 98:  # 2 min
            state = BATTERY_STATE["OVERLFLOW"]
        elif charge_amount >= config["PROC_SETTINGS"]["high_charge_percent"]:
            state = BATTERY_STATE["HIGH"]
        elif charge_amount <= config["PROC_SETTINGS"]["low_charge_percent"]:
            state = BATTERY_STATE["LOW"]

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
        if self.is_charging:
            message = f"You are currently charging your laptop. {self.time_to_full} until 100% charge!"
        else:
            message = f"You have {self.percentage:.1f}% charge which amount to {self.time_to_empty} of time left!"

        notification = await self.notifier.send(
            title="Process Started!",
            message="Hello I have started the battery monitoring process! " + message,
            icon=Icon(get_emoji("plain")),
            timeout=NOTIFICATION_TIMEOUT,
        )

        self.notifications.append(notification)

    async def send_charging_message(self):
        if self.current_battery_state == BATTERY_STATE["OVERLFLOW"]:
            notification = await self.notifier.send(
                title="Please STOP Charging",
                message=f"You are already {self.percentage:.1f}% Charged!! Any longer and you could ruin your battery! You dont need to charge any further!",
                icon=Icon(get_emoji("too-much")),
                timeout=NOTIFICATION_TIMEOUT,
            )
            self.reminder_time_passed("high", 0, True)
        elif self.current_battery_state == BATTERY_STATE["HIGH"]:
            notification = await self.notifier.send(
                title="You dont need to Charge",
                message=f"You are already {self.percentage:.1f}% Charged! You dont need to charge any further",
                icon=Icon(get_emoji("perfect")),
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

    async def send_discharging_message(self):
        if self.current_battery_state == BATTERY_STATE["LOW"]:
            notification = await self.notifier.send(
                title="Dont Stop Charging!",
                message=f"You have {self.time_to_empty or ''} of Charge Left! Currently there is {self.percentage:.1f}% charge left. You need to charge some more!",
                icon=Icon(get_emoji("happy")),
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

    async def send_removal_warning(self):
        notification = await self.notifier.send(
            title=f"Its {self.percentage:.1f}% Full",
            message=f"You should remove the charger now! There is {self.time_to_full or ''} of time left until full charge! Better to not spoil your battery!",
            icon=Icon(get_emoji("perfect")),
            timeout=NOTIFICATION_TIMEOUT,
        )

        self.notifications.append(notification)

    async def send_overflow_warning(self):
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

    async def send_charge_reminder(self):
        notification = await self.notifier.send(
            title="Battery too low!",
            message=f"You have only {self.percentage:.1f}% battery left which will last for {self.time_to_empty}. Charge quickly!",
            icon=Icon(get_emoji("oh-no")),
            timeout=NOTIFICATION_TIMEOUT,
        )

        self.notifications.append(notification)

    async def send_updated_settings_message(self):
        notification = await self.notifier.send(
            title="Settings Updated!",
            message="The settings has been changed and saved successfuly!",
            icon=Icon(get_emoji("yes")),
            timeout=NOTIFICATION_TIMEOUT,
        )

        self.notifications.append(notification)

    def reminder_time_passed(
        self,
        event_name: EVENTS,
        elapsed_time_in_seconds: int,
        reset_timer: bool = False,
    ) -> bool:
        if reset_timer:
            self.timers[event_name] = time.time()
            return False

        # print(f"checking {event_name}")
        if event_name not in self.timers:
            self.timers[event_name] = time.time()
            return True

        out = time.time() - self.timers[event_name] >= elapsed_time_in_seconds
        if out:
            self.timers[event_name] = time.time()
        return out

    async def update(self, config: AppConfig):
        self.battery.refresh()
        self.current_battery_state = self.get_battery_state(config)
        print(self.percentage, "-", self.current_battery_state)
        print(self.current_charger_state)

        if self.battery.state != self.current_charger_state:
            new_state = self.battery.state
            if new_state == "Charging":
                if config["PROC_SETTINGS"]["alert_when_charger_plugged"]:
                    await self.send_charging_message()
            else:
                if config["PROC_SETTINGS"]["alert_when_charger_removed"]:
                    await self.send_discharging_message()

            self.current_charger_state = new_state
            print("state changed")

        if self.current_charger_state == "Charging":
            charge_amount = self.battery.percent.value
            pause_time = config["PROC_SETTINGS"]["remind_high_charge_time"]

            if charge_amount >= config["PROC_SETTINGS"][
                "overflow_percent"
            ] and self.reminder_time_passed(
                "overflow", config["PROC_SETTINGS"]["remind_overflow_charge_time"]
            ):  # 2 min
                await self.send_overflow_warning()
            elif charge_amount >= config["PROC_SETTINGS"][
                "high_charge_percent"
            ] and self.reminder_time_passed("high", pause_time):
                await self.send_removal_warning()

        elif self.current_charger_state == "Discharging":
            charge_amount = self.battery.percent.value
            pause_time = config["PROC_SETTINGS"]["remind_low_charge_time"]

            if charge_amount <= config["PROC_SETTINGS"][
                "low_charge_percent"
            ] and self.reminder_time_passed("min", pause_time):
                await self.send_charge_reminder()

        if len(self.notifications) > 5:
            await self.notifier.clear(self.notifications[0])
            self.notifications.pop(0)

    async def clear_all_messages(self):
        await self.notifier.clear_all()


progress = Progress(
    TextColumn("[bold blue] Charge %", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
)


async def proc(app: BackgroundProcessManager):
    config = load_config()
    await app.send_welcome_message()
    try:
        while True:
            await app.update(config)
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("\nBackground process cancelled")
        raise


async def main():
    app = BackgroundProcessManager()
    loop = asyncio.get_running_loop()

    # Create separate event loop for background thread
    executor = ThreadPoolExecutor()
    background_loop = asyncio.new_event_loop()
    background_future = loop.run_in_executor(executor, background_loop.run_forever)

    # Schedule proc in background loop
    proc_task = asyncio.run_coroutine_threadsafe(proc(app), background_loop)

    try:
        # Progress handling in main thread
        with progress:
            task = progress.add_task("Charging")
            progress.console.log(f"Requesting Charge...")
            progress.start_task(task)

            i = 0
            while i < 105:
                try:
                    next_input = input("next: ")
                    if next_input == "c":
                        app.battery.set_test_state("Charging")
                        continue
                    elif next_input == "d":
                        app.battery.set_test_state("Discharging")
                        continue
                    advance = int(next_input) if next_input else 1
                    progress.update(task, advance=advance)
                    i += advance
                    app.battery.set_test_percentage(i)
                except KeyboardInterrupt:
                    print("\nOperation cancelled by user")
                    break

            progress.console.log(f"Downloaded")

    finally:
        # Cleanup
        proc_task.cancel()
        background_loop.call_soon_threadsafe(background_loop.stop)
        executor.shutdown(wait=False)


def clear_all_messages():
    app = BackgroundProcessManager()
    asyncio.run(app.clear_all_messages())


atexit.register(clear_all_messages)


if __name__ == "__main__":
    asyncio.run(main())
