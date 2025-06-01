import datetime
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from constants.constants import *
from functions.bd_functions import *
from functions.notifications import *
from project_config.settings import *
from pwd_generator import get_current_directory
from project_config.wrapper import exception_handler

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


@exception_handler
async def hi_again(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("Отправка приветственного сообщения пользователю.")
    
    keyboard = [
        [InlineKeyboardButton('Ближайшее занятие', callback_data='near_lesson')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    second_message = 'Чтобы узнать дату ближайшего занятия, нажми на кнопку ниже'
    
    await update.message.reply_text(second_message, reply_markup=reply_markup)
    logging.info("Приветственное сообщение успешно отправлено.")


@exception_handler
async def get_kids_lessons(time_period, student_tg_id):
    logging.info(f"Получение уроков для студента с tg_id: {student_tg_id} на период {time_period} дней.")
    
    project_directory = await get_current_directory()
    try:
        credentials = service_account.Credentials.from_service_account_file(project_directory + CREDENTIALS_FILE)
        service = build('calendar', 'v3', credentials=credentials)

        now = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).isoformat() + '+03:00'  # Текущая дата и время в формате UTC+3
        week_later = (datetime.datetime.utcnow() + datetime.timedelta(days=time_period, hours=3)).isoformat() + '+03:00'
        
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            timeMax=week_later,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        student = await get_student(student_tg_id)
        if not student:
            logging.warning(f"Студент с tg_id: {student_tg_id} не найден.")
            return (None, 0)

        first_name = student[1]
        last_name = student[2]

        if not events:
            logging.info("Нет запланированных уроков.")
            return (None, 0)
        else:
            events_list = []
            events_count = 0
            for event in events:
                event_name = event['summary']

                if ('УРОК' in event_name) and (first_name in event_name) and (last_name in event_name):
                    kid_name = event_name.split('; ')[1]
                    
                    start_time = event['start']['dateTime']
                    end_time = event['end']['dateTime']

                    start_correct_time = await time_get(start_time)
                    end_correct_time = await time_get(end_time)
                    
                    full_inf = [start_correct_time, end_correct_time, kid_name]

                    events_list.append(full_inf)
                    events_count += 1
            
            logging.info(f"Найдено {events_count} уроков для студента {first_name} {last_name}.")
            return [events_list, events_count]

    except Exception as e:
        logging.error(f'Ошибка при получении уроков: {e}')
        return (None, 0)


@exception_handler
async def notifications_process(update: Update, context: ContextTypes.DEFAULT_TYPE, notifications_json, student_tg_id):
    logging.info(f"Обработка уведомлений для студента с tg_id: {student_tg_id}.")
    
    kids_lessons_if, lessons_count = await get_kids_lessons(time_period=1, student_tg_id=student_tg_id)
    
    if lessons_count == 0:
        logging.info("Нет запланированных уроков для уведомления.")
        return  # Если уроков нет, выходим из функции

    day, hours, minutes = await get_current_time_formatted()
    user_id_str = str(student_tg_id)
    
    if user_id_str not in notifications_json:
        notifications_json[user_id_str] = {
            'warning_day_message': None,
            'warning_hour_message': None
        }
        
    warnings = notifications_json[user_id_str]
    warning_hour_message = warnings['warning_hour_message']
    warning_day_message = warnings['warning_day_message']

    start_inf = kids_lessons_if[0][0]
    start_day = int(start_inf['day'])
    
    start_hour_text = start_inf['hours']
    start_hour = int(start_hour_text)
    start_minutes_text = start_inf['minutes']
    start_minutes = int(start_minutes_text)

    time_lesson = f'{start_day}{start_hour}'

    day_check = time_lesson != warning_day_message
    hour_check = time_lesson != warning_hour_message
    w_t = (
                f'❗️ НАПОМИНАЮ ❗\n\n'
                f'У тебя завтра занятие с преподавателем по Химии.\n'
                f"Начало в {start_hour_text}:{start_minutes_text}.\n\n"
                "Занятие можно отменить/перенести бесплатно только за сутки (то есть сейчас). При отмене позже этого срока занятие подлежит оплате.\n\n"
                "Напоминаю о необходимости выполнения ДЗ. Отговорка 'забылось' не принимается - данное сообщение является официальным напоминанием. ДЗ может быть выдано за сутки до занятия, поэтому проверить дневник нужно сейчас."
            )
    if start_day - day == 1:
        if (24 - hours) + start_hour <= 24 and day_check:
            hours_delta = (24 - hours) + start_hour

            warning_text = (
                f'❗️ НАПОМИНАЮ ❗\n\n'
                f'У тебя завтра занятие с преподавателем по Химии.\n'
                f"Начало в {start_hour_text}:{start_minutes_text}.\n\n"
                "Занятие можно отменить/перенести бесплатно только за сутки (то есть сейчас). При отмене позже этого срока занятие подлежит оплате.\n\n"
                "Напоминаю о необходимости выполнения ДЗ. Отговорка 'забылось' не принимается - данное сообщение является официальным напоминанием. ДЗ может быть выдано за сутки до занятия, поэтому проверить дневник нужно сейчас."
            )
            await context.bot.send_message(chat_id=student_tg_id, text=warning_text)
            notifications_json[user_id_str]['warning_day_message'] = f'{start_day}{start_hour}'
            logging.info(f"Отправлено уведомление о занятии на завтра для студента {student_tg_id}.")

    elif start_day - day == 0:
        if (start_hour - hours) <= 24 and day_check:
            hours_delta = start_hour - hours

            warning_text = (
                f'❗️ НАПОМИНАЮ ❗\n\n'
                f'У тебя скоро занятие с преподавателем по Химии.\n'
                f'Начало в {start_hour_text}:{start_minutes_text}.\n'
                'Если ты ещё не выполнил ДЗ, то также напоминаю о его выполнении.'
            )
            await context.bot.send_message(chat_id=student_tg_id, text=warning_text)
            notifications_json[user_id_str]['warning_day_message'] = f'{start_day}{start_hour}' 
            logging.info(f"Отправлено уведомление о занятии сегодня для студента {student_tg_id}.")

        if start_hour - hours == 1 and hour_check:
            warning_text = (
                f'❗❗ НАПОМИНАЮ ❗❗\n\n'
                f'У тебя скоро занятие с преподавателем по Химии.\n'
                f'Начало в {start_hour_text}:{start_minutes_text}.\n'
                'Если ты ещё не выполнил ДЗ, то также напоминаю о его выполнении.'
            )
            await context.bot.send_message(chat_id=student_tg_id, text=warning_text)
            notifications_json[user_id_str]['warning_hour_message'] = f'{start_day}{start_hour}' 
            logging.info(f"Отправлено уведомление за час до занятия для студента {student_tg_id}.")
        
        elif start_hour - hours == 0 and hour_check:
            warning_text = (
                f'❗❗ НАПОМИНАЮ ❗❗\n\n'
                f'У тебя скоро занятие с преподавателем по Химии.\n'
                f'Начало в {start_hour_text}:{start_minutes_text}.\n'
                'Если ты ещё не выполнил ДЗ, то также напоминаю о его выполнении.'
            )
            await context.bot.send_message(chat_id=student_tg_id, text=warning_text)
            notifications_json[user_id_str]['warning_hour_message'] = f'{start_day}{start_hour}' 
            logging.info(f"Отправлено уведомление в момент занятия для студента {student_tg_id}.")

    await save_notifications(notifications_json)
    logging.info("Уведомления успешно сохранены.")


@exception_handler
async def test_f(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Запуск тестовой функции для обработки уведомлений.")
    
    students_id = await get_all_telegram_ids()
    notifications = await load_notifications()
    
    for student_tg_id in students_id:
        logging.info(f"Обработка уведомлений для студента с tg_id: {student_tg_id}.")
        await notifications_process(update, context, notifications, student_tg_id)


@exception_handler
async def get_current_time_formatted():
    now = datetime.datetime.now()
    
    day = int(now.strftime("%d"))
    hours = int(now.strftime("%H"))
    minutes = int(now.strftime("%M"))
    
    logging.info(f"Текущая дата и время: {day} {hours}:{minutes}.")
    return day, hours, minutes


@exception_handler
async def message_creator(start_event, end_event):
    logging.info("Создание сообщения о занятии.")
    
    start_day = start_event['day']
    start_month = start_event['month']
    start_hours = start_event['hours']
    start_minutes = start_event['minutes']

    end_hours = end_event['hours']
    end_minutes = end_event['minutes']

    day_start_inf = f'{start_day} {start_month}'
    event_start_inf = f'Начало занятия {day_start_inf} в {start_hours}:{start_minutes}'
    event_end_inf = f'И продлится оно до {end_hours}:{end_minutes}'
    
    logging.info("Сообщение о занятии успешно создано.")
    return day_start_inf, event_start_inf, event_end_inf


@exception_handler
async def time_get(time_dt_f):
    logging.info(f"Парсинг времени из строки: {time_dt_f}.")
    
    start_time_dt = datetime.datetime.fromisoformat(time_dt_f)

    start_hours = start_time_dt.strftime("%H")
    start_minutes = start_time_dt.strftime("%M")
    
    start_day = start_time_dt.strftime("%d").lstrip('0')  # Убираем ведущий ноль
    start_month = start_time_dt.strftime("%B")
    start_years = start_time_dt.strftime("%Y")
    start_month_rus = months_translation[start_month]
    
    inf = {
        'hours': start_hours,
        'minutes': start_minutes,
        'day': start_day,
        'month': start_month_rus,
    }
    
    logging.info(f"Парсинг времени завершен: {inf}.")
    return inf


@exception_handler
async def parse_date(date_str):
    logging.info(f"Парсинг даты из строки: {date_str}.")
    
    months = {
        'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
        'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
        'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
    }
    
    date_part, time_part = date_str.split(', ')
    day, month_name = date_part.split()
    month = months[month_name]
    
    parsed_date = f"2024-{month}-{int(day):02d}T{time_part}:00"
    logging.info(f"Парсинг даты завершен: {parsed_date}.")
    
    return parsed_date
