from battery_reminder.src.settings_gui import AppSettingUI
from battery_reminder.src.app_config_manager import (
    load_config,
    get_app_name,
    is_first_run,
)
from battery_reminder.src.assets_manager import app_icon
from battery_reminder.src.notifier import Notifier
from battery_reminder.src.background_proc import (
    run_background_process,
    BackgroundProcessManager,
)
from battery_reminder.src.startup_manager import (
    add_to_startup,
    remove_from_startup,
    is_in_startup,
)
from battery_reminder.src.logger_config import setup_logger
from battery_reminder.src import powerplan
