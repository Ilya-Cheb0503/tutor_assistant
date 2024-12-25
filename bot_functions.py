import datetime
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from functools import partial

import pytz

from settings import *
from bd_functions import *
from notifications import *

from constants import *

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


async def hi_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    keyboard = [
        [InlineKeyboardButton('Ближайшее занятие', callback_data='near_lesson')],
    ]

    # Создаем разметку для кнопок
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем сообщение с инлайн кнопками

    second_message = 'Чтобы узнать дату ближайшего занятия, нажми на кнопку ниже'
    await update.message.reply_text(second_message, reply_markup=reply_markup)

# Попытка получить события из календаря
async def get_kids_lessons(time_period, student_tg_id):
    try:
        credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)
        service = build('calendar', 'v3', credentials=credentials)

        # Устанавливаем временные рамки для запроса (текущая дата и дата через 7 дней)
        now = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).isoformat() + '+03:00'  # Текущая дата и время в формате UTC+3
        week_later = (datetime.datetime.utcnow() + datetime.timedelta(days=time_period, hours=3)).isoformat() + '+03:00'
        # logging.info(f'ВРЕМЯ {now}')
        # Получаем события только на неделю вперед
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            timeMax=week_later,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        student = await get_student(student_tg_id)
        # logging.info(f'STUDENT {student}')
        first_name = student[1]
        last_name = student[2]

        if not events:
            return (None, 0)
        else:
            events_list = []
            events_count = 0
            for event in events:
                event_name = event['summary']
                # logging.info(f'event = {event_name}')

                if 'УРОК' in event_name and (first_name and last_name) in event_name:
                    kid_name = event_name.split('; ')[1]
                    
                    logging.info(f'kid_name {kid_name}')
                    
                    start_time = event['start']['dateTime']
                    end_time = event['end']['dateTime']

                    start_correct_time = await time_get(start_time)
                    end_correct_time = await time_get(end_time)
                    
                    full_inf = [start_correct_time, end_correct_time, kid_name]

                    events_list.append(full_inf)
                    events_count += 1
        logging.info(f'RETURN {events_list} {events_count}')
        return [events_list, events_count]


    except Exception as e:
        logging.error(f'ошибка {e}')


async def notifications_process(update: Update, context: ContextTypes.DEFAULT_TYPE, notifications_json, student_tg_id):
    kids_lessons_if, lessons_count = await get_kids_lessons(time_period=1, student_tg_id=student_tg_id)
    if lessons_count.__eq__(0):
        pass
    else:
        day, hours, minutes = await get_current_time_formatted()
        user_id_str = str(student_tg_id)
        
        if user_id_str not in notifications_json:
            logging.info(f'Хуйня какая-то: {notifications_json},\n{student_tg_id},\n{student_tg_id not in notifications_json}')
            notifications_json[user_id_str] = {
                'warning_day_message': None,
                'warning_hour_message': None
            }
            
        warnings = notifications_json[user_id_str]
        warning_hour_message = warnings['warning_hour_message']
        warning_day_message = warnings['warning_day_message']

        start_inf = kids_lessons_if[0][0]
        logging.info(f'DAY {start_inf}')
        start_day = int(start_inf['day'])
        
        start_hour_text = start_inf['hours']
        start_hour = int(start_hour_text)
        start_minutes_text = start_inf['minutes']
        start_minutes = int(start_minutes_text)

        time_lesson = f'{start_day}{start_hour}'

        day_check = time_lesson.__ne__(warning_day_message)
        hour_check = time_lesson.__ne__(warning_hour_message)

        if start_day-day == 1:
            logging.info('ПРОВЕРКА ДНЯ')
            if (24-hours) + start_hour <= 24 and day_check:
                logging.info('ПРОВЕУРКА ДНЯ 222')
                logging.info('one day')
                hours_delta = (24-hours) + start_hour
                if start_minutes > minutes:
                    minutes_delta = start_minutes-minutes
                elif start_minutes < minutes:
                    hours_delta -= 1
                    minutes_delta = (60 - minutes) + start_minutes
                else:
                    minutes_delta = 0

                warning_text = (
                f'❗️ НАПОМИНАЮ ❗\n\n'
                f'У тебя завтра занятие с преподавателем по Химии.\n'
                f'Начало в {start_hour_text}:{start_minutes_text}.\n'
                f'То есть, через {hours_delta} часов и {minutes_delta} минут\n\n'
                'Если ты ещё не выполнил ДЗ, то также напоминаю о его выполнении.'
                )
                await context.bot.send_message(chat_id=student_tg_id, text=warning_text)
                notifications_json[user_id_str]['warning_day_message'] = f'{start_day}{start_hour}' 
        
        elif start_day-day == 0:
            logging.info('ПРОВЕРКА СЕГОДНЯ')

            if (start_hour - hours) <= 24 and day_check:
                logging.info('ПРОВЕРКА СЕГОДНЯ СРАБОТАЛА')
                hours_delta = start_hour - hours
                if start_minutes > minutes:
                    minutes_delta = start_minutes-minutes
                elif start_minutes < minutes:
                    hours_delta -= 1
                    minutes_delta = (60 - minutes) + start_minutes
                else:
                    minutes_delta = 0
                logging.info(f'через {hours_delta} часов и {minutes_delta}')
                warning_text = (
                f'❗️ НАПОМИНАЮ ❗\n\n'
                f'У тебя скоро занятие с преподавателем по Химии.\n'
                f'Начало в {start_hour_text}:{start_minutes_text}.\n'
                f'То есть, через {hours_delta} часов и {minutes_delta} минут\n\n'
                'Если ты ещё не выполнил ДЗ, то также напоминаю о его выполнении.'
                )
                await context.bot.send_message(chat_id=student_tg_id, text=warning_text)
                notifications_json[user_id_str]['warning_day_message'] = f'{start_day}{start_hour}' 

            logging.info('ПРОВЕРКА ЧАСА')
            if start_hour - hours == 0 and hour_check:
                logging.info('ПРОВЕРКА ЧАСА СРАБОТАЛА')
                minutes_delta = start_minutes-minutes
                warning_text = (
                f'❗❗ НАПОМИНАЮ ❗❗\n\n'
                f'У тебя скоро занятие с преподавателем по Химии.\n'
                f'Начало в {start_hour_text}:{start_minutes_text}.\n'
                f'То есть, через {minutes_delta}\n\n'
                'Если ты ещё не выполнил ДЗ, то также напоминаю о его выполнении.'
                )
                await context.bot.send_message(chat_id=student_tg_id, text=warning_text)
                notifications_json[user_id_str]['warning_hour_message'] = f'{start_day}{start_hour}' 

    await save_notifications(notifications_json)

async def test_f(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    students_id = await get_all_telegram_ids()

    logging.info('Проверка связи')
    
    notifications = await load_notifications()
    for student_tg_id in students_id:
        await notifications_process(update, context, notifications, student_tg_id)
        
    
    


async def get_current_time_formatted():
    # Получаем текущее время
    now = datetime.datetime.now()
    
    # Форматируем время в нужный формат
    day = int(now.strftime("%d"))
    hours = int(now.strftime("%H"))
    minutes = int(now.strftime("%M"))
    
    return day, hours, minutes


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
