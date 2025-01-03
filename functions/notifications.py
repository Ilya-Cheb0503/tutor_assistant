import json
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from constants.constants import *
from pwd_generator import get_current_directory
from project_config.wrapper import exception_handler
from project_config.settings import *

# Инициализация планировщика
scheduler = AsyncIOScheduler()

# Функция для загрузки уведомлений из файла

@exception_handler
async def load_notifications():
    logging.info("Загрузка уведомлений из файла.")
    
    project_folder = await get_current_directory()
    notifications_path = project_folder + NOTIFICATIONS_FILE
    
    if os.path.exists(notifications_path):
        with open(notifications_path, 'r') as file:
            notifications = json.load(file)
            logging.info("Уведомления успешно загружены.")
            return notifications
    
    logging.warning("Файл уведомлений не найден, возвращается пустой словарь.")
    return {}

@exception_handler
async def save_notifications(notifications):
    logging.info("Сохранение уведомлений в файл.")
    
    project_folder = await get_current_directory()
    notifications_path = project_folder + NOTIFICATIONS_FILE
    
    with open(notifications_path, 'w') as file:
        json.dump(notifications, file, ensure_ascii=True, indent=4)
    
    logging.info("Уведомления успешно сохранены.")