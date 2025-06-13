import sys
import os
import platform
import ctypes
import shutil
from pathlib import Path
from battery_reminder.src.logger_config import setup_logger

# Initialize logger
logger = setup_logger()


startup_folder = os.path.join(
    os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup"
)


def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """Relaunch the script with admin rights."""
    if getattr(sys, "frozen", False):
        # PyInstaller .exe
        exe = sys.executable
    else:
        exe = sys.argv[0]
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)


def get_exe_path():
    # Get the path to the current executable (works for PyInstaller --onefile or --onedir)
    if getattr(sys, "frozen", False):
        return sys.executable
    else:
        return os.path.abspath(sys.argv[0])


def get_shortcut_path(shortcut_name=None):
    # Name of the shortcut (default: exe name)
    if shortcut_name is None:
        shortcut_name = os.path.splitext(os.path.basename(get_exe_path()))[0]
    return os.path.join(startup_folder, f"{shortcut_name}.lnk")


def create_shortcut(shortcut_path, target_path, icon_path=None):
    import pythoncom
    from win32com.shell import shell
    from win32com.shell import shellcon
    from win32com.client import Dispatch

    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target_path
    shortcut.WorkingDirectory = os.path.dirname(target_path)
    if icon_path:
        shortcut.IconLocation = icon_path
    shortcut.save()


def add_to_startup(shortcut_name=None, icon_path=None):
    """Add the application to system startup."""
    if not is_admin():
        print("Requesting admin privileges to add to startup...")
        run_as_admin()
        sys.exit(0)
    shortcut_path = get_shortcut_path(shortcut_name)
    exe_path = get_exe_path()
    create_shortcut(shortcut_path, exe_path, icon_path)
    logger.info("Added to startup.")

    return True


def is_in_startup(shortcut_name=None):
    shortcut_path = get_shortcut_path(shortcut_name)
    return os.path.exists(shortcut_path)


def remove_from_startup(shortcut_name=None):
    if not is_admin():
        print("Requesting admin privileges to remove from startup...")
        run_as_admin()
        sys.exit(0)
    shortcut_path = get_shortcut_path(shortcut_name)
    if os.path.exists(shortcut_path):
        os.remove(shortcut_path)
        logger.info("Removed from startup.")

    return True
