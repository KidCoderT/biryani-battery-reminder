# __main__.py : Main application entry point
# Copyright (C) 2025 Tejas

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
import asyncio
import threading
import multiprocessing
import ttkbootstrap as ttk
from tkinter import messagebox
from pystray import Icon, Menu, MenuItem

from battery_reminder.src import AppSettingUI
from battery_reminder.src import load_config, get_app_name, is_first_run
from battery_reminder.src import app_icon
from battery_reminder.src import (
    run_background_process,
)
from battery_reminder.src import (
    add_to_startup,
    remove_from_startup,
    is_in_startup,
)
from battery_reminder.src import Notifier
from battery_reminder.src import logger
from ctypes import c_bool

from battery_reminder.src import BackgroundProcessManager


def is_frozen():
    """Check if the application is running as a frozen executable (cx_Freeze)."""
    return getattr(sys, "frozen", False)  # True if frozen, False otherwise[1][6]


def is_already_running():
    """Check if another instance of this executable is running."""
    import psutil  # Requires 'psutil' package

    current_pid = os.getpid()
    exe_name = os.path.basename(sys.executable if is_frozen() else sys.argv[0])
    count = 0
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] == exe_name and proc.info["pid"] != current_pid:
                count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return count > 0


class App:
    def __init__(self):
        logger.info("Initializing application...")
        self.app_name = get_app_name()
        self.config = load_config()

        self.notification_queue = multiprocessing.Queue()
        self.critical_notifications_queue = multiprocessing.Queue()
        self.notifier = Notifier(
            self.notification_queue, self.critical_notifications_queue
        )

        self.stop_bg_process_flag = multiprocessing.Value(c_bool, False)
        self.settings_updated_flag = multiprocessing.Value(c_bool, False)

        self.background_process = None

        self.settings_app_instance = None
        self.gui_window = None
        self.gui_window: ttk.Window | None = None
        self.tray_icon = None

        # Initialize the main window but keep it hidden
        self.gui_window = ttk.Window()
        self.gui_window.withdraw()

        self.settings_app_instance = AppSettingUI(
            self.gui_window,
            self.stop_background_process,
            self.start_background_process,
            self.on_quit_callback,
            self.check_bg_running,
            self.on_settings_update_callback,
        )

        if self.config["PROC_SETTINGS"]["run_on_startup"]:
            logger.info("Application configured to run on startup")
            self.start_background_process()

        self.setup_tray_icon()
        logger.info("Application initialization complete")

    def check_bg_running(self):
        if self.stop_bg_process_flag.value:
            logger.info("Background process is not running")
            return False

        return self.background_process is not None

    def start_background_process(self):
        if self.background_process is None or not self.background_process.is_alive():
            logger.info("Starting background process...")

            self.stop_bg_process_flag.value = False
            self.notifier.clear_notifications.set()
            self.background_process = run_background_process(
                self.notification_queue,
                self.critical_notifications_queue,
                self.stop_bg_process_flag,
                self.settings_updated_flag,
            )

            if self.tray_icon:
                self.tray_icon.icon = app_icon(True)
                self.tray_icon.menu = self.create_menu()
                logger.info("Background process started successfully")

            if self.settings_app_instance:
                self.settings_app_instance.update_battery_health_widgets()
                self.settings_app_instance._update_app_status()

        else:
            logger.warning(
                "Attempted to start background process while it was already running"
            )

    def stop_background_process(self):
        if self.background_process and self.background_process.is_alive():
            logger.info("Stopping background process...")

            self.stop_bg_process_flag.value = True
            self.background_process.join(timeout=20)

            if self.background_process.is_alive():
                logger.error("Background thread did not terminate gracefully")

            self.background_process = None
            self.notifier.send_process_stopped_message()

            if self.tray_icon:
                self.tray_icon.icon = app_icon(False)
                self.tray_icon.menu = self.create_menu()

            logger.info("Background process stopped")
            logger.debug("Stop message sent successfully")

            if self.settings_app_instance:
                self.settings_app_instance.update_battery_health_widgets()
                self.settings_app_instance._update_app_status()
        else:
            logger.info("Background process was not running")

    def open_settings(self):
        assert self.gui_window is not None

        if not self.gui_window.winfo_exists():
            logger.info("Recreating settings GUI window")
            self.gui_window = ttk.Window()
            self.gui_window.withdraw()
            self.settings_app_instance = AppSettingUI(self.gui_window)

        self.gui_window.deiconify()
        self.gui_window.lift()
        self.gui_window.attributes("-topmost", True)
        self.gui_window.attributes("-topmost", False)

        assert self.settings_app_instance is not None

        self.settings_app_instance.update_battery_health_widgets()
        self.settings_app_instance._update_app_status()

        logger.info("Settings GUI shown")

    def on_quit_callback(self):
        logger.info("Quitting application initiated...")

        # clear messages BEFORE stopping background process
        self.stop_background_process()

        if self.tray_icon:
            logger.info("Stopping system tray icon...")
            self.tray_icon.stop()

        if self.gui_window and self.gui_window.winfo_exists():
            logger.info("Destroying settings GUI...")
            self.gui_window.destroy()
            self.gui_window = None
            self.settings_app_instance = None

        self.critical_notifications_queue.close()
        self.notification_queue.close()

        logger.info("Exiting Python process...")
        sys.exit(0)

    def on_click_menu_item(self):
        logger.info("Clicked on menu item")
        if not self.check_bg_running():
            self.start_background_process()

        self.open_settings()

    def create_menu(self):
        menu = Menu(
            MenuItem(
                "On Click Menu",
                self.on_click_menu_item,
                default=True,
                visible=False,
            ),
            MenuItem("Open Settings", self.open_settings),
            MenuItem(
                "Start Background",
                self.start_background_process,
                enabled=not self.check_bg_running(),
            ),
            MenuItem(
                "Stop Background",
                self.stop_background_process,
                enabled=self.check_bg_running(),
            ),
            MenuItem("Quit", self.on_quit_callback),
        )
        return menu

    def setup_tray_icon(self):
        logger.info("Setting up system tray icon...")
        icon_image = app_icon(self.check_bg_running())

        menu = self.create_menu()

        self.tray_icon = Icon(self.app_name, icon_image, self.app_name, menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        logger.info("System tray icon setup complete")

    def on_settings_update_callback(self):
        # if run_on_startup:
        #     add_to_startup()
        # else:
        #     remove_from_startup()

        if self.background_process and self.background_process.is_alive():
            self.settings_updated_flag.value = True
        else:
            BackgroundProcessManager.send_updated_settings_message(
                self.critical_notifications_queue
            )
        # logger.info(f"Startup setting updated: {}")


async def main():
    try:
        # if is_already_running():
        #     logger.warning("Another instance is already running")
        #     messagebox.showwarning(
        #         "Application Already Running",
        #         f"{get_app_name()} is already running. Check in your System tray and use the existing instance.",
        #     )
        #     sys.exit(0)

        logger.info("Starting application...")
        app_instance = App()

        # if app_instance.config["PROC_SETTINGS"]["run_on_startup"]:
        #     if not is_in_startup():
        #         add_to_startup()
        #         logger.info("Startup setting updated: True")
        #
        # if not app_instance.config["PROC_SETTINGS"]["run_on_startup"]:
        #     logger.info("Opening settings on manual launch")
        #     app_instance.open_settings()
        #
        # if is_first_run():
        #     logger.info("Opening settings for first installation")
        #     app_instance.open_settings()
        app_instance.open_settings()

        def run_notifier_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(app_instance.notifier.main())
            loop.close()

        notifier_thread = threading.Thread(target=run_notifier_in_thread, daemon=True)
        notifier_thread.start()

        logger.info("Starting main application loop")
        app_instance.gui_window.mainloop()

    except Exception as e:
        logger.exception("Fatal error in main application loop")
        raise


if __name__ == "__main__":
    asyncio.run(main())
