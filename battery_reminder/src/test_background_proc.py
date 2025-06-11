import asyncio
from typing import Literal
from batteryinfo import Battery, TimeFormat

from concurrent.futures import ThreadPoolExecutor

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
)

from rich import print
from .background_proc import BackgroundProcessManager


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


progress = Progress(
    TextColumn("[bold blue] Charge %", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
)


async def test_proc(app: BackgroundProcessManager):
    await app.send_welcome_message()
    try:
        while True:
            await app.update()
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        print("\nBackground process cancelled")
        raise


def main():
    app = BackgroundProcessManager(_class=_Battery)
    loop = asyncio.get_running_loop()

    app.battery.set_test_state(
        "Charging" if input("Start State: ") == "c" else "Discharging"
    )

    # Create separate event loop for background thread
    executor = ThreadPoolExecutor()
    background_loop = asyncio.new_event_loop()
    background_future = loop.run_in_executor(executor, background_loop.run_forever)

    # Schedule proc in background loop
    proc_task = asyncio.run_coroutine_threadsafe(test_proc(app), background_loop)

    try:
        # Progress handling in main thread
        with progress:
            task = progress.add_task("Charging")
            progress.console.log("Requesting Charge...")
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
                    if not next_input.isdigit() and next_input != "":
                        continue
                    advance = int(next_input) if next_input else 1
                    progress.update(task, advance=advance)
                    i += advance
                    app.battery.set_test_percentage(i)
                except KeyboardInterrupt:
                    print("\nOperation cancelled by user")
                    break

            progress.console.log("Downloaded")

    finally:
        # Cleanup
        proc_task.cancel()
        background_loop.call_soon_threadsafe(background_loop.stop)
        executor.shutdown(wait=False)
