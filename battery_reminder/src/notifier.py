import queue
import asyncio
from battery_reminder.src.app_config_manager import get_app_name
from desktop_notifier import DesktopNotifier, Icon, Urgency, Button
import multiprocessing

from battery_reminder.src.assets_manager import get_emoji
from battery_reminder.src.logger_config import logger

NOTIFICATION_LIMIT = 5


class Notifier:
    def __init__(
        self,
        notification_queue: multiprocessing.Queue,
        critical_notifications_queue: multiprocessing.Queue,
        app_name=get_app_name(),
    ):
        self.notifier = DesktopNotifier(
            app_name=app_name,
            notification_limit=NOTIFICATION_LIMIT,
        )
        self.urgent_notifications_queue = critical_notifications_queue
        self.notification_queue = notification_queue
        self.clear_notifications = multiprocessing.Event()
        self.clear_notifications.clear()
        self.notifications = []

    async def send_notification(self, notification):
        params = notification.copy()
        params["icon"] = Icon(get_emoji(params.pop("icon")))
        if "buttons" in params:
            params["buttons"] = [
                (
                    Button(
                        button[0],
                        lambda: print(button[1]),
                    )
                )
                for button in params.pop("buttons")
            ]
        notification = await self.notifier.send(**params)
        self.notifications.append(notification)
        return notification

    async def clear_all(self):
        await self.notifier.clear_all()
        self.notifications.clear()

    async def main(self):
        await self.clear_all()
        logger.info("Notifier started")

        while True:
            if self.clear_notifications.is_set():
                await self.clear_all()
                self.clear_notifications.clear()

            if self.urgent_notifications_queue.empty():
                try:
                    notification = self.notification_queue.get(block=False)
                    logger.debug(f"Notification received: {notification}")
                    await self.send_notification(notification)
                except queue.Empty:
                    pass
            else:
                notification = self.urgent_notifications_queue.get()
                logger.debug(f"Urgent notification received: {notification}")
                await self.send_notification(notification)

            if len(self.notifications) > 5:
                await self.notifier.clear(self.notifications[0])
                self.notifications.pop(0)

            await asyncio.sleep(0.1)

    def send_process_stopped_message(self):
        self.urgent_notifications_queue.put_nowait(
            dict(
                title="Process Stopped!",
                message="Be ware I will no longer remind you if you overcharge your battery!",
                icon="oh-no",
                urgency=Urgency.Critical,
                timeout=0,
            )
        )

        self.clear_notifications.set()
