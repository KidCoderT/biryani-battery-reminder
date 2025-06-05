import tkinter as tk
from typing import Literal
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.icons import Emoji

from battery_reminder.src.background_proc import BackgroundProcessManager


class AppSettingUI:
    LIGHT_THEME = "litera"
    DARK_THEME = "darkly"

    def __init__(self, main_window: ttk.Window) -> None:
        self.master = main_window

        self.master.geometry("820x900")
        self.master.resizable(False, False)

        self.theme: Literal["light", "dark"] = "light"
        self.master.style.theme_use(self.LIGHT_THEME)

        self.style = ttk.Style()
        self.style.configure(
            "CustomLight.TButton", background="#ffffff", foreground="#222222"
        )
        self.style.configure(
            "CustomDark.TButton", background="#222222", foreground="#ffffff"
        )

        self.main_frame = ttk.Frame(
            self.master,
            padding=(25, 25),
        )
        self.main_frame.pack(fill=BOTH, expand=YES)

        header_frame = ttk.Frame(self.main_frame, padding=(10, 10))
        header_frame.pack(fill=X)

        app_title_label = ttk.Label(
            header_frame,
            text="Biryani (Battery Reminder)",
            font=("Arial", 16, "bold"),
        )
        app_title_label.pack(
            side=LEFT, padx=(0, 10), expand=True, fill=X
        )  # Allow title to expand

        self.icons = {
            "light": "🌞",  # Emoji.get("FULL MOON SYMBOL").char,
            "dark": "🌙",  # Emoji.get("BLACK SUN WITH RAYS").char,
        }

        self.theme_button = ttk.Button(
            header_frame,
            text=self.icons[self.theme],
            style="CustomDark.TButton",
            command=self.toggle_theme,
            padding=(10, 10),
        )
        self.theme_button.pack(side=RIGHT, padx=(0, 5))

        self.separator = ttk.Separator(self.main_frame, orient="horizontal")
        self.separator.pack(fill="x", pady=20)

        self.style.configure("custom.TNotebook", tabposition="n")
        self.style.configure(
            "custom.TNotebook.Tab", padding=(0, 25), font=("Arial", 10)
        )

        self.notebook = ttk.Notebook(self.main_frame, style="custom.TNotebook")

        self.battery_health_tab = ttk.Frame(self.notebook, padding=(20, 20))
        self.create_battery_health_widgets(self.battery_health_tab)
        self.notebook.add(self.battery_health_tab, text="Battery Health".center(60))

        self.app_settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.app_settings_tab, text="App Settings".center(60))

        self.notebook.pack(fill="both", expand=True)

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        # Switch theme
        self.master.style.theme_use(
            self.LIGHT_THEME if self.theme == "light" else self.DARK_THEME
        )
        # Re-apply custom styles after theme change
        self.style.configure(
            "CustomLight.TButton", background="#ffffff", foreground="#222222"
        )
        self.style.configure(
            "CustomDark.TButton", background="#222222", foreground="#ffffff"
        )
        # Use the correct style for the current theme
        style = "CustomDark.TButton" if self.theme == "light" else "CustomLight.TButton"
        self.theme_button.config(text=self.icons[self.theme], style=style)

    def create_battery_health_widgets(self, frame: ttk.Frame):
        top_details_frame = ttk.Frame(frame)
        top_details_frame.pack(fill=X, pady=(0, 30))

        # Use grid for left and right details frames
        left_details = ttk.Frame(top_details_frame)
        right_details = ttk.Frame(top_details_frame)

        left_details.grid(
            row=0, column=0, sticky="nsew", padx=(0, 30)
        )  # Add horizontal spacing between columns
        right_details.grid(row=0, column=1, sticky="nsew", padx=(30, 0))

        # Make both columns expand equally
        top_details_frame.grid_columnconfigure(0, weight=1)
        top_details_frame.grid_columnconfigure(1, weight=1)

        # Configure the detail frames' columns
        for details_frame in (left_details, right_details):
            details_frame.grid_columnconfigure(0, weight=0)
            details_frame.grid_columnconfigure(1, weight=1)

        details_data = [
            (left_details, "Vendor:", "N/A"),
            (left_details, "Model:", "N/A"),
            (left_details, "Temperature:", "N/A"),
            (right_details, "Technology:", "N/A"),
            (right_details, "Voltage:", "N/A"),
            (right_details, "Energy Rate:", "N/A"),
        ]

        self.battery_detail_labels = {}
        for i, (parent_frame, text, val_text) in enumerate(details_data):
            row_idx = i % 3
            ttk.Label(parent_frame, text=text).grid(
                row=row_idx,
                column=0,
                sticky=W,
                padx=10,
                pady=8,  # More horizontal and vertical padding
            )
            value_label = ttk.Label(parent_frame, text=val_text, width=20, anchor=E)
            value_label.grid(
                row=row_idx, column=1, sticky=E, padx=10, pady=8
            )  # More padding
            self.battery_detail_labels[
                text.replace(":", "").replace(" ", "_").lower()
            ] = value_label

        self.bottom_frame = ttk.Frame(frame)
        self.bottom_frame.pack(fill="both", expand=YES)

        # Configure column and row weights to allow content to center
        # We need more control over the grid
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.rowconfigure(0, weight=1)  # For the meter
        self.bottom_frame.rowconfigure(1, weight=1)  # For the energy details

        # Add additional empty rows/columns for centering if needed
        # Or, we can use sticky="nsew" and rely on row/column weights
        # combined with appropriate padding to push content to the center.

        # Meter
        meter = ttk.Meter(
            self.bottom_frame,
            metersize=180,
            padding=10,
            amountused=96,
            amounttotal=100,
            metertype="full",
            arcrange=360,
            textright="%",
            subtext="Battery Health",
        )
        # Adjust pady for meter: remove or reduce bottom padding
        # Let's try (20, 0) to remove padding at the bottom of the meter
        meter.grid(row=0, column=0, pady=(20, 0), sticky="nsew")

        # Energy Details Frame
        energy_details_frame = ttk.Frame(self.bottom_frame)
        # Adjust pady for energy_details_frame: remove or reduce top padding
        # Let's try (0, 20) to remove padding at the top of the energy details frame
        energy_details_frame.grid(row=1, column=0, pady=(0, 20), sticky="nsew")

        # Create a sub-frame to hold the labels for horizontal centering
        label_container_frame = ttk.Frame(energy_details_frame)
        label_container_frame.pack(expand=YES, anchor="center")  # Center this sub-frame

        ttk.Label(label_container_frame, text="Energy Full:").pack(side=LEFT, padx=5)
        self.energy_full_value_label = ttk.Label(label_container_frame, text="N/A")
        self.energy_full_value_label.pack(side=LEFT, padx=5)
        ttk.Label(label_container_frame, text="Energy Original Full:").pack(
            side=LEFT, padx=20
        )
        self.energy_original_full_value_label = ttk.Label(
            label_container_frame, text="N/A"
        )
        self.energy_original_full_value_label.pack(side=LEFT, padx=5)


def main():
    app = BackgroundProcessManager()
    print(app.battery.as_dict())
    root = ttk.Window(
        title="Biryani (Battery Reminder)", themename="litera", size=(650, 550)
    )  # Adjusted height for bottom buttons
    app = AppSettingUI(root)
    root.mainloop()
