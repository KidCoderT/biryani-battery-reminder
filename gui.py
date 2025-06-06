import tkinter as tk
from tkinter import font as tkFont
from typing import Literal
import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class BatteryReminderApp:
    def __init__(self, master):
        self.master = master
        master.geometry("800x700")
        master.resizable(False, False)

        # --- Theme Initialization ---
        self.light_theme_name = "litera"  # Default light theme
        self.dark_theme_name = "superhero"  # Default dark theme
        self.master.style.theme_use(self.light_theme_name)

        # Configure custom font (can still be used if needed)
        # default_font.configure(size=10)
        # default_font = tkFont.nametofont("TkDefaultFont")

        # --- Header Frame ---
        header_frame = ttk.Frame(master, padding=(10, 10))
        header_frame.pack(fill=X)

        app_title_label = ttk.Label(
            header_frame, text="Biryani (Battery Reminder)", font=("Arial", 16, "bold")
        )
        app_title_label.pack(
            side=LEFT, padx=(0, 10), expand=True, fill=X
        )  # Allow title to expand

        self.theme: Literal["light", "dark"] = "light"
        self.theme_button = ttk.Button(
            header_frame,
            text=f"{self.theme.capitalize()} Theme",
            style="Outline.TButton",
            command=self.set_theme,
        )
        self.theme_button.pack(side=RIGHT, padx=(0, 5))

        # self.light_theme_button = ttk.Button(
        #     header_frame,
        #     text="Light Theme",
        #     style="Outline.TButton",
        #     command=self.set_light_theme,
        # )
        # self.light_theme_button.pack(side=RIGHT, padx=(0, 5))

        # --- Validation Commands ---
        self.vcmd_2digit = (master.register(self.validate_2digit_input), "%P")
        self.vcmd_percent = (master.register(self.validate_percent_input), "%P")

        # --- Tab Control ---
        self.notebook = ttk.Notebook(master)

        # --- App Settings Tab ---
        self.app_settings_tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(self.app_settings_tab, text="App Settings")
        self.create_app_settings_widgets()

        # --- Battery Health Tab ---
        self.battery_health_tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(self.battery_health_tab, text="Battery Health")
        self.create_battery_health_widgets()

        self.notebook.pack(expand=True, fill=BOTH, padx=10, pady=(0, 10))

        # --- Bottom Buttons Frame (Save/Reset) ---
        bottom_buttons_frame = ttk.Frame(master, padding=(10, 10))
        bottom_buttons_frame.pack(fill=X, side=BOTTOM)

        self.reset_button = ttk.Button(
            bottom_buttons_frame,
            text="Reset Settings",
            command=self.reset_settings,
            bootstyle="danger-outline",
        )
        self.reset_button.pack(side=RIGHT, padx=(0, 5))

        self.save_button = ttk.Button(
            bottom_buttons_frame,
            text="Save Settings",
            command=self.save_settings,
            bootstyle="success",
        )
        self.save_button.pack(side=RIGHT, padx=5)

    def set_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.master.style.theme_use(
            self.light_theme_name if self.theme == "light" else self.dark_theme_name
        )
        self.theme_button.config(text=f"{self.theme.capitalize()} Theme")
        self.update_canvas_theme()
        print(
            f"Switched to {self.light_theme_name if self.theme == 'light' else self.dark_theme_name} theme"
        )

    # def set_light_theme(self):
    #     self.master.style.theme_use(self.light_theme_name)
    #     self.update_canvas_theme()
    #     print(f"Switched to {self.light_theme_name} theme")

    # def set_dark_theme(self):
    #     self.master.style.theme_use(self.dark_theme_name)
    #     self.update_canvas_theme()
    #     print(f"Switched to {self.dark_theme_name} theme")

    def update_canvas_theme(self):
        if hasattr(self, "progress_canvas"):
            bg_color = self.master.style.colors.get("bg")
            self.progress_canvas.configure(bg=bg_color)
            text_color = self.master.style.colors.get("fg")
            self.progress_canvas.itemconfigure(self.percentage_text, fill=text_color)
            outline_color = (
                self.master.style.colors.get("primary")
                if self.master.style.theme.name != self.dark_theme_name
                else self.master.style.colors.get("selectfg")
            )
            self.progress_canvas.itemconfigure(
                self.circle_outline, outline=outline_color
            )

    def validate_2digit_input(self, P):
        if P == "":
            return True  # Allow empty temporarily for better UX
        if not P.isdigit():
            return False
        if len(P) > 2:
            return False
        num = int(P)
        return num <= 59  # Max value for minutes/seconds

    def validate_percent_input(self, P):
        if P == "":
            return True  # Allow empty temporarily for better UX
        if not P.isdigit():
            return False
        if len(P) > 3:
            return False
        num = int(P)
        return num <= 100

    def format_and_validate_entry(self, event, max_val=59):
        widget = event.widget
        content = widget.get()

        # Handle empty content
        if content == "":
            widget.delete(0, END)
            widget.insert(0, "00")
            return

        # Handle non-digit content
        if not content.isdigit():
            valid_part = "".join(filter(str.isdigit, content))
            if not valid_part:
                valid_part = "00"
            content = valid_part

        # Convert to number and validate range
        num = int(content)
        if num > max_val:
            num = max_val
        content = str(num)

        # Format with leading zero
        if len(content) == 1:
            content = f"0{content}"

        # Update widget if content changed
        if widget.get() != content:
            widget.delete(0, END)
            widget.insert(0, content)

    def create_app_settings_widgets(self):
        frame = self.app_settings_tab
        frame.grid_columnconfigure(0, weight=0)  # Label column
        frame.grid_columnconfigure(1, weight=1)  # Spacer column

        # --- Row 0: Run on Startup ---
        run_on_startup_label = ttk.Label(frame, text="Run on Startup:")
        run_on_startup_label.grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.run_on_startup_var = tk.BooleanVar(value=False)
        run_on_startup_check = ttk.Checkbutton(
            frame, variable=self.run_on_startup_var, bootstyle="success-square-toggle"
        )
        run_on_startup_check.grid(
            row=0, column=2, columnspan=6, sticky=E, padx=5, pady=5
        )

        # --- Row 1: Low Battery Reminder ---
        low_battery_label = ttk.Label(frame, text="Low Battery Reminder:")
        low_battery_label.grid(row=1, column=0, sticky=W, padx=5, pady=5)

        percent_input_frame1 = ttk.Frame(frame)
        percent_input_frame1.grid(
            row=1, column=2, columnspan=6, sticky=E, padx=5, pady=5
        )
        self.low_battery_entry = ttk.Entry(
            percent_input_frame1,
            width=4,
            validate="key",
            validatecommand=self.vcmd_percent,
        )
        self.low_battery_entry.insert(0, "20")  # Default value
        self.low_battery_entry.pack(side=LEFT)
        self.low_battery_entry.bind(
            "<FocusOut>", lambda e: self.format_and_validate_entry(e, max_val=100)
        )
        self.low_battery_entry.bind(
            "<FocusIn>", lambda e: self.low_battery_entry.select_range(0, END)
        )
        ttk.Label(percent_input_frame1, text="%").pack(side=LEFT, padx=(2, 0))

        # --- Row 2: Low Battery Reminder Repeat Interval ---
        low_repeat_label = ttk.Label(
            frame, text="Low Battery Reminder Repeat Interval:"
        )
        low_repeat_label.grid(row=2, column=0, sticky=W, padx=5, pady=5)

        hms_input_frame1 = ttk.Frame(frame)
        hms_input_frame1.grid(row=2, column=2, columnspan=6, sticky=E, padx=5, pady=5)

        # Minutes
        self.low_repeat_m_entry = ttk.Entry(
            hms_input_frame1, width=3, validate="key", validatecommand=self.vcmd_2digit
        )
        self.low_repeat_m_entry.insert(0, "05")
        self.low_repeat_m_entry.pack(side=LEFT)
        self.low_repeat_m_entry.bind(
            "<FocusOut>", lambda e: self.format_and_validate_entry(e, max_val=59)
        )
        self.low_repeat_m_entry.bind(
            "<FocusIn>", lambda e: self.low_repeat_m_entry.select_range(0, END)
        )
        ttk.Label(hms_input_frame1, text="m").pack(side=LEFT, padx=(2, 5))

        # Seconds
        self.low_repeat_s_entry = ttk.Entry(
            hms_input_frame1, width=3, validate="key", validatecommand=self.vcmd_2digit
        )
        self.low_repeat_s_entry.insert(0, "00")
        self.low_repeat_s_entry.pack(side=LEFT)
        self.low_repeat_s_entry.bind(
            "<FocusOut>", lambda e: self.format_and_validate_entry(e, max_val=59)
        )
        self.low_repeat_s_entry.bind(
            "<FocusIn>", lambda e: self.low_repeat_s_entry.select_range(0, END)
        )
        ttk.Label(hms_input_frame1, text="s").pack(side=LEFT, padx=(2, 0))

        # --- Row 3: High Battery Reminder ---
        high_battery_label = ttk.Label(frame, text="High Battery Reminder:")
        high_battery_label.grid(row=3, column=0, sticky=W, padx=5, pady=(15, 5))

        percent_input_frame2 = ttk.Frame(frame)
        percent_input_frame2.grid(
            row=3, column=2, columnspan=6, sticky=E, padx=5, pady=(15, 5)
        )
        self.high_battery_entry = ttk.Entry(
            percent_input_frame2,
            width=4,
            validate="key",
            validatecommand=self.vcmd_percent,
        )
        self.high_battery_entry.insert(0, "80")  # Default value
        self.high_battery_entry.pack(side=LEFT)
        self.high_battery_entry.bind(
            "<FocusOut>", lambda e: self.format_and_validate_entry(e, max_val=100)
        )
        self.high_battery_entry.bind(
            "<FocusIn>", lambda e: self.high_battery_entry.select_range(0, END)
        )
        ttk.Label(percent_input_frame2, text="%").pack(side=LEFT, padx=(2, 0))

        # --- Row 4: High Battery Reminder Repeat Interval ---
        high_repeat_label = ttk.Label(
            frame, text="High Battery Reminder Repeat Interval:"
        )
        high_repeat_label.grid(row=4, column=0, sticky=W, padx=5, pady=5)

        hms_input_frame2 = ttk.Frame(frame)
        hms_input_frame2.grid(row=4, column=2, columnspan=6, sticky=E, padx=5, pady=5)

        # Minutes
        self.high_repeat_m_entry = ttk.Entry(
            hms_input_frame2, width=3, validate="key", validatecommand=self.vcmd_2digit
        )
        self.high_repeat_m_entry.insert(0, "05")
        self.high_repeat_m_entry.pack(side=LEFT)
        self.high_repeat_m_entry.bind(
            "<FocusOut>", lambda e: self.format_and_validate_entry(e, max_val=59)
        )
        self.high_repeat_m_entry.bind(
            "<FocusIn>", lambda e: self.high_repeat_m_entry.select_range(0, END)
        )
        ttk.Label(hms_input_frame2, text="m").pack(side=LEFT, padx=(2, 5))

        # Seconds
        self.high_repeat_s_entry = ttk.Entry(
            hms_input_frame2, width=3, validate="key", validatecommand=self.vcmd_2digit
        )
        self.high_repeat_s_entry.insert(0, "00")
        self.high_repeat_s_entry.pack(side=LEFT)
        self.high_repeat_s_entry.bind(
            "<FocusOut>", lambda e: self.format_and_validate_entry(e, max_val=59)
        )
        self.high_repeat_s_entry.bind(
            "<FocusIn>", lambda e: self.high_repeat_s_entry.select_range(0, END)
        )
        ttk.Label(hms_input_frame2, text="s").pack(side=LEFT, padx=(2, 0))

        # --- Row 5: Overflow ---
        overflow_label = ttk.Label(frame, text="Overflow:")
        overflow_label.grid(row=5, column=0, sticky=W, padx=5, pady=(15, 5))

        percent_input_frame3 = ttk.Frame(frame)
        percent_input_frame3.grid(
            row=5, column=2, columnspan=6, sticky=E, padx=5, pady=(15, 5)
        )
        self.overflow_entry = ttk.Entry(
            percent_input_frame3,
            width=4,
            validate="key",
            validatecommand=self.vcmd_percent,
        )
        self.overflow_entry.insert(0, "05")  # Default value
        self.overflow_entry.pack(side=LEFT)
        self.overflow_entry.bind(
            "<FocusOut>", lambda e: self.format_and_validate_entry(e, max_val=100)
        )
        self.overflow_entry.bind(
            "<FocusIn>", lambda e: self.overflow_entry.select_range(0, END)
        )
        ttk.Label(percent_input_frame3, text="%").pack(side=LEFT, padx=(2, 0))

    def save_settings(self):
        settings = {
            "run_on_startup": self.run_on_startup_var.get(),
            "low_battery_level": self.low_battery_entry.get(),
            "low_repeat_h": self.low_repeat_h_entry.get(),
            "low_repeat_m": self.low_repeat_m_entry.get(),
            "low_repeat_s": self.low_repeat_s_entry.get(),
            "high_battery_level": self.high_battery_entry.get(),
            "high_repeat_h": self.high_repeat_h_entry.get(),
            "high_repeat_m": self.high_repeat_m_entry.get(),
            "high_repeat_s": self.high_repeat_s_entry.get(),
            "overflow": self.overflow_entry.get(),
        }
        print("Saving settings:", settings)
        try:
            from ttkbootstrap.dialogs import Messagebox

            Messagebox.ok(
                "Settings Saved Successfully! (Placeholder)", title="Save Settings"
            )
        except ImportError:
            print("ttkbootstrap.dialogs.Messagebox not available for confirmation.")

    def reset_settings(self):
        self.run_on_startup_var.set(False)
        default_values = {
            self.low_battery_entry: ("20", 100),
            self.high_battery_entry: ("80", 100),
            self.overflow_entry: ("05", 100),
            self.low_repeat_h_entry: ("00", 23),
            self.low_repeat_m_entry: ("05", 59),
            self.low_repeat_s_entry: ("00", 59),
            self.high_repeat_h_entry: ("00", 23),
            self.high_repeat_m_entry: ("05", 59),
            self.high_repeat_s_entry: ("00", 59),
        }
        for entry_widget, (default_val, max_v) in default_values.items():
            entry_widget.delete(0, END)
            entry_widget.insert(0, default_val)

            class DummyEvent:
                def __init__(self, widget):
                    self.widget = widget

            self.format_and_validate_entry(DummyEvent(entry_widget), max_val=max_v)
        print("Settings reset to defaults.")
        try:
            from ttkbootstrap.dialogs import Messagebox

            Messagebox.ok(
                "Settings have been reset to defaults. (Placeholder)",
                title="Reset Settings",
            )
        except ImportError:
            print("ttkbootstrap.dialogs.Messagebox not available for confirmation.")

    def create_battery_health_widgets(self):
        frame = self.battery_health_tab
        top_details_frame = ttk.Frame(frame)
        top_details_frame.pack(fill=X, pady=(0, 20))

        left_details = ttk.Frame(top_details_frame)
        left_details.pack(side=LEFT, fill=X, expand=True, padx=(0, 10))
        right_details = ttk.Frame(top_details_frame)
        right_details.pack(side=LEFT, fill=X, expand=True, padx=(10, 0))

        details_data = [
            (left_details, "Vendor:", "N/A"),
            (left_details, "Model:", "N/A"),
            (left_details, "Serial Number:", "N/A"),
            (right_details, "Technology:", "N/A"),
            (right_details, "Voltage:", "N/A"),
            (right_details, "Energy Rate:", "N/A"),
        ]

        self.battery_detail_labels = {}
        for i, (parent_frame, text, val_text) in enumerate(details_data):
            row_idx = i % 3
            ttk.Label(parent_frame, text=text).grid(
                row=row_idx, column=0, sticky=W, padx=5, pady=2
            )
            value_label = ttk.Label(
                parent_frame, text=val_text, width=20, anchor=W
            )  # Store labels if they need updating
            value_label.grid(row=row_idx, column=1, sticky=W, padx=5, pady=2)
            self.battery_detail_labels[
                text.replace(":", "").replace(" ", "_").lower()
            ] = value_label

        circle_canvas_frame = ttk.Frame(frame)
        circle_canvas_frame.pack(pady=(10, 10))
        canvas_bg = self.master.style.colors.get("bg")
        self.progress_canvas = tk.Canvas(
            circle_canvas_frame,
            width=150,
            height=150,
            bg=canvas_bg,
            highlightthickness=0,
        )
        self.progress_canvas.pack()
        initial_outline_color = self.master.style.colors.get("primary")
        initial_text_color = self.master.style.colors.get("fg")
        self.circle_outline = self.progress_canvas.create_oval(
            10, 10, 140, 140, outline=initial_outline_color, width=4
        )
        self.percentage_text = self.progress_canvas.create_text(
            75, 75, text="96%", font=("Helvetica", 24, "bold"), fill=initial_text_color
        )

        energy_details_frame = ttk.Frame(frame)
        energy_details_frame.pack(pady=(10, 5))
        ttk.Label(energy_details_frame, text="Energy Full:").pack(side=LEFT, padx=5)
        self.energy_full_value_label = ttk.Label(energy_details_frame, text="N/A")
        self.energy_full_value_label.pack(side=LEFT, padx=5)
        ttk.Label(energy_details_frame, text="Energy Original Full:").pack(
            side=LEFT, padx=20
        )
        self.energy_original_full_value_label = ttk.Label(
            energy_details_frame, text="N/A"
        )
        self.energy_original_full_value_label.pack(side=LEFT, padx=5)

        self.update_canvas_theme()


if __name__ == "__main__":
    root = ttk.Window(
        title="Biryani (Battery Reminder)", themename="litera", size=(650, 550)
    )  # Adjusted height for bottom buttons
    app = BatteryReminderApp(root)
    root.mainloop()
