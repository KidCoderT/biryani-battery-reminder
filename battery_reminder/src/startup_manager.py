import sys
import os
import platform
import shutil
from pathlib import Path
from .logger_config import setup_logger

# Initialize logger
logger = setup_logger()


def get_app_path():
    """Get the path to the application executable or script."""
    if getattr(sys, "frozen", False):
        # If running as a PyInstaller bundle
        return sys.executable
    else:
        # If running as a script, get the main.py path and use python interpreter
        return f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'


def add_to_startup(app_name):
    """Add the application to system startup."""
    try:
        if platform.system() == "Windows":
            _add_to_windows_startup(app_name)
        elif platform.system() == "Linux":
            _add_to_linux_startup(app_name)
        elif platform.system() == "Darwin":  # macOS
            _add_to_macos_startup(app_name)
        else:
            logger.warning(
                f"Startup management not implemented for {platform.system()}"
            )
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to add to startup: {e}")
        return False


def remove_from_startup(app_name):
    """Remove the application from system startup."""
    try:
        if platform.system() == "Windows":
            _remove_from_windows_startup(app_name)
        elif platform.system() == "Linux":
            _remove_from_linux_startup(app_name)
        elif platform.system() == "Darwin":  # macOS
            _remove_from_macos_startup(app_name)
        else:
            logger.warning(
                f"Startup management not implemented for {platform.system()}"
            )
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to remove from startup: {e}")
        return False


def _add_to_windows_startup(app_name):
    """Add application to Windows startup registry."""
    try:
        import winreg

        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_path = get_app_path()

        with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
            winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, app_path)
        logger.info(f"Added '{app_name}' to Windows startup")
    except Exception as e:
        logger.error(f"Error adding to Windows startup: {e}")
        raise


def _remove_from_windows_startup(app_name):
    """Remove application from Windows startup registry."""
    try:
        import winreg

        key = winreg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

        with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
            try:
                winreg.DeleteValue(reg_key, app_name)
                logger.info(f"Removed '{app_name}' from Windows startup")
            except FileNotFoundError:
                logger.info(f"'{app_name}' not found in Windows startup")
    except Exception as e:
        logger.error(f"Error removing from Windows startup: {e}")
        raise


def _add_to_linux_startup(app_name):
    """Add application to Linux startup."""
    try:
        app_path = get_app_path()

        # Try different autostart directories based on desktop environment
        autostart_dirs = [
            os.path.expanduser("~/.config/autostart"),  # GNOME, KDE, XFCE
            os.path.expanduser("~/.local/share/applications"),  # Some distributions
        ]

        desktop_entry = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec={app_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Terminal=false
"""

        # Try each autostart directory
        for autostart_dir in autostart_dirs:
            try:
                os.makedirs(autostart_dir, exist_ok=True)
                desktop_file = os.path.join(autostart_dir, f"{app_name}.desktop")
                with open(desktop_file, "w") as f:
                    f.write(desktop_entry)
                os.chmod(desktop_file, 0o755)
                logger.info(f"Added '{app_name}' to Linux startup in {autostart_dir}")
                return
            except Exception as e:
                logger.warning(f"Failed to add to {autostart_dir}: {e}")
                continue

        raise Exception("Failed to add to any autostart directory")
    except Exception as e:
        logger.error(f"Error adding to Linux startup: {e}")
        raise


def _remove_from_linux_startup(app_name):
    """Remove application from Linux startup."""
    try:
        # Check all possible autostart directories
        autostart_dirs = [
            os.path.expanduser("~/.config/autostart"),
            os.path.expanduser("~/.local/share/applications"),
        ]

        removed = False
        for autostart_dir in autostart_dirs:
            desktop_file = os.path.join(autostart_dir, f"{app_name}.desktop")
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
                logger.info(f"Removed '{app_name}' from {autostart_dir}")
                removed = True

        if not removed:
            logger.info(f"'{app_name}' not found in any Linux startup location")
    except Exception as e:
        logger.error(f"Error removing from Linux startup: {e}")
        raise


def _add_to_macos_startup(app_name):
    """Add application to macOS startup."""
    try:
        app_path = get_app_path()
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{app_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
        plist_dir = os.path.expanduser("~/Library/LaunchAgents")
        os.makedirs(plist_dir, exist_ok=True)
        plist_file = os.path.join(plist_dir, f"{app_name}.plist")

        with open(plist_file, "w") as f:
            f.write(plist_content)
        logger.info(f"Added '{app_name}' to macOS startup")
    except Exception as e:
        logger.error(f"Error adding to macOS startup: {e}")
        raise


def _remove_from_macos_startup(app_name):
    """Remove application from macOS startup."""
    try:
        plist_file = os.path.expanduser(f"~/Library/LaunchAgents/{app_name}.plist")
        if os.path.exists(plist_file):
            os.remove(plist_file)
            logger.info(f"Removed '{app_name}' from macOS startup")
        else:
            logger.info(f"'{app_name}' not found in macOS startup")
    except Exception as e:
        logger.error(f"Error removing from macOS startup: {e}")
        raise
