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
from battery_reminder.src.logger_config import logger
from battery_reminder.src import powerplan
