import time
import sys
import threading
import asyncio
from pathlib import Path
import ttkbootstrap as ttk
from tkinter import Toplevel
from pystray import Icon, Menu, MenuItem
import os


from .src.settings_gui import AppSettingUI
from .src.config import load_config, get_app_name
from .src.assets_manager import app_icon
from .src.background_proc import run_background_process, stop_background_process_flag
from .src.startup_manager import add_to_startup, remove_from_startup


class App:
    def __init__(self):
        self.app_name = get_app_name()
        self.config = load_config()
        self.background_thread = None

        self.settings_app_instance = None
        self.gui_window = None
        self.tray_icon = None

        # Initialize the main window but keep it hidden
        self.gui_window = ttk.Window()
        self.gui_window.withdraw()
        self.settings_app_instance = AppSettingUI(self.gui_window)

        if self.config["PROC_SETTINGS"]["run_on_startup"]:
            self.start_background_process()

        self.setup_tray_icon()

    def start_background_process(self):
        if self.background_thread is None or not self.background_thread.is_alive():
            print("Starting background process...")
            stop_background_process_flag.clear()
            self.background_thread = threading.Thread(
                target=run_background_process, daemon=True
            )
            self.background_thread.start()
            self.tray_icon.icon = app_icon(True)
            print("Background process started.")
        else:
            print("Background process is already running.")

    def stop_background_process(self):
        if self.background_thread and self.background_thread.is_alive():
            print("Stopping background process...")
            stop_background_process_flag.set()
            self.background_thread.join(timeout=10)
            if self.background_thread.is_alive():
                print("Warning: Background thread did not terminate gracefully.")
            self.background_thread = None
            self.tray_icon.icon = app_icon(False)
            print("Background process stopped.")
        else:
            print("Background process is not running.")

    def open_settings(self):
        if not self.gui_window.winfo_exists():
            self.gui_window = ttk.Window()
            self.gui_window.withdraw()
            self.settings_app_instance = AppSettingUI(self.gui_window)
            print("Settings GUI recreated and shown.")

        self.gui_window.deiconify()
        self.gui_window.lift()
        self.gui_window.attributes("-topmost", True)
        self.gui_window.attributes("-topmost", False)
        print("Settings GUI shown.")

    def on_quit_callback(self, icon):
        print("Quitting application initiated...")

        self.stop_background_process()

        if self.tray_icon:
            print("Stopping system tray icon...")
            self.tray_icon.stop()

        if self.gui_window and self.gui_window.winfo_exists():
            print("Destroying settings GUI...")
            self.gui_window.destroy()
            self.gui_window = None
            self.settings_app_instance = None

        print("Exiting Python process...")
        sys.exit(0)

    def setup_tray_icon(self):
        icon_image = app_icon(not stop_background_process_flag.is_set())

        menu = Menu(
            MenuItem("Open Settings", self.open_settings),
            MenuItem("Start Background", self.start_background_process, default=True),
            MenuItem("Stop Background", self.stop_background_process),
            MenuItem("Quit", self.on_quit_callback),
        )

        self.tray_icon = Icon(self.app_name, icon_image, self.app_name, menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        print("System tray icon set up.")


def main():
    app_instance = App()

    if not app_instance.config["PROC_SETTINGS"]["run_on_startup"]:
        app_instance.open_settings()

    # Run the Tkinter mainloop in the main thread
    app_instance.gui_window.mainloop()


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
