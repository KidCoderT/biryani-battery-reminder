import time
import asyncio
from pathlib import Path
from typing import Literal
import batteryinfo
from desktop_notifier import DesktopNotifier, Icon
from importlib.resources import as_file, files

APP_NAME = "battery-reminder"
# battery_state = Literal["Charging", "Discharging"]


class App:
    def __init__(self, app_name=APP_NAME) -> None:
        self.battery = batteryinfo.Battery()
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
            icon=Icon(Path("./emojis/plain.png").absolute()),
        )

    async def send_charging_message(self):
        await self.notifier.send(
            title="Started Charging!",
            message=f"It will take another {self.time_to_full or ''} to fully charge! Currently its {self.percentage:.1f}% full",
            icon=Icon(Path("./emojis/happy.png").absolute()),
        )

    async def send_discharging_message(self):
        await self.notifier.send(
            title="Stopped Charging!",
            message=f"You have {self.time_to_empty or ''} of Charge Left! Currently there is {self.percentage:.1f}% charge left",
            icon=Icon(Path("./emojis/happy.png").absolute()),
        )

    async def send_removal_warning(self):
        await self.notifier.send(
            title=f"Its {self.percentage:.1f}% Full",
            message=f"You should remove the charger now! There is {self.time_to_full or ''} of time left until full charge! Better to not spoil your battery!",
            icon=Icon(Path("./emojis/perfect.png").absolute()),
        )

    async def send_overflow_warning(self):
        await self.notifier.send(
            title="Please Stop Charging!",
            message=f"Its 100% charge pretty much. To not ruin your computer battery turn of the charger!",
            icon=Icon(Path("./emojis/too-much.png").absolute()),
        )

    async def send_charge_reminder(self):
        await self.notifier.send(
            title="Battery too low!",
            message=f"You have only {self.percentage:.1f}% battery left which will last for {self.time_to_empty}. Charge quickly!",
            icon=Icon(Path("./emojis/oh-no.png").absolute()),
        )

    def reminder_time_passed(
        self,
        event_name: str,
        elapsed_time_in_seconds: int,
    ) -> bool:
        if event_name not in self.timers:
            self.timers[event_name] = time.time()
            return False

        out = time.time() - self.timers[event_name] >= elapsed_time_in_seconds
        self.timers[event_name] = time.time()
        return out

    async def update(self):
        if self.battery.state != self.current_state:
            new_state = self.battery.state
            if new_state == "Charging":
                await self.send_charging_message()
            else:
                await self.send_discharging_message()

            self.current_state = new_state

        if self.current_state == "Charging":
            charge_amount = self.battery.percent.value
            if charge_amount >= 95:
                await self.send_removal_warning()
            elif charge_amount >= 99 and self.reminder_time_passed(
                ">99", 2 * 60
            ):  # 2 min
                await self.send_overflow_warning()

        if self.current_state == "Discharging":
            charge_amount = self.battery.percent.value
            if charge_amount <= 10 and self.reminder_time_passed("<10", 2 * 60):
                await self.send_charge_reminder()


async def main():
    app = App()

    await app.send_welcome_message()

    while True:
        await app.update()
        await asyncio.sleep(1)


asyncio.run(main())
