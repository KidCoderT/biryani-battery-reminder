import os
import sys
import asyncio
import threading
import ttkbootstrap as ttk
from tkinter import messagebox
from pystray import Icon, Menu, MenuItem

from battery_reminder.src.settings_gui import AppSettingUI
from battery_reminder.src.config import load_config, get_app_name
from battery_reminder.src.assets_manager import app_icon
from battery_reminder.src.background_proc import (
    clear_all_messages,
    run_background_process,
    stop_background_process_flag,
)
from battery_reminder.src.startup_manager import (
    add_to_startup,
    remove_from_startup,
    is_in_startup,
)
from battery_reminder.src.logger_config import setup_logger

# Initialize logger
logger = setup_logger()


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
        self.background_thread = None

        self.settings_app_instance = None
        self.gui_window = None
        self.tray_icon = None

        # Initialize the main window but keep it hidden
        self.gui_window = ttk.Window()
        self.gui_window.withdraw()
        self.check_bg_running = (
            lambda: not stop_background_process_flag.is_set()
            and self.background_thread is not None
        )
        self.settings_app_instance = AppSettingUI(
            self.gui_window,
            self.stop_background_process,
            self.start_background_process,
            self.on_quit_callback,
            self.check_bg_running,
            self.update_startup_setting,
        )

        self.setup_tray_icon()
        logger.info("Application initialization complete")

        if self.config["PROC_SETTINGS"]["run_on_startup"]:
            logger.info("Application configured to run on startup")
            self.start_background_process()

    def start_background_process(self):
        if self.background_thread is None or not self.background_thread.is_alive():
            logger.info("Starting background process...")
            stop_background_process_flag.clear()
            self.background_thread = threading.Thread(
                target=run_background_process, daemon=True
            )
            self.background_thread.start()
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
        if self.background_thread and self.background_thread.is_alive():
            logger.info("Stopping background process...")
            stop_background_process_flag.set()
            self.background_thread.join(timeout=20)
            if self.background_thread.is_alive():
                logger.error("Background thread did not terminate gracefully")
            self.background_thread = None
            self.tray_icon.icon = app_icon(False)
            self.tray_icon.menu = self.create_menu()
            logger.info("Background process stopped")

            if self.settings_app_instance:
                self.settings_app_instance.update_battery_health_widgets()
                self.settings_app_instance._update_app_status()
        else:
            logger.info("Background process was not running")

    def open_settings(self):
        if not self.gui_window.winfo_exists():
            logger.info("Recreating settings GUI window")
            self.gui_window = ttk.Window()
            self.gui_window.withdraw()
            self.settings_app_instance = AppSettingUI(self.gui_window)

        self.gui_window.deiconify()
        self.gui_window.lift()
        self.gui_window.attributes("-topmost", True)
        self.gui_window.attributes("-topmost", False)

        self.settings_app_instance.update_battery_health_widgets()
        self.settings_app_instance._update_app_status()

        logger.info("Settings GUI shown")

    def on_quit_callback(self, icon):
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

    def update_startup_setting(self, run_on_startup):
        if run_on_startup:
            add_to_startup()
        else:
            remove_from_startup()

        logger.info(f"Startup setting updated: {run_on_startup}")


def main():
    try:
        if is_already_running():
            logger.warning("Another instance is already running")
            messagebox.showwarning(
                "Application Already Running",
                f"{get_app_name()} is already running. Check in your System tray and use the existing instance.",
            )
            sys.exit(0)

        logger.info("Starting application...")
        app_instance = App()

        if app_instance.config["PROC_SETTINGS"]["run_on_startup"]:
            if not is_in_startup():
                add_to_startup()
                logger.info("Startup setting updated: True")

        if not app_instance.config["PROC_SETTINGS"]["run_on_startup"]:
            logger.info("Opening settings on manual launch")
            app_instance.open_settings()

        # Run the Tkinter mainloop in the main thread
        logger.info("Starting main application loop")
        app_instance.gui_window.mainloop()
    except Exception as e:
        logger.exception("Fatal error in main application loop")
        raise


if __name__ == "__main__":
    main()

"""
Application Overview and Process Flow:

1. Application Structure:
   - The app is a system tray application with a GUI settings window
   - Uses Tkinter for GUI and pystray for system tray functionality
   - Implements a background process for battery monitoring

2. Main Components:
   - App class: Core application logic and state management
   - System tray icon: Persistent interface for user control
   - Settings GUI: Configuration interface
   - Background process: Battery monitoring thread

3. Startup Process:
   - Application initializes with configuration from config file
   - Creates system tray icon
   - If 'run_on_startup' is enabled, starts background process
   - If launched manually (not on startup), opens settings GUI

4. Key Features:
   - System tray integration with menu options
   - Settings GUI for configuration
   - Background process control (start/stop)
   - Startup management
   - Clean shutdown process

5. Threading Model:
   - Main thread: Handles GUI and application flow
   - Background thread: Runs battery monitoring process
   - Tray icon thread: Manages system tray interface

6. Shutdown Process:
   - Stops background process
   - Removes system tray icon
   - Destroys GUI windows
   - Performs clean exit

7. Configuration:
   - Loads settings from config file
   - Manages startup behavior
   - Controls background process state
"""
