# Copyright (C) 2025 Tejas
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the LICENSE file for more details.

# WARNING: THIS ENTIRE CODE IS AI GENERATED SLOB
# I WAS TOO LAZY TO WRITE ALL OF THIS. I WROTE SOM PARTS BUT MOSTLY AI.
# IT WORKS BUT ITS ALSO CRAP.... SO UNLESS U REWRITING
# FROM SCRATCH DONT CHANGE IN MY RECOMMENDATION...

import tkinter as tk
from tkinter import filedialog
from typing import Any, Dict, Literal
from PIL import Image, ImageTk
import webbrowser
import os
from pathlib import Path

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledFrame
from ttkbootstrap.tooltip import ToolTip

from battery_reminder.src.background_proc import (
    BatteryDataManager,
)
from battery_reminder.src.app_config_manager import (
    AppConfig,
    get_default_config,
    load_config,
    save_config,
)
from battery_reminder.src.logger_config import logger
from battery_reminder.src.startup_manager import add_to_startup, remove_from_startup
from battery_reminder.src.assets_manager import get_tkinter_icon, get_default_sound
from battery_reminder.src import powerplan


class AppSettingUI:
    """Main application UI class for Battery Reminder."""

    # Theme Configuration
    LIGHT_THEME = "litera"
    DARK_THEME = "darkly"

    # UI Constants
    WINDOW_SIZE = "820x1025"
    METER_SIZE = 200
    METER_ARC_RANGE = 360

    # Tooltip Description
    TOOLTIP_DESCRIPTIONS: Dict[str, str] = {
        "vendor": "Battery manufacturer.",
        "model": "Battery model name or number.",
        "serial_number": "Unique battery ID for tracking and warranty.",
        "technology": "Battery type (e.g., Li-ion).",
        "percent": "Current charge level (%).",
        "state": "Battery status (e.g., Charging, Discharging).",
        "capacity": "Remaining battery capacity vs. original design (%).",
        "temperature": "Current battery temperature.",
        "cycle_count": "Number of full charge/discharge cycles. Indicates lifespan.",
        "energy": "Current stored energy (Wh).",
        "energy_full": "Current maximum energy the battery can hold (Wh).",
        "energy_full_design": "Original design capacity (Wh).",
        "energy_rate": "Current energy use or charging rate (W).",
        "voltage": "Current battery voltage (V).",
    }

    def __init__(
        self,
        main_window: ttk.Window,
        stop_proc=lambda: print("stop proc"),
        start_proc=lambda: print("start proc"),
        quit_app=lambda: print("quit app"),
        check_bg_proc_stat=lambda: True,
        on_update_callback=lambda: print("settings updated"),
        on_powerplan_restarted=lambda: print("WORKS AGAIN"),
        hide_gui_on_close=True,
    ) -> None:
        """Initialize the application UI.

        Args:
            main_window: The main ttkbootstrap window instance
        """
        logger.info("Initializing settings GUI...")
        self.master = main_window
        self.master.title("Biryani (Battery Reminder)")
        self.saved_data = load_config()

        self.check_bg_proc_stat = check_bg_proc_stat
        self.start_proc = start_proc
        self.stop_proc = stop_proc
        self.on_update_callback = on_update_callback
        self.quit_app = quit_app
        self.notify_powerplan_works_again = on_powerplan_restarted
        self.battery_data_manager = BatteryDataManager()

        self._setup_window()
        self._initialize_theme()
        self._create_main_layout()
        self._create_header()
        self._create_notebook()

        if hide_gui_on_close:
            self.master.protocol(
                "WM_DELETE_WINDOW", self.on_closing
            )  # Handle close button

        # Initialize button states
        self.reset_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self._update_button_states()

        self.toggle_theme()
        self._reload_data()
        self._retry_battery_settings()
        logger.info("Settings GUI initialized successfully")

    def on_closing(self):
        logger.info("Settings GUI closing...")
        # When the user closes the GUI, hide it instead of destroying it
        # so the system tray icon can still bring it back.
        # it also checks to see if the data has any changes

        current_data = self.get_current_settings()
        has_changes = self.has_settings_changed(current_data, ignore_theme=True)
        has_errors = self.error_count > 0

        if has_changes or has_errors:
            result = Messagebox.yesno(
                title="Confirm Close",
                message="Are you sure you want to close the settings without saving? Any changes will be lost.",
                parent=self.master,
            )

            if result == "Yes":
                self.master.withdraw()
                self.reset_default(False)
                logger.info("Settings GUI hidden")
            else:
                logger.info("Settings not closed")
        else:
            self.master.withdraw()
            logger.info("Settings GUI hidden")

    def _setup_window(self) -> None:
        """Configure the main window properties."""
        logger.debug("Setting up main window properties")
        self.master.geometry(self.WINDOW_SIZE)
        self.master.minsize(680, 680)
        # self.master.resizable(False, False)

        original_image = Image.open(get_tkinter_icon())
        resized_image = original_image.resize((48, 48), Image.Resampling.LANCZOS)
        tk_image = ImageTk.PhotoImage(resized_image)
        self.master.tk.call("wm", "iconphoto", self.master._w, tk_image)

    def _initialize_theme(self) -> None:
        """Initialize theme-related settings and styles."""
        logger.debug("Initializing theme settings")
        self.theme: Literal["light", "dark"] = (
            "light" if self.saved_data["GUI_SETTINGS"]["theme"] == "dark" else "dark"
        )

        # Configure custom button styles
        self.style = ttk.Style()
        self.style.configure(
            "CustomLight.TButton",
            background="#ffffff",
            foreground="#222222",
            justify=CENTER,
            anchor=CENTER,
        )
        self.style.configure(
            "CustomDark.TButton",
            background="#222222",
            foreground="#ffffff",
            justify=CENTER,
            anchor=CENTER,
        )

        # Configure error state styles with thicker borders
        # self.style.configure(
        #     "Error.TSpinbox", borderwidth=3, relief="solid", bordercolor="red"
        # )

        self.icons = {
            "dark": " ☀",
            "light": "🌕",
        }
        logger.debug(f"Initialized theme: {self.theme}")

    def _create_main_layout(self) -> None:
        """Create the main application layout."""
        self.main_frame = ttk.Frame(
            self.master,
            padding=(25, 25),
        )
        self.main_frame.pack(fill=BOTH, expand=YES)

    def _create_header(self) -> None:
        """Create the application header with title and control buttons."""
        header_frame = ttk.Frame(self.main_frame, padding=(10, 10))
        header_frame.pack(fill=X)

        # App Title
        app_title_label = ttk.Label(
            header_frame,
            text="🍛 Biryani (Battery Reminder)",
            font=("Arial", 16, "bold"),
        )
        app_title_label.pack(side=LEFT, padx=(0, 10), expand=True, fill=X)

        # Theme Toggle Button
        self.theme_button = ttk.Button(
            header_frame,
            text=self.icons[self.theme],
            style="CustomDark.TButton",
            command=self.toggle_theme,
            padding=(10, 10),
            width=3,
        )
        self.theme_button.pack(side=RIGHT, padx=(0, 5))

        # Reload Button
        self.reload_btn = ttk.Button(
            header_frame,
            text="🔄",
            style="light.TButton",
            command=self.update_battery_health_widgets,
            padding=(10, 10),
            width=3,
        )
        self.reload_btn.pack(side=RIGHT, padx=(0, 10))

        # Separator
        self.separator = ttk.Separator(self.main_frame, orient="horizontal")
        self.separator.pack(fill="x", pady=20)

    def _create_notebook(self) -> None:
        """Create the notebook widget with tabs."""
        self.style.configure("custom.TNotebook", tabposition="n")
        self.style.configure(
            "custom.TNotebook.Tab", padding=(0, 25), font=("Arial", 10)
        )

        self.notebook = ttk.Notebook(self.main_frame, style="custom.TNotebook")
        size = 20

        # App Settings Tab
        self.app_settings_tab = ttk.Frame(self.notebook)
        app_settings_scroll = ScrolledFrame(self.app_settings_tab, autohide=True)
        app_settings_scroll.pack(fill="both", expand=True)
        self.create_app_settings_widgets(app_settings_scroll)
        self.notebook.add(self.app_settings_tab, text="App Settings".center(size))

        # Battery Health Tab
        self.battery_health_tab = ttk.Frame(self.notebook)
        battery_health_scroll = ScrolledFrame(self.battery_health_tab, autohide=True)
        battery_health_scroll.pack(fill="both", expand=True)
        self.create_battery_health_widgets(battery_health_scroll)
        self.notebook.add(self.battery_health_tab, text="Battery Health".center(size))

        # App Status Tab
        self.app_status_tab = ttk.Frame(self.notebook)
        app_status_scroll = ScrolledFrame(self.app_status_tab, autohide=True)
        app_status_scroll.pack(fill="both", expand=True)
        self.create_status_widgets(app_status_scroll)
        self.notebook.add(self.app_status_tab, text="App Status".center(size))

        self.notebook.pack(fill="both", expand=True)

    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        logger.info(
            f"Toggling theme from {self.theme} to {'light' if self.theme == 'dark' else 'dark'}"
        )
        self.theme = "light" if self.theme == "dark" else "dark"

        # Update theme
        self.master.style.theme_use(
            self.LIGHT_THEME if self.theme == "light" else self.DARK_THEME
        )

        # Update button styles
        style = "CustomLight.TButton" if self.theme == "light" else "CustomDark.TButton"
        self.style.configure(
            "CustomLight.TButton", background="#ffffff", foreground="#222222"
        )
        self.style.configure(
            "CustomDark.TButton", background="#222222", foreground="#ffffff"
        )
        self.theme_button.configure(text=self.icons[self.theme], style=style)
        # self.reload_btn.configure(style=style)
        self.update_theme()
        logger.debug("Theme toggled successfully")

    def create_app_settings_widgets(self, frame: ttk.Frame) -> None:
        """Create app settings widgets.

        Args:
            frame: The parent frame for the app settings widgets
        """
        # scrolled_frame = ScrolledFrame(frame, autohide=True)
        # scrolled_frame.pack(expand=True, fill="both")
        self._create_form_widgets(frame)

    def _create_form_widgets(self, frame: ttk.Frame) -> None:
        """Create form widgets for the app settings."""
        form_frame = ttk.Frame(frame)

        # Always create button and error label attributes so they exist for __init__ and updates
        button_error_frame = ttk.Frame(form_frame, padding=(0, 20))
        self.error_label = ttk.Label(button_error_frame, text="", foreground="red")
        buttons_frame = ttk.Frame(button_error_frame)
        self.reset_default_button = ttk.Button(
            buttons_frame,
            text="Reset Default",
            command=self.reset_default,
            style="secondary.TButton",
            state="disabled",
        )
        self.reset_button = ttk.Button(
            buttons_frame,
            text="Reset",
            command=self.reset_settings,
            style="danger.TButton",
            state="disabled",
        )
        self.save_button = ttk.Button(
            buttons_frame,
            text="Save",
            command=self.save_settings,
            style="success.TButton",
            state="disabled",
        )

        # Always create these variables so get_current_settings never fails
        import tkinter as tk

        self.enable_power_save_var = tk.BooleanVar(
            value=self.saved_data["PROC_SETTINGS"]["save_power_state_at_percent"]
            is not None
        )
        self.power_save_percent_var = tk.IntVar(
            value=self.saved_data["PROC_SETTINGS"]["save_power_state_at_percent"] or 20
        )
        self.notify_power_change_var = tk.BooleanVar(
            value=self.saved_data["PROC_SETTINGS"]["remind_when_power_state_changes"]
        )
        self.default_power_plan_var = tk.StringVar(
            value=self.saved_data["PROC_SETTINGS"]["default_power_plan"]
        )
        # ToolTips can be added after packing if needed

        # Initialize error tracking attributes
        self.error_count = 0
        self.field_errors = {}

        form_frame.pack(fill="both", padx=30, pady=20, expand=YES)

        # Add trace to all variables to detect changes
        def on_variable_change(*args):
            self._update_button_states()

        # General Settings LabelFrame
        general_labelframe = ttk.LabelFrame(
            form_frame, text="General Settings", style="secondary", padding=(10, 10)
        )
        general_labelframe.grid_columnconfigure(1, weight=1)  # Spacer column
        general_labelframe.grid_columnconfigure(0, weight=0)  # Label column
        general_labelframe.pack(
            fill="x",
            pady=(0, 20),  # Add extra padding at bottom
        )

        # Run on Startup inside General Settings
        run_on_startup_label = ttk.Label(general_labelframe, text="Run on Startup:")
        run_on_startup_label.grid(row=0, column=0, sticky=W, padx=10, pady=(5, 15))
        self.run_on_startup_var = tk.BooleanVar(
            value=self.saved_data["PROC_SETTINGS"]["run_on_startup"]
        )
        self.run_on_startup_var.trace_add("write", on_variable_change)
        run_on_startup_check = ttk.Checkbutton(
            general_labelframe,
            variable=self.run_on_startup_var,
            style="primary-round-toggle",
        )
        run_on_startup_check.grid(row=0, column=1, sticky=E, padx=10, pady=(5, 15))
        ToolTip(
            run_on_startup_check,
            "Start the app automatically when Windows starts",
            bootstyle="info",
        )
        ToolTip(
            run_on_startup_label,
            "Start the app automatically when Windows starts",
            bootstyle="info",
        )

        # Alert when charger plugged
        charger_plugged_label = ttk.Label(
            general_labelframe, text="Alert when Charger Plugged:"
        )
        charger_plugged_label.grid(row=1, column=0, sticky=W, padx=10, pady=(5, 15))
        self.charger_plugged_var = tk.BooleanVar(
            value=self.saved_data["PROC_SETTINGS"]["alert_when_charger_plugged"]
        )
        self.charger_plugged_var.trace_add("write", on_variable_change)
        charger_plugged_check = ttk.Checkbutton(
            general_labelframe,
            variable=self.charger_plugged_var,
            style="primary-round-toggle",
        )
        charger_plugged_check.grid(row=1, column=1, sticky=E, padx=10, pady=(5, 15))
        ToolTip(
            charger_plugged_check,
            "Show notification when charger is connected",
            bootstyle="info",
        )
        ToolTip(
            charger_plugged_label,
            "Show notification when charger is connected",
            bootstyle="info",
        )

        # Alert when charger removed
        charger_removed_label = ttk.Label(
            general_labelframe, text="Alert when Charger Removed:"
        )
        charger_removed_label.grid(row=2, column=0, sticky=W, padx=10, pady=(5, 15))
        self.charger_removed_var = tk.BooleanVar(
            value=self.saved_data["PROC_SETTINGS"]["alert_when_charger_removed"]
        )
        self.charger_removed_var.trace_add("write", on_variable_change)
        charger_removed_check = ttk.Checkbutton(
            general_labelframe,
            variable=self.charger_removed_var,
            style="primary-round-toggle",
        )
        charger_removed_check.grid(row=2, column=1, sticky=E, padx=10, pady=(5, 15))
        ToolTip(
            charger_removed_check,
            "Show notification when charger is disconnected",
            bootstyle="info",
        )
        ToolTip(
            charger_removed_label,
            "Show notification when charger is disconnected",
            bootstyle="info",
        )

        # App Settings LabelFrame
        app_settings_labelframe = ttk.LabelFrame(
            form_frame, text="App Settings", style="secondary", padding=(10, 10)
        )
        app_settings_labelframe.grid_columnconfigure(
            1, weight=1
        )  # Input column expands
        app_settings_labelframe.grid_columnconfigure(0, weight=0)  # Label column
        app_settings_labelframe.pack(
            fill="x",
        )

        # Battery Percentage Settings
        def create_percentage_setting(
            parent,
            label_text,
            row,
            min_val=None,
            max_val=None,
            default=10,
            icon=None,
            icon_padding=5,
            icon_paddingr=2,
        ):
            # Label
            label = ttk.Label(parent, text=f"{label_text} (%):")
            label.grid(row=row, column=0, sticky=W, padx=10, pady=(5, 15))

            # Input frame for right alignment
            input_frame = ttk.Frame(parent)
            input_frame.grid(row=row, column=1, sticky=EW, padx=(0, 10), pady=(5, 15))
            input_frame.grid_columnconfigure(0, weight=1)

            # Icon (if provided)
            icon_label = None
            if icon:
                icon_label = ttk.Label(input_frame, text=icon, font=("Arial", 12))
                icon_label.pack(side=RIGHT, padx=(icon_padding, icon_paddingr))

            # Spinbox
            var = tk.IntVar(value=default)
            spinbox = ttk.Spinbox(
                input_frame,
                from_=0,
                to=max_val or 20,
                textvariable=var,
                width=5,
                wrap=False,
            )
            spinbox.pack(side=RIGHT)
            # Disable mouse wheel changing value
            spinbox.bind("<MouseWheel>", lambda e: "break")
            spinbox.bind("<Button-4>", lambda e: "break")  # Linux scroll up
            spinbox.bind("<Button-5>", lambda e: "break")  # Linux scroll down
            self.field_errors[spinbox] = False  # Track initial error state

            # Warning label
            warning = ttk.Label(
                parent,
                text=f"Warning: Value should be at least {min_val}%" if min_val else "",
                foreground="red",
                font=("Arial", 9),
            )
            warning.grid(
                row=row + 1, column=0, columnspan=2, sticky=W, padx=10, pady=(0, 5)
            )
            warning.grid_remove()

            # Validation
            def validate(*args):
                try:
                    value = var.get()
                    is_error = min_val and value < min_val
                    was_error = self.field_errors[spinbox]

                    if is_error and not was_error:
                        self.error_count += 1
                        self.field_errors[spinbox] = True
                        warning.grid()
                        spinbox.configure(style="Error.TSpinbox")
                    elif not is_error and was_error:
                        self.error_count -= 1
                        self.field_errors[spinbox] = False
                        warning.grid_remove()
                        spinbox.configure(style="default.TSpinbox")

                    # Update error message display
                    if self.error_count > 0:
                        self.error_label.config(
                            text=f"Errors: {self.error_count} remaining"
                        )
                    else:
                        self.error_label.config(text="")

                    # Update button states
                    self._update_button_states()

                except tk.TclError:
                    # Handle cases where input is not a valid integer temporarily
                    is_error = True
                    was_error = self.field_errors[spinbox]
                    if is_error and not was_error:
                        self.error_count += 1
                        self.field_errors[spinbox] = True
                        warning.grid()
                        spinbox.configure(style="Error.TSpinbox")

                    # Update error message display even for invalid input during typing
                    if self.error_count > 0:
                        self.error_label.config(
                            text=f"Errors: {self.error_count} remaining"
                        )
                    else:
                        self.error_label.config(text="")

                    # Update button states
                    self._update_button_states()

            var.trace_add("write", validate)
            var.trace_add("write", on_variable_change)
            return var, spinbox, warning, label, input_frame, icon_label

        def create_time_interval_setting(
            parent,
            label_text,
            row,
            min_seconds,
            max_seconds,
            default_seconds,
            icon=None,
        ):
            # Label
            label = ttk.Label(parent, text=f"{label_text} Interval:")
            label.grid(row=row, column=0, sticky=W, padx=10, pady=(5, 15))

            # Time input frame for right alignment
            time_frame = ttk.Frame(parent)
            time_frame.grid(row=row, column=1, sticky=EW, padx=(0, 10), pady=(5, 15))
            time_frame.grid_columnconfigure(0, weight=1)  # Expanding spacer
            for i in range(1, 5):
                time_frame.grid_columnconfigure(i, weight=0)

            # Minutes
            minutes_var = tk.IntVar(value=default_seconds // 60)
            minutes_spinbox = ttk.Spinbox(
                time_frame,
                from_=0,
                to=59,
                textvariable=minutes_var,
                width=4,
                wrap=False,
            )
            minutes_spinbox.grid(row=0, column=1, sticky=E, padx=(0, 2))
            # Disable mouse wheel changing value
            minutes_spinbox.bind("<MouseWheel>", lambda e: "break")
            minutes_spinbox.bind("<Button-4>", lambda e: "break")
            minutes_spinbox.bind("<Button-5>", lambda e: "break")
            min_label = ttk.Label(time_frame, text="min", width=3, anchor="e")
            min_label.grid(row=0, column=2, sticky=E, padx=(2, 8))

            # Seconds
            seconds_var = tk.IntVar(value=default_seconds % 60)
            seconds_spinbox = ttk.Spinbox(
                time_frame,
                from_=0,
                to=59,
                textvariable=seconds_var,
                width=4,
                wrap=False,
            )
            seconds_spinbox.grid(row=0, column=3, sticky=E, padx=(0, 2))
            # Disable mouse wheel changing value
            seconds_spinbox.bind("<MouseWheel>", lambda e: "break")
            seconds_spinbox.bind("<Button-4>", lambda e: "break")
            seconds_spinbox.bind("<Button-5>", lambda e: "break")
            sec_label = ttk.Label(time_frame, text="sec", width=3, anchor="e")
            sec_label.grid(
                row=0,
                column=4,
                sticky=E,
            )

            # Icon (if provided)
            icon_label = None
            if icon:
                icon_label = ttk.Label(time_frame, text=icon, font=("Arial", 12))
                icon_label.grid(row=0, column=5, sticky=E, padx=(5, 0))

            # Warning label
            warning = ttk.Label(
                parent,
                text=f"Warning: Interval must be between {min_seconds // 60}:{min_seconds % 60:02d} and {max_seconds // 60}:{max_seconds % 60:02d}",
                foreground="red",
                font=("Arial", 9),
            )
            warning.grid(
                row=row + 1, column=0, columnspan=2, sticky=W, padx=10, pady=(0, 5)
            )
            warning.grid_remove()

            # Validation function
            def validate_time(*args):
                try:
                    total_seconds = minutes_var.get() * 60 + seconds_var.get()
                    is_error = (
                        total_seconds < min_seconds or total_seconds > max_seconds
                    )
                    was_error = self.field_errors.get(
                        minutes_spinbox, False
                    ) or self.field_errors.get(seconds_spinbox, False)

                    if is_error and not was_error:
                        self.error_count += 1
                        self.field_errors[minutes_spinbox] = True
                        self.field_errors[seconds_spinbox] = True
                        warning.grid()
                        minutes_spinbox.configure(style="Error.TSpinbox")
                        seconds_spinbox.configure(style="Error.TSpinbox")
                    elif not is_error and was_error:
                        self.error_count -= 1
                        self.field_errors[minutes_spinbox] = False
                        self.field_errors[seconds_spinbox] = False
                        warning.grid_remove()
                        minutes_spinbox.configure(style="default.TSpinbox")
                        seconds_spinbox.configure(style="default.TSpinbox")

                    # Update error message display
                    if self.error_count > 0:
                        self.error_label.config(
                            text=f"Errors: {self.error_count} remaining"
                        )
                    else:
                        self.error_label.config(text="")

                    # Update button states
                    self._update_button_states()

                except tk.TclError:
                    # Handle cases where input is not a valid integer temporarily
                    is_error = True
                    was_error = self.field_errors.get(
                        minutes_spinbox, False
                    ) or self.field_errors.get(seconds_spinbox, False)
                    if is_error and not was_error:
                        self.error_count += 1
                        self.field_errors[minutes_spinbox] = True
                        self.field_errors[seconds_spinbox] = True
                        warning.grid()
                        minutes_spinbox.configure(style="Error.TSpinbox")
                        seconds_spinbox.configure(style="Error.TSpinbox")

                    # Update error message display even for invalid input during typing
                    if self.error_count > 0:
                        self.error_label.config(
                            text=f"Errors: {self.error_count} remaining"
                        )
                    else:
                        self.error_label.config(text="")

                    # Update button states
                    self._update_button_states()

            # Add validation to both spinboxes
            for var in [minutes_var, seconds_var]:
                var.trace_add("write", validate_time)

            self.field_errors[minutes_spinbox] = False  # Track initial error state
            self.field_errors[seconds_spinbox] = False  # Track initial error state

            return (minutes_var, seconds_var), time_frame, warning, label, icon_label

        # Create all percentage settings
        (
            self.low_battery_var,
            low_spinbox,
            low_warning,
            low_label,
            low_input_frame,
            low_icon_label,
        ) = create_percentage_setting(
            app_settings_labelframe,
            "Low Battery Alert",
            0,
            min_val=5,
            max_val=20,
            default=self.saved_data["PROC_SETTINGS"]["low_charge_percent"],
            icon="🔋",
            icon_padding=21 - 6 + 3 + 1,
            icon_paddingr=8,
        )
        tooltip_text = "When battery falls below this percentage, the app will remind you to plug in your device"
        ToolTip(low_spinbox, tooltip_text, bootstyle="info")
        ToolTip(low_label, tooltip_text, bootstyle="info")
        ToolTip(low_icon_label, tooltip_text, bootstyle="info")

        (
            self.high_battery_var,
            high_spinbox,
            high_warning,
            high_label,
            high_input_frame,
            high_icon_label,
        ) = create_percentage_setting(
            app_settings_labelframe,
            "High Battery Alert",
            2,
            min_val=75,
            max_val=94,
            default=self.saved_data["PROC_SETTINGS"]["high_charge_percent"],
            icon="⚡",
            icon_padding=7 + 3 + 3,
            icon_paddingr=0,
        )
        tooltip_text = "When battery reaches this percentage, the app will remind you to remove the charger"
        ToolTip(high_spinbox, tooltip_text, bootstyle="warning")
        ToolTip(high_label, tooltip_text, bootstyle="warning")
        ToolTip(high_icon_label, tooltip_text, bootstyle="warning")

        (
            self.overflow_var,
            overflow_spinbox,
            overflow_warning,
            overflow_label,
            overflow_input_frame,
            overflow_icon_label,
        ) = create_percentage_setting(
            app_settings_labelframe,
            "Overflow Alert",
            4,
            min_val=95,
            max_val=99,
            default=self.saved_data["PROC_SETTINGS"]["overflow_percent"],
            icon="⚠",
            icon_padding=8 + 3,
            icon_paddingr=0,
        )
        tooltip_text = "When battery reaches this percentage, the app will give urgent warnings to remove the charger"
        ToolTip(overflow_spinbox, tooltip_text, bootstyle="danger")
        ToolTip(overflow_label, tooltip_text, bootstyle="danger")
        ToolTip(overflow_icon_label, tooltip_text, bootstyle="danger")

        # Low battery interval (0:30 to 5:30)
        (
            self.low_interval_vars,
            low_interval_frame,
            low_interval_warning,
            low_interval_label,
            low_interval_icon_label,
        ) = create_time_interval_setting(
            app_settings_labelframe,
            "Low Battery",
            6,
            min_seconds=30,
            max_seconds=330,
            default_seconds=self.saved_data["PROC_SETTINGS"]["remind_low_charge_time"],
            icon=None,
        )
        low_interval_tooltip = "How often to remind you to plug in when battery is low. Set between 1:30 and 5:30 minutes"
        ToolTip(low_interval_frame, low_interval_tooltip, bootstyle="info")
        ToolTip(low_interval_label, low_interval_tooltip, bootstyle="info")

        (
            self.high_interval_vars,
            high_interval_frame,
            high_interval_warning,
            high_interval_label,
            high_interval_icon_label,
        ) = create_time_interval_setting(
            app_settings_labelframe,
            "High Battery",
            8,
            min_seconds=30,
            max_seconds=600,
            default_seconds=self.saved_data["PROC_SETTINGS"]["remind_high_charge_time"],
            icon=None,
        )
        high_interval_tooltip = "How often to remind you to unplug when battery is high. Set between 3:00 and 10:00 minutes"
        ToolTip(high_interval_frame, high_interval_tooltip, bootstyle="warning")
        ToolTip(high_interval_label, high_interval_tooltip, bootstyle="warning")
        (
            self.overflow_interval_vars,
            overflow_interval_frame,
            overflow_interval_warning,
            overflow_interval_label,
            overflow_interval_icon_label,
        ) = create_time_interval_setting(
            app_settings_labelframe,
            "Overflow",
            10,
            min_seconds=30,
            max_seconds=180,
            default_seconds=self.saved_data["PROC_SETTINGS"][
                "remind_overflow_charge_time"
            ],
            icon=None,
        )
        overflow_interval_tooltip = "How often to give urgent warnings when battery is at overflow level. Set between 0:30 and 2:00 minutes"
        ToolTip(overflow_interval_frame, overflow_interval_tooltip, bootstyle="danger")
        ToolTip(overflow_interval_label, overflow_interval_tooltip, bootstyle="danger")

        # Power Save Mode Settings (only if power plan is not UNKNOWN)

        current_powerplan = self.saved_data["PROC_SETTINGS"]["default_power_plan"]
        if current_powerplan != "UNKNOWN":
            # --- BEGIN Power Save Mode Settings Block ---
            power_save_labelframe = ttk.LabelFrame(
                form_frame,
                text="Power Save Mode Settings",
                style="secondary",
                padding=(10, 10),
            )
            power_save_labelframe.grid_columnconfigure(
                1, weight=1
            )  # Input column expands
            power_save_labelframe.grid_columnconfigure(0, weight=0)  # Label column
            power_save_labelframe.pack(
                fill="x",
                pady=(0, 20),
            )

            # Enable Power Save Mode
            enable_power_save_label = ttk.Label(
                power_save_labelframe, text="Enable Power Save Mode:"
            )
            enable_power_save_label.grid(
                row=0, column=0, sticky=W, padx=10, pady=(5, 15)
            )
            self.enable_power_save_var.trace_add("write", on_variable_change)
            enable_power_save_check = ttk.Checkbutton(
                power_save_labelframe,
                variable=self.enable_power_save_var,
                style="primary-round-toggle",
            )
            enable_power_save_check.grid(
                row=0, column=1, sticky=E, padx=10, pady=(5, 15)
            )
            ToolTip(
                enable_power_save_check,
                "Automatically switch to Power Saver mode when battery is low",
                bootstyle="info",
            )
            ToolTip(
                enable_power_save_label,
                "Automatically switch to Power Saver mode when battery is low",
                bootstyle="info",
            )

            # Power Save Mode Percentage
            power_save_percent_label = ttk.Label(
                power_save_labelframe, text="Power Save Mode Threshold (%):"
            )
            power_save_percent_label.grid(
                row=1, column=0, sticky=W, padx=10, pady=(5, 15)
            )

            # Input frame for right alignment
            power_save_input_frame = ttk.Frame(power_save_labelframe)
            power_save_input_frame.grid(
                row=1, column=1, sticky=EW, padx=(0, 10), pady=(5, 15)
            )
            power_save_input_frame.grid_columnconfigure(0, weight=1)

            # Icon
            power_save_icon_label = ttk.Label(
                power_save_input_frame, text="🔋", font=("Arial", 12)
            )
            power_save_icon_label.pack(side=RIGHT, padx=(5, 0))

            # Spinbox
            self.power_save_percent_spinbox = ttk.Spinbox(
                power_save_input_frame,
                from_=10,
                to=50,
                textvariable=self.power_save_percent_var,
                width=5,
                wrap=False,
            )
            self.power_save_percent_spinbox.pack(side=RIGHT)
            # Disable mouse wheel changing value
            self.power_save_percent_spinbox.bind("<MouseWheel>", lambda e: "break")
            self.power_save_percent_spinbox.bind("<Button-4>", lambda e: "break")
            self.power_save_percent_spinbox.bind("<Button-5>", lambda e: "break")
            self.field_errors[self.power_save_percent_spinbox] = (
                False  # Track initial error state
            )

            # Warning label
            self.power_save_warning = ttk.Label(
                power_save_labelframe,
                text="Warning: Value should be between 10% and 50%",
                foreground="red",
                font=("Arial", 9),
            )
            self.power_save_warning.grid(
                row=2, column=0, columnspan=2, sticky=W, padx=10, pady=(0, 5)
            )
            self.power_save_warning.grid_remove()

            # Validation for power save percentage (spinbox)
            def validate_power_save_percent_spinbox_main(*args):
                try:
                    value = self.power_save_percent_var.get()
                    is_error = value < 10 or value > 50
                    was_error = self.field_errors[self.power_save_percent_spinbox]

                    if is_error and not was_error:
                        self.error_count += 1
                        self.field_errors[self.power_save_percent_spinbox] = True
                        self.power_save_warning.grid()
                        self.power_save_percent_spinbox.configure(
                            style="Error.TSpinbox"
                        )
                    elif not is_error and was_error:
                        self.error_count -= 1
                        self.field_errors[self.power_save_percent_spinbox] = False
                        self.power_save_warning.grid_remove()
                        self.power_save_percent_spinbox.configure(
                            style="default.TSpinbox"
                        )

                    # Update error message display
                    if self.error_count > 0:
                        self.error_label.config(
                            text=f"Errors: {self.error_count} remaining"
                        )
                    else:
                        self.error_label.config(text="")

                    # Update button states
                    self._update_button_states()

                except tk.TclError:
                    # Handle cases where input is not a valid integer temporarily
                    is_error = True
                    was_error = self.field_errors[self.power_save_percent_spinbox]
                    if is_error and not was_error:
                        self.error_count += 1
                        self.field_errors[self.power_save_percent_spinbox] = True
                        self.power_save_warning.grid()
                        self.power_save_percent_spinbox.configure(
                            style="Error.TSpinbox"
                        )

                    # Update error message display even for invalid input during typing
                    if self.error_count > 0:
                        self.error_label.config(
                            text=f"Errors: {self.error_count} remaining"
                        )
                    else:
                        self.error_label.config(text="")

                    # Update button states
                    self._update_button_states()

                    self.power_save_percent_var.trace_add(
                        "write", validate_power_save_percent_spinbox_main
                    )

            self.power_save_percent_var.trace_add("write", on_variable_change)

            power_save_percent_tooltip = "When battery falls below this percentage, the app will automatically switch to Power Saver mode"
            ToolTip(
                self.power_save_percent_spinbox,
                power_save_percent_tooltip,
                bootstyle="info",
            )
            ToolTip(
                power_save_percent_label, power_save_percent_tooltip, bootstyle="info"
            )
            ToolTip(power_save_icon_label, power_save_percent_tooltip, bootstyle="info")

            # Notify when power state changes
            notify_power_change_label = ttk.Label(
                power_save_labelframe, text="Notify when Power State Changes:"
            )
            notify_power_change_label.grid(
                row=3, column=0, sticky=W, padx=10, pady=(5, 15)
            )
            self.notify_power_change_var.trace_add("write", on_variable_change)
            notify_power_change_check = ttk.Checkbutton(
                power_save_labelframe,
                variable=self.notify_power_change_var,
                style="primary-round-toggle",
            )
            notify_power_change_check.grid(
                row=3, column=1, sticky=E, padx=10, pady=(5, 15)
            )
            ToolTip(
                notify_power_change_check,
                "Show notification when power mode is automatically changed",
                bootstyle="info",
            )
            ToolTip(
                notify_power_change_label,
                "Show notification when power mode is automatically changed",
                bootstyle="info",
            )

            # Function to enable/disable power save fields based on checkbox state
            def toggle_power_save_fields(*args):
                if self.enable_power_save_var.get():
                    self.power_save_percent_spinbox.configure(state="normal")
                    power_save_percent_label.configure(foreground="")
                    power_save_icon_label.configure(foreground="")
                    notify_power_change_check.configure(state="normal")
                    notify_power_change_label.configure(foreground="")
                else:
                    self.power_save_percent_spinbox.configure(state="disabled")
                    power_save_percent_label.configure(foreground="gray")
                    power_save_icon_label.configure(foreground="gray")
                    notify_power_change_check.configure(state="disabled")
                    notify_power_change_label.configure(foreground="gray")

            # Add trace to enable/disable checkbox
            self.enable_power_save_var.trace_add("write", toggle_power_save_fields)

            # Initialize the field state
            toggle_power_save_fields()

            # Default Power Plan
            default_power_plan_label = ttk.Label(
                power_save_labelframe, text="Default Power Plan:"
            )
            default_power_plan_label.grid(
                row=4, column=0, sticky=W, padx=10, pady=(5, 15)
            )

            # Import powerplan module for available plans
            # from battery_reminder.src import powerplan # This import is already at the top

            # Create combobox for power plans
            self.default_power_plan_var.trace_add("write", on_variable_change)

            default_power_plan_combobox = ttk.Combobox(
                power_save_labelframe,
                textvariable=self.default_power_plan_var,
                values=powerplan.get_available_power_plans(),
                state="readonly",
                width=20,
            )
            default_power_plan_combobox.grid(
                row=4, column=1, sticky=E, padx=10, pady=(5, 15)
            )
            # Disable mouse wheel changing value
            default_power_plan_combobox.bind("<MouseWheel>", lambda e: "break")
            default_power_plan_combobox.bind("<Button-4>", lambda e: "break")
            default_power_plan_combobox.bind("<Button-5>", lambda e: "break")
            self.field_errors[default_power_plan_combobox] = (
                False  # Track initial error state
            )

            # Warning label
            self.power_save_warning = ttk.Label(
                power_save_labelframe,
                text="Warning: Value should be between 10% and 50%",
                foreground="red",
                font=("Arial", 9),
            )
            self.power_save_warning.grid(
                row=5, column=0, columnspan=2, sticky=W, padx=10, pady=(0, 5)
            )
            self.power_save_warning.grid_remove()

            # Validation for power save percentage (combobox)
            def validate_power_save_percent_combobox_main(*args):
                try:
                    value = self.default_power_plan_var.get()
                    is_error = value not in powerplan.get_available_power_plans()
                    was_error = self.field_errors[default_power_plan_combobox]

                    if is_error and not was_error:
                        self.error_count += 1
                        self.field_errors[default_power_plan_combobox] = True
                        self.power_save_warning.grid()
                        default_power_plan_combobox.configure(style="Error.TSpinbox")
                    elif not is_error and was_error:
                        self.error_count -= 1
                        self.field_errors[default_power_plan_combobox] = False
                        self.power_save_warning.grid_remove()
                        default_power_plan_combobox.configure(style="default.TSpinbox")

                    # Update error message display
                    if self.error_count > 0:
                        self.error_label.config(
                            text=f"Errors: {self.error_count} remaining"
                        )
                    else:
                        self.error_label.config(text="")

                    # Update button states
                    self._update_button_states()

                except tk.TclError:
                    # Handle cases where input is not a valid integer temporarily
                    is_error = True
                    was_error = self.field_errors[default_power_plan_combobox]
                    if is_error and not was_error:
                        self.error_count += 1
                        self.field_errors[default_power_plan_combobox] = True
                        self.power_save_warning.grid()
                        default_power_plan_combobox.configure(style="Error.TSpinbox")

                    # Update error message display even for invalid input during typing
                    if self.error_count > 0:
                        self.error_label.config(
                            text=f"Errors: {self.error_count} remaining"
                        )
                    else:
                        self.error_label.config(text="")

                    # Update button states
                    self._update_button_states()

                    self.default_power_plan_var.trace_add(
                        "write", validate_power_save_percent_combobox_main
                    )

            self.default_power_plan_var.trace_add("write", on_variable_change)

            default_power_plan_tooltip = (
                "The power plan to restore to when battery level improves"
            )
            ToolTip(
                default_power_plan_combobox,
                default_power_plan_tooltip,
                bootstyle="info",
            )
            ToolTip(
                default_power_plan_label, default_power_plan_tooltip, bootstyle="info"
            )

            # Button and Error Message Frame (always create, only pack if power plan is valid)
            # button_error_frame.pack(fill="x", expand=YES, anchor=S) # This line is moved outside the conditional block
            # self.error_label.pack(side=LEFT, padx=(10, 0)) # This line is moved outside the conditional block
            # buttons_frame.pack(side=RIGHT, padx=(10, 0)) # This line is moved outside the conditional block
            # self.reset_default_button.pack(side=LEFT, padx=(0, 10)) # This line is moved outside the conditional block
            # self.reset_button.pack(side=LEFT, padx=(0, 10)) # This line is moved outside the conditional block
            # self.save_button.pack(side=LEFT) # This line is moved outside the conditional block
        else:
            unknown_label = ttk.Label(
                form_frame,
                text=(
                    "Power Save Mode settings are unavailable because the current power plan could not be detected."
                    "If you believe this is a bug, please file a report through the App Status page."
                ),
                foreground="#888888",  # grey color
                font=("Arial", 10, "italic"),
                wraplength=680,
                justify="left",
            )
            unknown_label.pack(fill="x", pady=(20, 15), padx=(10, 0))

        # End of Power Save Mode Settings block

        # Sound Settings Section
        sound_settings_labelframe = ttk.LabelFrame(
            form_frame,
            text="Sound Settings",
            style="secondary",
            padding=(10, 10),
        )
        sound_settings_labelframe.grid_columnconfigure(
            1, weight=1
        )  # Input column expands
        sound_settings_labelframe.grid_columnconfigure(0, weight=0)  # Label column
        sound_settings_labelframe.pack(
            fill="x",
            pady=(0, 20),
        )

        # Sound settings configuration
        sound_settings_config = [
            {
                "key": "low_battery_sound",
                "label": "Low Battery Sound",
                "default": get_default_sound("too-low"),
                "tooltip": "Sound played when battery level is low",
            },
            {
                "key": "high_battery_sound",
                "label": "High Battery Sound",
                "default": get_default_sound("perfect-battery"),
                "tooltip": "Sound played when battery level is high",
            },
            {
                "key": "overflow_battery_sound",
                "label": "Overflow Battery Sound",
                "default": get_default_sound("battery-overflow"),
                "tooltip": "Sound played when battery is at overflow level",
            },
            {
                "key": "welcome_sound",
                "label": "Welcome Sound",
                "default": None,
                "tooltip": "Sound played when the app starts monitoring",
            },
            {
                "key": "started_charging_sound",
                "label": "Started Charging Sound",
                "default": None,
                "tooltip": "Sound played when charger is connected",
            },
            {
                "key": "charger_disconnected_sound",
                "label": "Charger Disconnected Sound",
                "default": None,
                "tooltip": "Sound played when charger is disconnected",
            },
            {
                "key": "settings_updated_sound",
                "label": "Settings Updated Sound",
                "default": None,
                "tooltip": "Sound played when settings are saved",
            },
            {
                "key": "power_state_changed_sound",
                "label": "Power State Changed Sound",
                "default": None,
                "tooltip": "Sound played when power mode is automatically changed",
            },
            {
                "key": "power_state_restored_sound",
                "label": "Power State Restored Sound",
                "default": None,
                "tooltip": "Sound played when power mode is restored",
            },
        ]

        # Initialize sound variables
        self.sound_vars = {}
        self.sound_labels = {}
        self.sound_edit_buttons = {}
        self.sound_clear_buttons = {}
        # --- Local state for sound settings (unsaved changes) ---
        # Initialize from saved_data
        self.current_sound_data = {}
        for config in sound_settings_config:
            key = config["key"]
            self.current_sound_data[key] = self.saved_data["PROC_SETTINGS"].get(
                key, config["default"]
            )

        def create_sound_setting_row(parent, config, row):
            key = config["key"]
            label_text = config["label"]
            default_value = config["default"]
            tooltip_text = config["tooltip"]

            # Get current value from local state
            current_value = self.current_sound_data.get(key, default_value)

            # Label
            label = ttk.Label(parent, text=f"{label_text}:")
            label.grid(row=row, column=0, sticky=W, padx=10, pady=(5, 15))

            # Value display frame
            value_frame = ttk.Frame(parent)
            value_frame.grid(row=row, column=1, sticky=EW, padx=(0, 10), pady=(5, 15))
            value_frame.grid_columnconfigure(0, weight=1)

            def get_display_value(value):
                if value is None:
                    return "None"
                elif isinstance(value, str) and os.path.exists(value):
                    filename = os.path.basename(value)
                    # foldername = value.split("\\")[-2]
                    # small_name = len(foldername + "\\" + filename) < 20
                    return "...\\" + (
                        # (foldername[:5] + "...\\" + filename)
                        # if not small_name
                        # else (foldername + "\\" + filename)
                        filename
                    )
                else:
                    print(value)
                    return str(value)

            value_var = tk.StringVar(value=get_display_value(current_value))
            value_label = ttk.Label(value_frame, textvariable=value_var, anchor=W)
            value_label.pack(side=LEFT, fill=X, expand=True)

            # Buttons frame
            buttons_frame = ttk.Frame(value_frame)
            buttons_frame.pack(side=RIGHT, padx=(10, 0))

            # Edit button
            edit_button = ttk.Button(
                buttons_frame,
                text="🔍",
                style="info.TButton",
                width=3,
                command=lambda: self._edit_sound_file(key, value_var),
            )
            edit_button.pack(side=LEFT, padx=(0, 5))

            # Clear button
            clear_button = ttk.Button(
                buttons_frame,
                text="❌",
                style="warning.TButton",
                width=3,
                command=lambda: self._clear_sound_file(key, value_var),
            )
            clear_button.pack(side=LEFT)

            self.sound_vars[key] = value_var
            self.sound_labels[key] = value_label
            self.sound_edit_buttons[key] = edit_button
            self.sound_clear_buttons[key] = clear_button

            ToolTip(label, tooltip_text, bootstyle="info")
            ToolTip(value_label, tooltip_text, bootstyle="info")
            ToolTip(edit_button, f"Change the {label_text.lower()}", bootstyle="info")
            ToolTip(
                clear_button, f"Remove the {label_text.lower()}", bootstyle="warning"
            )

        for i, config in enumerate(sound_settings_config):
            create_sound_setting_row(sound_settings_labelframe, config, i)

        # At the end of _create_form_widgets, always pack the button and error frame
        button_error_frame.pack(fill="x", expand=YES, anchor=S)
        self.error_label.pack(side=LEFT, padx=(10, 0))
        buttons_frame.pack(side=RIGHT, padx=(10, 0))
        self.reset_default_button.pack(side=LEFT, padx=(0, 10))
        self.reset_button.pack(side=LEFT, padx=(0, 10))
        self.save_button.pack(side=LEFT)

    def _edit_sound_file(self, key: str, value_var: tk.StringVar) -> None:
        """Open file dialog to select a sound file (local state only)."""
        logger.info(f"Opening file dialog for sound setting: {key}")
        current_path = self.current_sound_data.get(key)
        initial_dir = (
            os.path.dirname(current_path)
            if current_path and os.path.exists(current_path)
            else os.path.expanduser("~")
        )
        file_path = filedialog.askopenfilename(
            title=f"Select sound file for {key.replace('_', ' ').title()}",
            initialdir=initial_dir,
            filetypes=[
                ("WAV files", "*.wav"),
            ],
        )
        if file_path:
            self.current_sound_data[key] = str(Path(file_path))
            filename = os.path.basename(file_path)
            display_value = filename[-10:] if len(filename) > 10 else filename
            value_var.set(display_value)
            self._update_button_states()
            logger.info(f"Sound file updated for {key}: {file_path}")

    def _clear_sound_file(self, key: str, value_var: tk.StringVar) -> None:
        """Clear the sound file setting (local state only)."""
        logger.info(f"Clearing sound file for setting: {key}")
        self.current_sound_data[key] = None
        value_var.set("None")
        self._update_button_states()
        logger.info(f"Sound file cleared for {key}")

    def _update_button_states(self) -> None:
        """Update the state of reset and save buttons based on changes and errors."""
        current_data = self.get_current_settings()
        has_changes = self.has_settings_changed(current_data, ignore_theme=True)
        has_errors = self.error_count > 0
        differs_from_default = self.has_settings_changed(
            self.saved_data, get_default_config(), ignore_theme=True
        )

        # Reset button is enabled if there are changes
        self.reset_button.configure(state="normal" if has_changes else "disabled")

        # Reset Default button is enabled if current settings differ from default
        self.reset_default_button.configure(
            state="normal" if differs_from_default else "disabled"
        )

        # Save button is enabled if there are changes and no errors
        self.save_button.configure(
            state="normal" if not has_errors and has_changes else "disabled"
        )

    def get_current_settings(self) -> AppConfig:
        """Get the current values from all input fields.

        Returns:
            AppConfig: Dictionary containing all current settings
        """
        # Get time values in seconds
        low_min, low_sec = self.low_interval_vars
        high_min, high_sec = self.high_interval_vars
        overflow_min, overflow_sec = self.overflow_interval_vars

        # Handle power save mode settings
        save_power_state_at_percent = None
        if self.enable_power_save_var.get():
            save_power_state_at_percent = self.power_save_percent_var.get()

        # Get sound settings from local state
        sound_settings = {}
        for key in self.sound_vars:
            value = self.current_sound_data.get(key)
            sound_settings[key] = value

        # Create the settings dictionary with proper typing
        proc_settings = {
            "run_on_startup": self.run_on_startup_var.get(),
            "alert_when_charger_plugged": self.charger_plugged_var.get(),
            "alert_when_charger_removed": self.charger_removed_var.get(),
            "low_charge_percent": self.low_battery_var.get(),
            "high_charge_percent": self.high_battery_var.get(),
            "overflow_percent": self.overflow_var.get(),
            "remind_low_charge_time": low_min.get() * 60 + low_sec.get(),
            "remind_high_charge_time": high_min.get() * 60 + high_sec.get(),
            "remind_overflow_charge_time": overflow_min.get() * 60 + overflow_sec.get(),
            "save_power_state_at_percent": save_power_state_at_percent,
            "remind_when_power_state_changes": self.notify_power_change_var.get(),
            "default_power_plan": self.default_power_plan_var.get(),
        }

        # Add sound settings
        proc_settings.update(sound_settings)

        # Cast to AppConfig type to satisfy the type checker
        result: AppConfig = {
            "PROC_SETTINGS": proc_settings,  # type: ignore
            "GUI_SETTINGS": {"theme": self.theme},
        }
        return result

    def has_settings_changed(
        self, new_data: AppConfig, old_data: AppConfig | None = None, ignore_theme=False
    ) -> bool:
        """Check if the new settings differ from the saved settings.

        Args:
            new_data: The new configuration data to compare against
            old_data: The old configuration data to compare against. Defaults to self.saved_data

        Returns:
            bool: True if settings have changed, False otherwise
        """
        og_data = self.saved_data.copy()
        if old_data is not None:
            og_data = old_data.copy()

        # Compare PROC_SETTINGS
        for key, value in new_data["PROC_SETTINGS"].items():
            if og_data["PROC_SETTINGS"][key] != value:
                return True

        # Compare GUI_SETTINGS
        if not ignore_theme:
            for key, value in new_data["GUI_SETTINGS"].items():
                if og_data["GUI_SETTINGS"][key] != value:
                    return True

        return False

    def reset_settings(self):
        """Reset all settings to their saved values."""
        logger.info("Resetting settings to last saved values...")
        # Show confirmation dialog
        result = Messagebox.yesno(
            title="Confirm Reset",
            message="Are you sure you want to reset all settings to their last saved values?",
            parent=self.master,
        )

        if result == "Yes":
            # Reset PROC_SETTINGS
            self.run_on_startup_var.set(
                self.saved_data["PROC_SETTINGS"]["run_on_startup"]
            )
            self.charger_plugged_var.set(
                self.saved_data["PROC_SETTINGS"]["alert_when_charger_plugged"]
            )
            self.charger_removed_var.set(
                self.saved_data["PROC_SETTINGS"]["alert_when_charger_removed"]
            )
            self.low_battery_var.set(
                self.saved_data["PROC_SETTINGS"]["low_charge_percent"]
            )
            self.high_battery_var.set(
                self.saved_data["PROC_SETTINGS"]["high_charge_percent"]
            )
            self.overflow_var.set(self.saved_data["PROC_SETTINGS"]["overflow_percent"])

            # Reset time intervals
            low_min, low_sec = self.low_interval_vars
            high_min, high_sec = self.high_interval_vars
            overflow_min, overflow_sec = self.overflow_interval_vars

            low_min.set(
                self.saved_data["PROC_SETTINGS"]["remind_low_charge_time"] // 60
            )
            low_sec.set(self.saved_data["PROC_SETTINGS"]["remind_low_charge_time"] % 60)
            high_min.set(
                self.saved_data["PROC_SETTINGS"]["remind_high_charge_time"] // 60
            )
            high_sec.set(
                self.saved_data["PROC_SETTINGS"]["remind_high_charge_time"] % 60
            )
            overflow_min.set(
                self.saved_data["PROC_SETTINGS"]["remind_overflow_charge_time"] // 60
            )
            overflow_sec.set(
                self.saved_data["PROC_SETTINGS"]["remind_overflow_charge_time"] % 60
            )

            # Reset power save mode settings
            self.enable_power_save_var.set(
                self.saved_data["PROC_SETTINGS"]["save_power_state_at_percent"]
                is not None
            )
            self.power_save_percent_var.set(
                self.saved_data["PROC_SETTINGS"]["save_power_state_at_percent"] or 20
            )
            self.notify_power_change_var.set(
                self.saved_data["PROC_SETTINGS"]["remind_when_power_state_changes"]
            )
            self.default_power_plan_var.set(
                self.saved_data["PROC_SETTINGS"]["default_power_plan"]
            )

            # Reset sound settings from saved_data
            for key in self.sound_vars:
                value = self.saved_data["PROC_SETTINGS"].get(key)
                self.current_sound_data[key] = value
                if value is None:
                    self.sound_vars[key].set("None")
                else:
                    filename = os.path.basename(value)
                    display_value = filename[-10:] if len(filename) > 10 else filename
                    self.sound_vars[key].set(display_value)
            self._update_button_states()
            logger.info("Settings reset to last saved values")

    def update_theme(self):
        data = self.saved_data.copy()
        data["GUI_SETTINGS"]["theme"] = self.theme
        save_config(data)

    def save_settings(self):
        """Save the current settings and update the saved data."""
        logger.info("Saving settings...")
        old_startup_setting = self.saved_data["PROC_SETTINGS"]["run_on_startup"]
        current_data = self.get_current_settings()

        # Save the data
        save_config(current_data)

        # Update the saved data reference
        self.saved_data = current_data

        # Handle startup setting changes
        if self.saved_data["PROC_SETTINGS"]["run_on_startup"] != old_startup_setting:
            try:
                if self.saved_data["PROC_SETTINGS"]["run_on_startup"]:
                    success = add_to_startup()
                    if not success:
                        Messagebox.show_warning(
                            title="Startup Setting Failed",
                            message="Failed to add the app to startup. Please try running the app as administrator.",
                            parent=self.master,
                        )
                else:
                    success = remove_from_startup()
                    if not success:
                        Messagebox.show_warning(
                            title="Startup Setting Failed",
                            message="Failed to remove the app from startup. Please try running the app as administrator.",
                            parent=self.master,
                        )
            except Exception as e:
                logger.error(f"Error updating startup setting: {e}")
                Messagebox.show_error(
                    title="Startup Setting Error",
                    message=f"An error occurred while updating startup settings: {str(e)}",
                    parent=self.master,
                )

        # Update local sound state from saved (in case of normalization)
        for key in self.sound_vars:
            self.current_sound_data[key] = self.saved_data["PROC_SETTINGS"].get(key)

        # Update button states
        self._update_button_states()
        logger.info("Settings saved successfully")
        self.on_update_callback()

    def create_battery_health_widgets(self, frame: ttk.Frame) -> None:
        """Create battery health monitoring widgets.

        Args:
            frame: The parent frame for the battery health widgets
        """
        container = ttk.Frame(frame)
        container.pack(fill="both", padx=(20, 20))
        self._create_top_details(container)
        self._create_bottom_details(container)

    def _create_top_details(self, frame: ttk.Frame) -> None:
        """Create the top section of battery details.

        Args:
            frame: The parent frame for the top details
        """
        top_details_frame = ttk.Frame(frame)
        top_details_frame.pack(fill=X, pady=(0, 30))

        left_details = ttk.Frame(top_details_frame)
        right_details = ttk.Frame(top_details_frame)

        left_details.grid(row=0, column=0, sticky="nsew", padx=(0, 30))
        right_details.grid(row=0, column=1, sticky="nsew", padx=(30, 0))

        top_details_frame.grid_columnconfigure(0, weight=1)
        top_details_frame.grid_columnconfigure(1, weight=1)

        for details_frame in (left_details, right_details):
            details_frame.grid_columnconfigure(0, weight=0)
            details_frame.grid_columnconfigure(1, weight=1)

        data = self.battery_data_manager.get_battery_data()

        details_data = [
            (left_details, "vendor"),
            (left_details, "model"),
            (left_details, "temperature"),
            (right_details, "technology"),
            (right_details, "voltage"),
            (right_details, "energy_rate"),
        ]

        self.battery_detail_labels = {}
        for i, (parent_frame, key) in enumerate(details_data):
            self._create_detail_row(parent_frame, key, data[key], i % 3)

    def _create_detail_row(
        self, parent_frame: ttk.Frame, key: str, value: Any, row_idx: int
    ) -> None:
        """Create a single detail row with label and value.

        Args:
            parent_frame: The parent frame for the detail row
            key: The property key
            value: The property value
            row_idx: The row index in the grid
        """
        # Label and info icon frame
        label_info_frame = ttk.Frame(parent_frame)
        label_info_frame.grid(row=row_idx, column=0, sticky=W, padx=10, pady=8)

        text = key.replace("_", " ").capitalize() + ":"
        property_label = ttk.Label(label_info_frame, text=text)
        property_label.pack(side=LEFT)

        info_icon = ttk.Label(label_info_frame, text="𝒊", font=("Arial", 9, "bold"))
        info_icon.pack(side=LEFT, padx=(5, 0))

        # Add tooltips
        if key in self.TOOLTIP_DESCRIPTIONS:
            ToolTip(info_icon, text=self.TOOLTIP_DESCRIPTIONS[key])
            ToolTip(property_label, text=self.TOOLTIP_DESCRIPTIONS[key])

        # Value label
        val_text = str(value)
        value_label = ttk.Label(parent_frame, text=val_text, width=20, anchor=E)
        value_label.grid(row=row_idx, column=1, sticky=E, padx=10, pady=8)
        self.battery_detail_labels[key] = value_label

        if key in self.TOOLTIP_DESCRIPTIONS:
            ToolTip(value_label, text=self.TOOLTIP_DESCRIPTIONS[key])

    def _create_bottom_details(self, frame: ttk.Frame) -> None:
        """Create the bottom section with meter and energy details.

        Args:
            frame: The parent frame for the bottom details
        """
        self.bottom_frame = ttk.Frame(frame)
        self.bottom_frame.pack(fill="both", expand=YES)

        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.rowconfigure(0, weight=1)
        self.bottom_frame.rowconfigure(1, weight=1)

        data = self.battery_data_manager.get_battery_data()

        # Create meter
        self.meter = ttk.Meter(
            self.bottom_frame,
            metersize=self.METER_SIZE,
            padding=30,
            amountused=data["capacity"].value,
            amounttotal=100,
            metertype="full",
            arcrange=self.METER_ARC_RANGE,
            textright="%",
            subtext="Battery Health",
            style=INFO,
        )
        self.meter.grid(row=0, column=0, pady=(20, 0), sticky="nsew")
        ToolTip(self.meter, text=self.TOOLTIP_DESCRIPTIONS["capacity"])

        # Create energy details
        self._create_energy_details(data)

    def _create_energy_details(self, data: Dict[str, Any]) -> None:
        """Create energy details section.

        Args:
            data: Battery data dictionary
        """
        energy_details_frame = ttk.Frame(self.bottom_frame)
        energy_details_frame.grid(row=1, column=0, pady=(0, 20), sticky="nsew")

        label_container_frame = ttk.Frame(energy_details_frame)
        label_container_frame.pack(expand=YES, anchor="center")

        # Energy Full
        energy_full_label = ttk.Label(label_container_frame, text="Energy Full:")
        energy_full_label.pack(side=LEFT, padx=5)
        self.energy_full_value_label = ttk.Label(
            label_container_frame, text=data["energy_full"]
        )
        self.energy_full_value_label.pack(side=LEFT, padx=5)
        ToolTip(energy_full_label, text=self.TOOLTIP_DESCRIPTIONS["energy_full"])
        ToolTip(
            self.energy_full_value_label, text=self.TOOLTIP_DESCRIPTIONS["energy_full"]
        )

        # Energy Original Full
        energy_original_full_label = ttk.Label(
            label_container_frame, text="Energy Original Full:"
        )
        energy_original_full_label.pack(side=LEFT, padx=(20, 5))
        self.energy_original_full_value_label = ttk.Label(
            label_container_frame, text=data["energy_full_design"]
        )
        self.energy_original_full_value_label.pack(side=LEFT, padx=5)
        ToolTip(
            energy_original_full_label,
            text=self.TOOLTIP_DESCRIPTIONS["energy_full_design"],
        )
        ToolTip(
            self.energy_original_full_value_label,
            text=self.TOOLTIP_DESCRIPTIONS["energy_full_design"],
        )

    def update_battery_health_widgets(self) -> None:
        """Update all battery health related widgets with fresh data."""
        data = self.battery_data_manager.get_battery_data()

        for key, value in data.items():
            if key not in self.battery_detail_labels or key == "capacity":
                continue

            self.battery_detail_labels[key].configure(text=value)

        # Update meter
        self.meter.configure(amountused=data["capacity"].value)

        # Update energy labels
        self.energy_full_value_label.configure(text=data["energy_full"])
        self.energy_original_full_value_label.configure(text=data["energy_full_design"])

        # Update detail labels
        # self.battery_detail_labels["voltage"].configure(text=data["voltage"])
        # self.battery_detail_labels["temperature"].configure(text=data["temperature"])

    def reset_default(self, check=True) -> None:
        """Reset all settings to their default values."""
        logger.info("Resetting settings to default values...")
        # Show confirmation dialog

        result = (
            Messagebox.yesno(
                title="Confirm Reset to Default",
                message="Are you sure you want to reset all settings to their default values? This cannot be undone.",
                parent=self.master,
            )
            if check
            else "Yes"
        )

        if result == "Yes":
            # Reset PROC_SETTINGS
            self.run_on_startup_var.set(
                get_default_config()["PROC_SETTINGS"]["run_on_startup"]
            )
            self.charger_plugged_var.set(
                get_default_config()["PROC_SETTINGS"]["alert_when_charger_plugged"]
            )
            self.charger_removed_var.set(
                get_default_config()["PROC_SETTINGS"]["alert_when_charger_removed"]
            )
            self.low_battery_var.set(
                get_default_config()["PROC_SETTINGS"]["low_charge_percent"]
            )
            self.high_battery_var.set(
                get_default_config()["PROC_SETTINGS"]["high_charge_percent"]
            )
            self.overflow_var.set(
                get_default_config()["PROC_SETTINGS"]["overflow_percent"]
            )

            # Reset time intervals
            low_min, low_sec = self.low_interval_vars
            high_min, high_sec = self.high_interval_vars
            overflow_min, overflow_sec = self.overflow_interval_vars

            low_min.set(
                get_default_config()["PROC_SETTINGS"]["remind_low_charge_time"] // 60
            )
            low_sec.set(
                get_default_config()["PROC_SETTINGS"]["remind_low_charge_time"] % 60
            )
            high_min.set(
                get_default_config()["PROC_SETTINGS"]["remind_high_charge_time"] // 60
            )
            high_sec.set(
                get_default_config()["PROC_SETTINGS"]["remind_high_charge_time"] % 60
            )
            overflow_min.set(
                get_default_config()["PROC_SETTINGS"]["remind_overflow_charge_time"]
                // 60
            )
            overflow_sec.set(
                get_default_config()["PROC_SETTINGS"]["remind_overflow_charge_time"]
                % 60
            )

            # Reset power save mode settings
            self.enable_power_save_var.set(
                get_default_config()["PROC_SETTINGS"]["save_power_state_at_percent"]
                is not None
            )
            self.power_save_percent_var.set(
                get_default_config()["PROC_SETTINGS"]["save_power_state_at_percent"]
                or 20
            )
            self.notify_power_change_var.set(
                get_default_config()["PROC_SETTINGS"]["remind_when_power_state_changes"]
            )
            self.default_power_plan_var.set(
                get_default_config()["PROC_SETTINGS"]["default_power_plan"]
            )

            # Reset sound settings to defaults
            for key in self.sound_vars:
                default_value = get_default_config()["PROC_SETTINGS"].get(key)
                self.current_sound_data[key] = default_value
                if default_value is None:
                    self.sound_vars[key].set("None")
                else:
                    filename = os.path.basename(default_value)
                    display_value = filename[-10:] if len(filename) > 10 else filename
                    self.sound_vars[key].set(display_value)
            self._update_button_states()
            logger.info("Settings reset to default values")

    def _retry_battery_settings(self):
        logger.debug("Attempting to retry battery settings detection.")
        if self.saved_data["PROC_SETTINGS"]["default_power_plan"] != "UNKNOWN":
            logger.info(
                "Default power plan already detected: %s",
                self.saved_data["PROC_SETTINGS"]["default_power_plan"],
            )
            return

        new_plan = powerplan.get_current_scheme_name()
        logger.debug("Current power plan detected: %s", new_plan)

        if new_plan != "UNKNOWN":
            self.saved_data["PROC_SETTINGS"]["default_power_plan"] = new_plan
            save_config(self.saved_data)
            logger.info(
                "Power plan '%s' detected and saved. Rebuilding app settings tab.",
                new_plan,
            )

            # Rebuild the app settings tab to show power save mode settings
            self._rebuild_app_settings_tab()
            return

        logger.warning("Power plan still not detected. Will retry in 10 seconds.")
        # Schedule next update
        self.master.after(10000, self._retry_battery_settings)

    def _rebuild_app_settings_tab(self):
        """Rebuild the app settings tab to reflect changes in power plan detection."""
        logger.info("Rebuilding app settings tab due to power plan detection")

        # Store current tab selection
        current_tab = self.notebook.index(self.notebook.select())

        # Remove the old app settings tab
        self.notebook.forget(self.app_settings_tab)

        # Create new app settings tab
        self.app_settings_tab = ttk.Frame(self.notebook)
        app_settings_scroll = ScrolledFrame(self.app_settings_tab, autohide=True)
        app_settings_scroll.pack(fill="both", expand=True)
        self.create_app_settings_widgets(app_settings_scroll)

        # Add the new tab at the same position
        self.notebook.insert(0, self.app_settings_tab, text="App Settings".center(20))

        # Restore tab selection
        self.notebook.select(current_tab)

        # Update button states
        self._update_button_states()

        self.notify_powerplan_works_again()

        logger.info("App settings tab rebuilt successfully")

    def _reload_data(self):
        """Reload the data from the config file."""
        try:
            data = self.battery_data_manager.get_battery_data()
            logger.debug("Reloading battery data")

            # Update all detail labels
            for key, value in data.items():
                if key not in self.battery_detail_labels or key == "capacity":
                    continue
                self.battery_detail_labels[key].configure(text=str(value))

            # Update meter with capacity
            if hasattr(data["capacity"], "value"):
                self.meter.configure(amountused=data["capacity"].value)
            else:
                self.meter.configure(amountused=0)

            # Update energy labels
            self.energy_full_value_label.configure(text=str(data["energy_full"]))
            self.energy_original_full_value_label.configure(
                text=str(data["energy_full_design"])
            )

        except Exception as e:
            logger.error(f"Error updating battery data: {str(e)}")
            # Set loading state for all fields
            for label in self.battery_detail_labels.values():
                label.configure(text="Loading...")
            self.meter.configure(amountused=0)
            self.energy_full_value_label.configure(text="Loading...")
            self.energy_original_full_value_label.configure(text="Loading...")

        # Schedule next update
        self.master.after(1000, self._reload_data)

    def create_status_widgets(self, frame: ttk.Frame) -> None:
        """Create app status widgets.

        Args:
            frame: The parent frame for the app status widgets
        """
        # Main content frame for consistent padding
        content_frame = ttk.Frame(frame)
        content_frame.pack(fill="both", padx=30, pady=20, expand=YES)

        # Status Frame
        status_frame = ttk.Frame(content_frame)
        status_frame.pack(fill="none", pady=(0, 20), anchor="center")

        # Status Label
        status_label = ttk.Label(
            status_frame,
            text="Current App Status:",
            font=("Arial", 10, "bold"),
        )
        status_label.pack(side=LEFT, padx=(0, 10))

        # Status Value Label
        self.status_value_label = ttk.Label(
            status_frame,
            text="STOPPED",
            font=("Arial", 10, "bold"),
            foreground="red",
        )
        self.status_value_label.pack(side=LEFT)

        # Buttons Frame
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.pack(fill="none", pady=(0, 20), anchor="center")

        # Start Button
        self.start_button = ttk.Button(
            buttons_frame,
            text="Start App",
            command=self._start_app,
            style="success.TButton",
            width=15,
        )
        self.start_button.pack(side=LEFT, padx=(0, 10))
        ToolTip(
            self.start_button,
            "Start the battery monitoring service",
            bootstyle="success",
        )

        # Stop Button
        self.stop_button = ttk.Button(
            buttons_frame,
            text="Stop App",
            command=self._stop_app,
            style="warning.TButton",
            width=15,
            state="disabled",
        )
        self.stop_button.pack(side=LEFT, padx=(0, 10))
        ToolTip(
            self.stop_button, "Stop the battery monitoring service", bootstyle="warning"
        )

        def _quit_app() -> None:
            """Quit the application with confirmation."""
            logger.info("User requested to quit application")
            result = Messagebox.yesno(
                title="Confirm Quit",
                message="Are you sure you want to quit the application? This will stop all battery monitoring services.",
                parent=self.master,
            )

            if result == "Yes":
                logger.info("User confirmed quit - calling quit_app function")
                self.quit_app()
            else:
                logger.info("User cancelled quit operation")

        self.quit_button = ttk.Button(
            buttons_frame,
            text="QUIT APP",
            command=_quit_app,
            style="danger.TButton",
            width=15,
        )
        self.quit_button.pack(side=LEFT)
        ToolTip(self.quit_button, "Quit the application entirely", bootstyle="danger")

        ttk.Separator(content_frame, orient="horizontal", style="default").pack(
            fill="x", pady=(20, 15)
        )

        github_frame = ttk.LabelFrame(
            content_frame,
            text="   Have a Github Account?   ",
            style="default",
            padding=(10, 10),
        )
        github_frame.pack(
            fill="x",
            pady=(20, 10),  # Add extra padding at bottom
        )

        # Github Button
        ttk.Button(
            github_frame,
            text="Report Bug/Issue 🐛",
            command=lambda: self._open_url(
                "https://github.com/KidCoderT/biryani-battery-reminder/issues/new?template=bug_report.md"
            ),
            style="info.TButton",
            width=20,
        ).pack(fill="x")

        ttk.Button(
            github_frame,
            text="Suggest a Feature 💡",
            command=lambda: self._open_url(
                "https://github.com/KidCoderT/biryani-battery-reminder/issues/new?template=feature_request.md"
            ),
            style="primary.TButton",
            width=20,
        ).pack(fill="x", pady=(10, 0))

        gmail_frame = ttk.LabelFrame(
            content_frame,
            text="   Or, send me an email!   ",
            style="default",
            padding=(10, 10),
        )
        gmail_frame.pack(
            fill="x",
            pady=(20, 20),  # Add extra padding at bottom
        )
        ttk.Button(
            gmail_frame,
            text="Send Email 📧",
            command=lambda: self._open_mailto("coder52057@gmail.com"),
            style="success.TButton",
            width=20,
        ).pack(fill="x", pady=(0, 0))

        # If the above options don't work or you need further assistance, please email me directly at coder52057@gmail.com.
        ttk.Label(
            content_frame,
            text="If the above options don't work, you can directly email ",
            font=("Arial", 9, "italic"),
            foreground="#888888",
            anchor="center",
            justify="center",
        ).pack(fill="x", pady=(0, 0))
        ttk.Label(
            content_frame,
            text="coder52057@gmail.com",
            font=("Arial", 10, "bold"),
            foreground="#222222",
            anchor="center",
            justify="center",
            wraplength=500,
        ).pack(fill="x", pady=(0, 10))

        ttk.Separator(content_frame, orient="horizontal", style="default").pack(
            fill="x", pady=(10, 10)
        )

        # Appreciation label for starring the repo
        ttk.Label(
            content_frame,
            text="Like this app? Star the repo and share your feeback to show your appreciation!",
            font=("Arial", 11, "normal"),
            anchor="center",
            justify="center",
            wraplength=500,
        ).pack(fill="x", pady=(0, 5))

        # Star the GitHub repo button
        ttk.Button(
            content_frame,
            text="⭐ Star the GitHub Repo!",
            command=lambda: self._open_url(
                "https://github.com/KidCoderT/biryani-battery-reminder"
            ),
            style="default.TButton",
            width=25,
        ).pack(fill="x", pady=(0, 5))

        # Review button (Product Hunt as example)
        ttk.Button(
            content_frame,
            text="📝 Leave a Review!",
            command=lambda: self._open_url(
                "https://www.producthunt.com/products/biryani-battery-reminder"
            ),
            style="warning.TButton",
            width=25,
        ).pack(fill="x", pady=(5, 10))

        # Initialize app status
        self._update_app_status()

    def _update_app_status(self) -> None:
        """Update the app status display and button states."""
        is_running = self.check_bg_proc_stat()

        # Update status label
        self.status_value_label.configure(
            text="RUNNING" if is_running else "STOPPED",
            foreground="green" if is_running else "red",
        )

        # Update button states
        self.start_button.configure(state="disabled" if is_running else "normal")
        self.stop_button.configure(state="normal" if is_running else "disabled")

    def _start_app(self) -> None:
        """Start the battery monitoring service."""
        logger.info("Starting battery monitoring service...")
        try:
            self.start_proc()
            self._update_app_status()
            # Messagebox.ok(
            #     title="Success",
            #     message="Battery monitoring service has been started.",
            #     parent=self.master,
            # )
            logger.info("Battery monitoring service started successfully")
        except Exception as e:
            logger.error(f"Failed to start battery monitoring service: {str(e)}")
            Messagebox.show_error(
                title="Error",
                message=f"Failed to start the service: {str(e)}",
                parent=self.master,
            )

    def _stop_app(self) -> None:
        """Stop the battery monitoring service."""
        logger.info("Stopping battery monitoring service...")
        try:
            self.stop_proc()
            self._update_app_status()
            # Messagebox.ok(
            #     title="Success",
            #     message="Battery monitoring service has been stopped.",
            #     parent=self.master,
            # )
            logger.info("Battery monitoring service stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop battery monitoring service: {str(e)}")
            Messagebox.show_error(
                title="Error",
                message=f"Failed to stop the service: {str(e)}",
                parent=self.master,
            )

    def _open_url(self, url: str) -> None:
        """Open a URL in the default web browser."""
        try:
            webbrowser.open_new(url)
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            Messagebox.show_error(
                title="Error",
                message=f"Failed to open the link: {str(e)}",
                parent=self.master,
            )

    def _open_mailto(self, email: str) -> None:
        """Open the default mail client with a mailto link."""
        try:
            webbrowser.open_new(f"mailto:")
            webbrowser.open_new(
                f"https://mail.google.com/mail/?view=cm&to={email}&su=Hello.%20Regarding%20Biryani&body=This%20is%20the%20body"
            )
        except Exception as e:
            logger.error(f"Failed to open mailto for {email}: {e}")
            Messagebox.show_error(
                title="Error",
                message=f"Failed to open the mail client: {str(e)}",
                parent=self.master,
            )


def main(debug=False):
    """Main entry point for the application."""
    root = ttk.Window(
        title="Biryani (Battery Reminder)", themename="litera", size=(650, 550)
    )
    app = AppSettingUI(root, hide_gui_on_close=not debug)
    root.mainloop()
