import time
import sys
import threading
import asyncio
from pathlib import Path
from tkinter import Tk, Toplevel
from pystray import Icon, Menu, MenuItem
from PIL import Image
import os

# from .gui import SettingsApp
# from .background_service import run_background_process, stop_background_process_flag
# from .config import load_config, save_config, get_app_name
# from .startup_manager import add_to_startup, remove_from_startup

from .src.background_proc import main

# class App:
#     def __init__(self):
#         self.app_name = get_app_name()
#         self.config = load_config()
#         self.background_thread = None
#         self.gui_window = None
#         self.tray_icon = None
#
#         # Determine if the app should run background process immediately
#         # if self.config.getboolean("Settings", "run_on_startup", fallback=False):
#         #     self.start_background_process()
#
#         self.setup_tray_icon()
#
#     # def start_background_process(self):
#     #     if self.background_thread is None or not self.background_thread.is_alive():
#     #         print("Starting background process...")
#     #         stop_background_process_flag.clear()  # Ensure flag is clear
#     #         self.background_thread = threading.Thread(
#     #             target=run_background_process, daemon=True
#     #         )
#     #         self.background_thread.start()
#     #         print("Background process started.")
#     #     else:
#     #         print("Background process is already running.")
#
#     # def stop_background_process(self):
#     #     if self.background_thread and self.background_thread.is_alive():
#     #         print("Stopping background process...")
#     #         stop_background_process_flag.set()  # Signal to stop
#     #         self.background_thread.join(
#     #             timeout=5
#     #         )  # Wait for thread to finish (with timeout)
#     #         if self.background_thread.is_alive():
#     #             print("Warning: Background thread did not terminate gracefully.")
#     #         self.background_thread = None
#     #         print("Background process stopped.")
#     #     else:
#     #         print("Background process is not running.")
#
#     # def open_settings(self):
#     #     if self.gui_window is None or not self.gui_window.winfo_exists():
#     #         print("Opening settings GUI...")
#     #         self.gui_window = Tk()
#     #         self.gui_window.withdraw()  # Hide the main Tkinter window
#     #         settings_app = SettingsApp(self.gui_window, self)
#     #         self.gui_window.mainloop()  # Start Tkinter event loop for the settings window
#     #     else:
#     #         print("Settings GUI is already open.")
#     #         self.gui_window.deiconify()  # Bring to front if minimized/hidden
#
#     # def on_quit_callback(self, icon):
#     #     print("Quitting application...")
#     #     self.stop_background_process()
#     #     icon.stop()
#     #     if self.gui_window and self.gui_window.winfo_exists():
#     #         self.gui_window.quit()  # Stop Tkinter event loop for the GUI
#
#     def setup_tray_icon(self):
#         # Load icon (make sure 'assets/icon.ico' exists)
#
#         icon_path = Path("./emojis/icon.ico").absolute()
#         image = Image.open(icon_path)
#
#         # Create menu items
#         menu = Menu(
#             MenuItem(
#                 "Open Settings", lambda: print("open settings")
#             ),  # self.open_settings),
#             MenuItem(
#                 "Start Background", lambda: print("start background proc"), default=True
#             ),  # self.start_background_process),
#             MenuItem(
#                 "Stop Background", lambda: print("stop backgroun proc")
#             ),  # self.stop_background_process),
#             MenuItem("Quit", lambda: print("quit")),  # self.on_quit_callback),
#         )
#
#         onclicked = lambda: print("clicked")
#
#         self.tray_icon = Icon(self.app_name, image, self.app_name, menu)
#         # Run in a separate thread to not block the main process
#         threading.Thread(target=self.tray_icon.run, daemon=True).start()
#         print("System tray icon set up.")
#
#     # def update_startup_setting(self, run_on_startup):
#     #     if run_on_startup:
#     #         add_to_startup(self.app_name)
#     #     else:
#     #         remove_from_startup(self.app_name)
#     #
#     #     self.config.set("Settings", "run_on_startup", str(run_on_startup))
#     #     save_config(self.config)
#     #     print(f"Startup setting updated: {run_on_startup}")
#
#
# def main():
#     app_instance = App()
#     # If the app was launched by clicking the EXE (not on startup)
#     # and "run_on_startup" is false, we should only show the GUI.
#     # The background process is *only* started if 'run_on_startup' is true
#     # or if the user explicitly clicks "Start Background" or launches the GUI
#     # and the GUI then starts the background process.
#
#     # Here, we ensure the GUI is shown when the user explicitly launches the app.
#     # The tray icon is always present, so the user can control from there.
#     # If `run_on_startup` is False, the background process is NOT started automatically
#     # when the user clicks the EXE, only the GUI will show.
#     # The user can then enable `run_on_startup` from the GUI.
#     # if not app_instance.config.getboolean("Settings", "run_on_startup", fallback=False):
#     #     app_instance.open_settings()
#
#     while True:
#         time.sleep(0.5)
#
#
# if __name__ == "__main__":
#     main()
