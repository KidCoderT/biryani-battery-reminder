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

import tkinter as tk
from typing import Any, Dict, Literal
from PIL import Image, ImageTk
import webbrowser

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
from battery_reminder.src.logger_config import setup_logger
from battery_reminder.src.startup_manager import add_to_startup, remove_from_startup
from battery_reminder.src.assets_manager import get_tkinter_icon

# Initialize logger
logger = setup_logger()


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
        logger.info("Settings GUI initialized successfully")

    def on_closing(self):
        logger.info("Settings GUI closing...")
        # When the user closes the GUI, hide it instead of destroying it
        # so the system tray icon can still bring it back.
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

        # Button and Error Message Frame
        button_error_frame = ttk.Frame(form_frame, padding=(0, 20))
        button_error_frame.pack(fill="x", expand=YES, anchor=S)

        # Error Message Label
        self.error_label = ttk.Label(button_error_frame, text="", foreground="red")
        self.error_label.pack(side=LEFT, padx=(10, 0))

        # Buttons Frame (to right-align buttons)
        buttons_frame = ttk.Frame(button_error_frame)
        buttons_frame.pack(side=RIGHT, padx=(10, 0))

        # Reset Default
        self.reset_default_button = ttk.Button(
            buttons_frame,
            text="Reset Default",
            command=self.reset_default,
            style="secondary.TButton",
            state="disabled",
        )
        self.reset_default_button.pack(side=LEFT, padx=(0, 10))
        ToolTip(
            self.reset_default_button,
            "Reset all settings to their default values",
            bootstyle="info",
        )

        # Reset Button
        self.reset_button = ttk.Button(
            buttons_frame,
            text="Reset",
            command=self.reset_settings,
            style="danger.TButton",
            state="disabled",
        )
        self.reset_button.pack(side=LEFT, padx=(0, 10))
        ToolTip(
            self.reset_button,
            "Reset all settings to their last saved values",
            bootstyle="info",
        )

        # Save Button
        self.save_button = ttk.Button(
            buttons_frame,
            text="Save",
            command=self.save_settings,
            style="success.TButton",
            state="disabled",
        )
        self.save_button.pack(side=LEFT)
        ToolTip(self.save_button, "Save current settings", bootstyle="info")

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

        return {
            "PROC_SETTINGS": {
                "run_on_startup": self.run_on_startup_var.get(),
                "alert_when_charger_plugged": self.charger_plugged_var.get(),
                "alert_when_charger_removed": self.charger_removed_var.get(),
                "low_charge_percent": self.low_battery_var.get(),
                "high_charge_percent": self.high_battery_var.get(),
                "overflow_percent": self.overflow_var.get(),
                "remind_low_charge_time": low_min.get() * 60 + low_sec.get(),
                "remind_high_charge_time": high_min.get() * 60 + high_sec.get(),
                "remind_overflow_charge_time": overflow_min.get() * 60
                + overflow_sec.get(),
            },
            "GUI_SETTINGS": {"theme": self.theme},
        }

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

            # Update button states
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

        # Show notification using Messagebox
        # Messagebox.ok(
        #     title="Settings Saved",
        #     message="Your settings have been successfully updated.",
        #     parent=self.master,
        # )

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

    def reset_default(self) -> None:
        """Reset all settings to their default values."""
        logger.info("Resetting settings to default values...")
        # Show confirmation dialog
        result = Messagebox.yesno(
            title="Confirm Reset to Default",
            message="Are you sure you want to reset all settings to their default values? This cannot be undone.",
            parent=self.master,
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

            # Update button states
            self._update_button_states()
            logger.info("Settings reset to default values")

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
