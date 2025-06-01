import time
import asyncio
from pathlib import Path
from typing import Literal
import batteryinfo
from desktop_notifier import DesktopNotifier, Icon, Urgency
from .config import DEFAULT_CONFIG_DATA, AppConfig
from .assets_manager import get_emoji


APP_NAME = "battery-reminder"


class App:
    def __init__(self, app_name=APP_NAME) -> None:
        self.battery = batteryinfo.Battery(time_format=batteryinfo.TimeFormat.Human)
        self.notifier = DesktopNotifier(app_name=app_name, notification_limit=5)
        self.current_state = self.battery.state
        self.timers = {}

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

        await self.notifier.send(
            title="Process Started!",
            message="Hello I have started the battery monitoring process! " + message,
            icon=Icon(get_emoji("plain")),
        )

    async def send_charging_message(self):
        await self.notifier.send(
            title="Started Charging!",
            message=f"It will take another {self.time_to_full or ''} to fully charge! Currently its {self.percentage:.1f}% full",
            icon=Icon(get_emoji("happy")),
        )

    async def send_discharging_message(self):
        await self.notifier.send(
            title="Stopped Charging!",
            message=f"You have {self.time_to_empty or ''} of Charge Left! Currently there is {self.percentage:.1f}% charge left",
            icon=Icon(get_emoji("happy")),
        )

    async def send_removal_warning(self):
        await self.notifier.send(
            title=f"Its {self.percentage:.1f}% Full",
            message=f"You should remove the charger now! There is {self.time_to_full or ''} of time left until full charge! Better to not spoil your battery!",
            icon=Icon(get_emoji("perfect")),
        )

    async def send_overflow_warning(self):
        await self.notifier.send(
            title="Please Stop Charging!",
            message=f"Its 100% charge pretty much. To not ruin your computer battery turn of the charger!",
            icon=Icon(get_emoji("too-much")),
            urgency=Urgency.Critical,
        )

    async def send_charge_reminder(self):
        await self.notifier.send(
            title="Battery too low!",
            message=f"You have only {self.percentage:.1f}% battery left which will last for {self.time_to_empty}. Charge quickly!",
            icon=Icon(get_emoji("oh-no")),
        )

    def reminder_time_passed(
        self,
        event_name: str,
        elapsed_time_in_seconds: int,
    ) -> bool:
        if event_name not in self.timers:
            self.timers[event_name] = time.time()
            return True

        out = time.time() - self.timers[event_name] >= elapsed_time_in_seconds
        if out:
            self.timers[event_name] = time.time()
        return out

    async def update(self, config: AppConfig):
        if self.battery.state != self.current_state:
            new_state = self.battery.state
            if new_state == "Charging":
                if config["PROC_SETTINGS"]["alert_when_charger_plugged"]:
                    await self.send_charging_message()
            else:
                if config["PROC_SETTINGS"]["alert_when_charger_removed"]:
                    await self.send_discharging_message()

            self.current_state = new_state

        if self.current_state == "Charging":
            charge_amount = self.battery.percent.value
            pause_time = config["PROC_SETTINGS"]["remind_high_charge_time"] * 60

            if charge_amount >= 99 and self.reminder_time_passed(
                "overflow", 2 * 60
            ):  # 2 min
                await self.send_overflow_warning()
            elif charge_amount >= config["PROC_SETTINGS"][
                "high_charge_percent"
            ] and self.reminder_time_passed("high", pause_time):
                await self.send_removal_warning()

        if self.current_state == "Discharging":
            charge_amount = self.battery.percent.value
            pause_time = config["PROC_SETTINGS"]["remind_low_charge_time"] * 60

            if charge_amount <= config["PROC_SETTINGS"][
                "low_charge_percent"
            ] and self.reminder_time_passed("min", pause_time):
                await self.send_charge_reminder()


async def main():
    app = App()
    await app.send_welcome_message()

    while True:
        await app.update(DEFAULT_CONFIG_DATA)
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
