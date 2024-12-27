import json
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from constants.constants import *
from pwd_generator import get_current_directory

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# Функция для загрузки уведомлений из файла
async def load_notifications():
    project_folder = await get_current_directory()
    notifications_path = project_folder+NOTIFICATIONS_FILE
    if os.path.exists(notifications_path):
        with open(notifications_path, 'r') as file:
            return json.load(file)
    return {}

# Функция для сохранения уведомлений в файл
async def save_notifications(notifications):
    project_folder = await get_current_directory()
    notifications_path = project_folder+NOTIFICATIONS_FILE
    with open(notifications_path, 'w') as file:
        json.dump(notifications, file, ensure_ascii=True, indent=4)
