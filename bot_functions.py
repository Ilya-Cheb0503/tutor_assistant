import datetime
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

import pytz

TEACHER_ID = 5086356786
TEACHER_EMAIL = 'rinigudini@gmail.com'

months_translation = {
    "January": "Января",
    "February": "Февраля",
    "March": "Марта",
    "April": "Апреля",
    "May": "Мая",
    "June": "Июня",
    "July": "Июля",
    "August": "Августа",
    "September": "Сентября",
    "October": "Октября",
    "November": "Ноября",
    "December": "Декабря"
}


# Путь к вашему файлу credentials.json
CREDENTIALS_FILE = r'C:\dev_py\chemical_tutor\calendar_project\project\chemical-tutor-ec8a32045bb2.json'
# ID вашего календаря (можно использовать 'primary' для основного календаря)
# CALENDAR_ID = 'cheb.ilya05@yandex.ru'
CALENDAR_ID = TEACHER_EMAIL

# Попытка получить события из календаря
async def get_kids_lessons(time_period, user_name):
    try:
        credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
        service = build('calendar', 'v3', credentials=credentials)

        # Устанавливаем временные рамки для запроса (текущая дата и дата через 7 дней)
        now = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).isoformat() + 'Z'  # Текущая дата и время в формате UTC+3
        week_later = (datetime.datetime.utcnow() + datetime.timedelta(days=time_period, hours=3)).isoformat() + 'Z'
        logging.info(f'ВРЕМЯ {now}')
        # Получаем события только на неделю вперед
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            timeMax=week_later,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return None, 0
        else:
            events_list = []
            events_count = 0
            for event in events:

                event_description = event['description']
                logging.info(f'user_name = {user_name} and descr = {event_description}')
                
                if user_name in event_description:
                    kid_name = event['description'].split(',')[1]                    
                    
                    
                    start_time = event['start']['dateTime']
                    end_time = event['end']['dateTime']

                    start_correct_time = await time_get(start_time)
                    end_correct_time = await time_get(end_time)
                    
                    full_inf = [start_correct_time, end_correct_time, kid_name]

                    events_list.append(full_inf)
                    events_count += 1

        return events_list, events_count


    except Exception as e:
        print(f'Ошибка доступа: {str(e)}')


# Попытка получить события из календаря
async def get_lessons_for_teacher(time_period, user_name):
    try:
        credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
        service = build('calendar', 'v3', credentials=credentials)

        # Устанавливаем временные рамки для запроса (текущая дата и дата через 7 дней)
        now = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).isoformat() + 'Z'  # Текущая дата и время в формате UTC+3
        week_later = (datetime.datetime.utcnow() + datetime.timedelta(days=time_period, hours=3)).isoformat() + 'Z'

        # Получаем события только на неделю вперед
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            timeMax=week_later,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return None, 0
        else:
            events_list = []
            events_count = 0
            for event in events:
                event_name = event['summary']

                if 'УРОК' in event_name:
                    kid_name = event_name.split('; ')[1]

                    start_time = event['start']['dateTime']
                    end_time = event['end']['dateTime']

                    start_correct_time = await time_get(start_time)
                    end_correct_time = await time_get(end_time)

                    full_inf = [start_correct_time, end_correct_time, kid_name]
                    # full_inf = await information_collector(event)
                    # full_inf.append(kid_name)
                    
                    events_list.append(full_inf)
                    events_count += 1
        return events_list, events_count


    except Exception as e:
        print(f'Ошибка доступа: {str(e)}')


async def test_f(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_inf = update.effective_user
    user_name = user_inf['username']

    kids_lessons_if, lessons_count = await get_kids_lessons(time_period=1, user_name=user_name)
    start_inf = kids_lessons_if[0]
    start_day = start_inf['day']
    start_hour = start_inf['hour']

    user_id = user_inf.id
    await context.bot.send_message(chat_id=user_id, text='test 10 seconds')


def get_current_hour_moscow():
    # Устанавливаем часовой пояс для Москвы
    moscow_tz = pytz.timezone('Europe/Moscow')
    
    # Получаем текущее время в московском часовом поясе
    moscow_time = datetime.now(moscow_tz)
    
    # Извлекаем текущий час
    current_hour = moscow_time.hour
    
    return current_hour


async def message_creator(start_event, end_event):
    start_day = start_event['day']
    start_month = start_event['month']
    start_hours = start_event['hours']
    start_minutes = start_event['minutes']

    end_hours = end_event['hours']
    end_minutes = end_event['minutes']

    day_start_inf = f'{start_day} {start_month}'
    event_start_inf = f'Начало занятия {day_start_inf} в {start_hours}:{start_minutes}'
    event_end_inf = f'И продлится оно до {end_hours}:{end_minutes}'
 
    
    

    return day_start_inf, event_start_inf, event_end_inf


async def time_get(time_dt_f):

                    
                    start_time_dt = datetime.datetime.fromisoformat(time_dt_f)

                    start_hours = start_time_dt.strftime("%H")
                    start_minutes = start_time_dt.strftime("%M")
                    
                    start_day = start_time_dt.strftime("%d")
                    if start_day[0].__eq__('0'):
                        start_day = start_day[1]

                    start_month = start_time_dt.strftime("%B")
                    start_years = start_time_dt.strftime("%Y")
                    start_month_rus = months_translation[start_month]
                    
                    # result_start_time = f'{start_hours}:{start_minutes} {start_day} {start_month_rus} {start_years} года.'
                    # result_start_time = f'{start_hours}:{start_minutes} {start_day} {start_month_rus}.'
                    
                    inf = {
                         'hours': start_hours,
                         'minutes': start_minutes,
                         'day': start_day,
                         'month': start_month_rus,
                    }
                    return inf


async def parse_date(date_str):
    months = {
        'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
        'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
        'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
    }
    
    # Разделяем дату и время
    date_part, time_part = date_str.split(', ')
    day, month_name = date_part.split()
    month = months[month_name]
    
    # Формируем строку в формате ISO 8601
    return f"2024-{month}-{int(day):02d}T{time_part}:00"
