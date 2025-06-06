# TODO: OBSERVER CLASS
# TODO: MAKE THE GUI AND BACK PROC INDEP

import tkinter as tk
from typing import Literal, Dict, Any
import ttkbootstrap as ttk
from ttkbootstrap import style
from ttkbootstrap.constants import *
from ttkbootstrap.tooltip import ToolTip
from ttkbootstrap.icons import Emoji

from battery_reminder.src.background_proc import BackgroundProcessManager


class AppSettingUI:
    """Main application UI class for Battery Reminder."""

    # Theme Configuration
    LIGHT_THEME = "litera"
    DARK_THEME = "darkly"

    # UI Constants
    WINDOW_SIZE = "820x900"
    METER_SIZE = 180
    METER_ARC_RANGE = 360

    # Tooltip Descriptions
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

    def __init__(self, main_window: ttk.Window) -> None:
        """Initialize the application UI.

        Args:
            main_window: The main ttkbootstrap window instance
        """
        self.master = main_window
        self._setup_window()
        self._initialize_theme()
        self._create_main_layout()
        self._create_header()
        self._create_notebook()

    def _setup_window(self) -> None:
        """Configure the main window properties."""
        self.master.geometry(self.WINDOW_SIZE)
        self.master.resizable(False, False)

    def _initialize_theme(self) -> None:
        """Initialize theme-related settings and styles."""
        self.theme: Literal["light", "dark"] = "light"
        self.master.style.theme_use(self.LIGHT_THEME)

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

        self.icons = {
            "dark": " ☀",
            "light": "🌕",
        }

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
            text="Biryani (Battery Reminder)",
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

        # App Settings Tab
        self.app_settings_tab = ttk.Frame(self.notebook)
        self.create_app_settings_widgets(self.app_settings_tab)
        self.notebook.add(self.app_settings_tab, text="App Settings".center(60))

        # Battery Health Tab
        self.battery_health_tab = ttk.Frame(self.notebook, padding=(20, 20))
        self.create_battery_health_widgets(self.battery_health_tab)
        self.notebook.add(self.battery_health_tab, text="Battery Health".center(60))

        self.notebook.pack(fill="both", expand=True)

    def toggle_theme(self) -> None:
        """Toggle between light and dark themes."""
        self.theme = "light" if self.theme == "dark" else "dark"

        # Update theme
        self.master.style.theme_use(
            self.LIGHT_THEME if self.theme == "light" else self.DARK_THEME
        )

        # Update button styles
        self.style.configure(
            "CustomLight.TButton", background="#ffffff", foreground="#222222"
        )
        self.style.configure(
            "CustomDark.TButton", background="#222222", foreground="#ffffff"
        )

        style = "CustomDark.TButton" if self.theme == "light" else "CustomLight.TButton"
        self.theme_button.config(text=self.icons[self.theme], style=style)

        self.update_elements_on_theme_change()

    def update_elements_on_theme_change(self) -> None:
        """Update UI elements when theme changes."""
        if self.theme == "light":
            self.meter.configure(bootstyle=DEFAULT)
        else:
            self.meter.configure(bootstyle=INFO)

    def create_app_settings_widgets(self, frame: ttk.Frame) -> None:
        """Create app settings widgets.

        Args:
            frame: The parent frame for the app settings widgets
        """
        self._create_form_widgets(frame)

    def _create_form_widgets(self, frame: ttk.Frame) -> None:
        """Create form widgets for the app settings."""
        form_frame = ttk.Frame(frame)

        # form_frame.grid_columnconfigure(1, weight=1)  # Spacer column
        # form_frame.grid_columnconfigure(0, weight=0)  # Label column
        form_frame.pack(fill="both", padx=30, pady=20, expand=YES)

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
        self.run_on_startup_var = tk.BooleanVar(value=False)
        run_on_startup_check = ttk.Checkbutton(
            general_labelframe,
            variable=self.run_on_startup_var,
            style="success-round-toggle",
        )
        run_on_startup_check.grid(row=0, column=1, sticky=E, padx=10, pady=(5, 15))

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
                    if min_val and value < min_val:
                        warning.grid()
                    else:
                        warning.grid_remove()
                except tk.TclError:
                    pass

            var.trace_add("write", validate)
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
                    if total_seconds < min_seconds or total_seconds > max_seconds:
                        warning.grid()
                    else:
                        warning.grid_remove()
                except tk.TclError:
                    pass

            # Add validation to both spinboxes
            for var in [minutes_var, seconds_var]:
                var.trace_add("write", validate_time)

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
            default=10,
            icon="🔋",
            icon_padding=21 - 6 + 3,
            icon_paddingr=2 + 6,
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
            1,
            min_val=75,
            max_val=94,
            default=85,
            icon="⚡",
            icon_padding=7 + 3,
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
            2,
            min_val=95,
            max_val=99,
            default=95,
            icon="⚠",
            icon_padding=8,
        )
        tooltip_text = "When battery reaches this percentage, the app will give urgent warnings to remove the charger"
        ToolTip(overflow_spinbox, tooltip_text, bootstyle="danger")
        ToolTip(overflow_label, tooltip_text, bootstyle="danger")
        ToolTip(overflow_icon_label, tooltip_text, bootstyle="danger")

        # Low battery interval (1:30 to 5:30)
        (
            self.low_interval_vars,
            low_interval_frame,
            low_interval_warning,
            low_interval_label,
            low_interval_icon_label,
        ) = create_time_interval_setting(
            app_settings_labelframe,
            "Low Battery",
            3,
            min_seconds=90,
            max_seconds=330,
            default_seconds=180,
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
            4,
            min_seconds=180,
            max_seconds=600,
            default_seconds=300,
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
            5,
            min_seconds=30,
            max_seconds=120,
            default_seconds=60,
            icon=None,
        )
        overflow_interval_tooltip = "How often to give urgent warnings when battery is at overflow level. Set between 0:30 and 2:00 minutes"
        ToolTip(overflow_interval_frame, overflow_interval_tooltip, bootstyle="danger")
        ToolTip(overflow_interval_label, overflow_interval_tooltip, bootstyle="danger")

    def create_battery_health_widgets(self, frame: ttk.Frame) -> None:
        """Create battery health monitoring widgets.

        Args:
            frame: The parent frame for the battery health widgets
        """
        self._create_top_details(frame)
        self._create_bottom_details(frame)

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

        data = BackgroundProcessManager().get_battery_data()

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

        data = BackgroundProcessManager().get_battery_data()

        # Create meter
        self.meter = ttk.Meter(
            self.bottom_frame,
            metersize=self.METER_SIZE,
            padding=10,
            amountused=data["capacity"].value,
            amounttotal=100,
            metertype="full",
            arcrange=self.METER_ARC_RANGE,
            textright="%",
            subtext="Battery Health",
            bootstyle=DEFAULT,
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
        data = BackgroundProcessManager().get_battery_data()

        # Update meter
        self.meter.configure(amountused=data["capacity"].value)

        # Update energy labels
        self.energy_full_value_label.configure(text=data["energy_full"])
        self.energy_original_full_value_label.configure(text=data["energy_full_design"])

        # Update detail labels
        self.battery_detail_labels["voltage"].configure(text=data["voltage"])
        self.battery_detail_labels["temperature"].configure(text=data["temperature"])


def main():
    """Main entry point for the application."""
    root = ttk.Window(
        title="Biryani (Battery Reminder)", themename="litera", size=(650, 550)
    )
    app = AppSettingUI(root)
    root.mainloop()
