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
        self.battery: Battery = _class(time_format=TimeFormat.Human)
        self.notifier = DesktopNotifier(app_name=app_name, notification_limit=5)
        self.current_charger_state = self.battery.state
        self.current_battery_state = BATTERY_STATE["NORMAL"]
        self.timers = {}

        self.notifications = []
        self.config = load_config()

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

    def get_battery_state(self):
        charge_amount = self.battery.percent.value
        state = BATTERY_STATE["NORMAL"]

        if charge_amount >= self.config["PROC_SETTINGS"]["overflow_percent"]:  # 2 min
            state = BATTERY_STATE["OVERLFLOW"]
        elif charge_amount >= self.config["PROC_SETTINGS"]["high_charge_percent"]:
            state = BATTERY_STATE["HIGH"]
        elif charge_amount <= self.config["PROC_SETTINGS"]["low_charge_percent"]:
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

    async def send_charging_message(self):
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

    async def send_discharging_message(self):
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

    async def update(self):
        self.battery.refresh()
        self.current_battery_state = self.get_battery_state()
        # print(self.percentage, "-", self.current_battery_state)
        # print(self.current_charger_state)

        if self.battery.state != self.current_charger_state:
            new_state = self.battery.state
            if new_state == "Charging":
                if self.config["PROC_SETTINGS"]["alert_when_charger_plugged"]:
                    await self.send_charging_message()
            else:
                if self.config["PROC_SETTINGS"]["alert_when_charger_removed"]:
                    await self.send_discharging_message()

            self.current_charger_state = new_state
            print("state changed")

        elif self.current_charger_state == "Charging":
            charge_amount = self.battery.percent.value
            pause_time = self.config["PROC_SETTINGS"]["remind_high_charge_time"]

            if charge_amount >= self.config["PROC_SETTINGS"][
                "overflow_percent"
            ] and self.reminder_time_passed(
                "overflow", self.config["PROC_SETTINGS"]["remind_overflow_charge_time"]
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

    async def clear_all_messages(self):
        await self.notifier.clear_all()

    def update_config(self, config: AppConfig):
        print("CONFIG UPDATED")
        self.config = config


def clear_all_messages():
    app = BackgroundProcessManager()
    asyncio.run(app.clear_all_messages())


atexit.register(clear_all_messages)

stop_background_process_flag = threading.Event()


async def main():
    """
    The main asynchronous routine for your background process.
    It coordinates the background tasks and checks for shutdown signals.
    """
    app = BackgroundProcessManager()

    await app.send_welcome_message()

    while not stop_background_process_flag.is_set():
        await app.update()

        # Asynchronously wait for 1 second, but allow interruption if the
        # stop flag is set. This is crucial for graceful shutdown.
        try:
            # asyncio.wait_for will raise TimeoutError if event doesn't get set
            # within 1 second. This allows the loop to continue.
            # If the event IS set, it will complete immediately and raise.
            # We specifically want to break if the flag is set.
            await asyncio.wait_for(
                asyncio.create_task(
                    asyncio.to_thread(
                        stop_background_process_flag.wait
                    )  # Run blocking wait in a thread pool
                ),
                timeout=1.0,
            )

            # If the above line completes without timeout, it means the flag was set, so break
            # ie -> THE PROGRAM WAS TERMINATED
            break

        except asyncio.TimeoutError:
            # The flag was not set within the timeout, so continue the loop
            pass
        except Exception as e:
            # Catch other potential errors during shutdown handling
            print(f"Error during async shutdown check: {e}")
            break  # Exit loop on error

    print("Background process: Signaled to stop and exiting async loop.")


def run_background_process():
    """
    This function is executed in a dedicated background thread.
    It's responsible for creating and running the asyncio event loop
    for the `proc` coroutine.
    """
    print("Background process thread: Starting asyncio loop for 'proc'...")
    try:
        # asyncio.run() creates a new event loop for the current thread,
        # runs the coroutine, and then closes the loop.
        asyncio.run(main())
    except RuntimeError as e:
        # This can sometimes happen if the event loop is already shutting down
        # or closed during cleanup. We'll catch specific errors if needed.
        if "Event loop is closed" not in str(e):
            raise  # Re-raise if it's not the expected shutdown error
    except Exception as e:
        print(f"Background process thread encountered an unexpected error: {e}")
    finally:
        print("Background process thread: Asyncio loop has stopped.")
