import sys
import os
from cx_Freeze import setup, Executable
import battery_reminder.src.startup_manager as startup_manager

# Detect virtual env path (for example on Windows, sys.prefix points to venv folder)
venv_path = sys.prefix

resource_src = os.path.join(
    venv_path, "Lib", "site-packages", "desktop_notifier", "resources"
)

if not os.path.exists(resource_src):
    print(f"Warning: Resource directory {resource_src} does not exist.")

setup(
    name="birayni-battery-reminder",
    version="2.0.0",
    description="Birayni - The Battery Reminder App. Reminds when the battery charge is 100% or too low with a fun notification and UI",
    author="Tejas",
    executables=[
        Executable(
            script="battery_reminder/__main__.py",
            target_name="biryani-battery-reminder.exe",  # you can add .exe explicitly if you want
            base="win32gui",
            icon="assets/icon.ico",
            shortcut_name=startup_manager.SHORTCUT_NAME,
            shortcut_dir="ProgramMenuFolder",
        )
    ],
    options={
        "build_exe": {
            "include_files": [("assets", "assets")],
            "includes": [
                "win32com",
                "win32com.client",
                "desktop_notifier",
                "desktop_notifier.resources",
                "pythoncom",
                "loguru",
                "tkinter",
                "ttkbootstrap",
                "ttkbootstrap.utility",
                "pystray",
                "psutil",
                "nava",
            ],
            "zip_include_packages": ["desktop_notifier"],
            "zip_includes": [
                (resource_src, "desktop_notifier/resources"),
            ],
            "optimize": 2,
        }
    },
)
