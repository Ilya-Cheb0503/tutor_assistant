import asyncio
import json
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Имя файла для хранения уведомлений
NOTIFICATIONS_FILE = 'notifications.json'

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# Функция для загрузки уведомлений из файла
async def load_notifications():
    if os.path.exists(NOTIFICATIONS_FILE):
        with open(NOTIFICATIONS_FILE, 'r') as file:
            return json.load(file)
    return {}

# Функция для сохранения уведомлений в файл
async def save_notifications(notifications):
    with open(NOTIFICATIONS_FILE, 'w') as file:
        json.dump(notifications, file)
