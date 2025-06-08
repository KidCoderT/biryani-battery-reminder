import sys
import os
import platform
import shutil


def add_to_startup(app_name):
    if platform.system() == "Windows":
        try:
            import winreg

            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            # Get the path to the executable
            if getattr(sys, "frozen", False):
                # If running as a PyInstaller bundle
                app_path = sys.executable
            else:
                # If running as a script, get the main.py path and use python interpreter
                app_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, app_name, 0, winreg.REG_SZ, app_path)
            print(f"Added '{app_name}' to Windows startup.")
        except Exception as e:
            print(f"Error adding to Windows startup: {e}")
    elif platform.system() == "Linux":
        try:
            # Get the path to the executable
            if getattr(sys, "frozen", False):
                # If running as a PyInstaller bundle
                app_path = sys.executable
            else:
                # If running as a script, get the main.py path and use python interpreter
                app_path = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'

            # Create desktop entry content
            desktop_entry = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec={app_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            # Get the autostart directory
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)

            # Write the desktop entry file
            desktop_file = os.path.join(autostart_dir, f"{app_name}.desktop")
            with open(desktop_file, "w") as f:
                f.write(desktop_entry)

            # Make the file executable
            os.chmod(desktop_file, 0o755)
            print(f"Added '{app_name}' to Linux startup.")
        except Exception as e:
            print(f"Error adding to Linux startup: {e}")
    else:
        print("Startup management for this OS is not implemented.")


def remove_from_startup(app_name):
    if platform.system() == "Windows":
        try:
            import winreg

            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.DeleteValue(reg_key, app_name)
            print(f"Removed '{app_name}' from Windows startup.")
        except FileNotFoundError:
            print(
                f"'{app_name}' not found in Windows startup (already removed or never added)."
            )
        except Exception as e:
            print(f"Error removing from Windows startup: {e}")
    elif platform.system() == "Linux":
        try:
            # Get the autostart directory
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_file = os.path.join(autostart_dir, f"{app_name}.desktop")

            # Remove the desktop entry file if it exists
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
                print(f"Removed '{app_name}' from Linux startup.")
            else:
                print(
                    f"'{app_name}' not found in Linux startup (already removed or never added)."
                )
        except Exception as e:
            print(f"Error removing from Linux startup: {e}")
    else:
        print("Startup management for this OS is not implemented.")
