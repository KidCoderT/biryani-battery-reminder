import time
import sys
import threading
import asyncio
from pathlib import Path
import ttkbootstrap as ttk
from tkinter import Toplevel, messagebox
from pystray import Icon, Menu, MenuItem
import os
import platform
import socket
import tempfile

from .src.settings_gui import AppSettingUI
from .src.config import load_config, get_app_name
from .src.assets_manager import app_icon
from .src.background_proc import run_background_process, stop_background_process_flag
from .src.startup_manager import add_to_startup, remove_from_startup
from .src.logger_config import setup_logger

# Initialize logger
logger = setup_logger()


def is_already_running():
    """Check if another instance of the application is already running."""
    app_name = get_app_name()

    if platform.system() == "Windows":
        try:
            import win32event
            import win32api
            import winerror
            import win32security

            mutex_name = f"Global\\{app_name}"
            try:
                mutex = win32event.CreateMutex(None, False, mutex_name)
                if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                    return True
                return False
            except Exception as e:
                logger.error(f"Error checking for existing instance on Windows: {e}")
                return False

        except ImportError:
            logger.warning("pywin32 not available, falling back to socket-based check")
            return check_via_socket(app_name)
    else:
        # For Linux and other Unix-like systems
        return check_via_socket(app_name)


def check_via_socket(app_name):
    """Check for existing instance using a socket lock file."""
    lock_file = os.path.join(tempfile.gettempdir(), f"{app_name}.lock")

    try:
        # Try to create and bind to a socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.bind(lock_file)
        return False
    except socket.error:
        # Socket already exists, meaning another instance is running
        return True
    except Exception as e:
        logger.error(f"Error checking for existing instance via socket: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass


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
        else:
            logger.warning(
                "Attempted to start background process while it was already running"
            )

    def stop_background_process(self):
        if self.background_thread and self.background_thread.is_alive():
            logger.info("Stopping background process...")
            stop_background_process_flag.set()
            self.background_thread.join(timeout=10)
            if self.background_thread.is_alive():
                logger.error("Background thread did not terminate gracefully")
            self.background_thread = None
            self.tray_icon.icon = app_icon(False)
            self.tray_icon.menu = self.create_menu()
            logger.info("Background process stopped")
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
        logger.info("Settings GUI shown")

    def on_quit_callback(self, icon):
        logger.info("Quitting application initiated...")

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

    def create_menu(self):
        menu = Menu(
            MenuItem("Open Settings", self.open_settings),
            MenuItem(
                "Start Background",
                self.start_background_process,
                default=True,
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
            add_to_startup(self.app_name)
        else:
            remove_from_startup(self.app_name)

        logger.info(f"Startup setting updated: {run_on_startup}")


def main():
    try:
        if is_already_running():
            logger.warning("Another instance is already running")
            messagebox.showwarning(
                "Application Already Running",
                f"{get_app_name()} is already running. Please use the existing instance. Check in your System tray",
            )
            sys.exit(0)

        logger.info("Starting application...")
        app_instance = App()

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
