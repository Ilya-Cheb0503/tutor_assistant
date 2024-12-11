import asyncio
import logging
import os
import time
from functools import partial

import nest_asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

load_dotenv()

from bot_functions import *

TEACHER_ID = 5086356786
TEACHER_EMAIL = 'rinigudini@gmail.com'

logging.basicConfig(
    level=logging.INFO,
    filename='bot_log.log',

    format=('%(levelname)s\n%(asctime)s\n%(message)s\n'
            '%(name)s, %(filename)s, '
            '%(funcName)s, %(lineno)s\n'),
    filemode='w',
    encoding='utf-8'
)

# Хранение пользователей
users = set()
admins_id = []

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    user_inf = update.effective_user
    user_id = user_inf.id
    user_name = user_inf.username

    user_r = 'kid'

    user_role = {
       'teacher': get_lessons_for_teacher,
       'kid': get_kids_lessons
    }


    options = {
        'week': [7, 'На этой неделе', 'Попробуй проверить расписание на месяц.'],
        'month': [30, 'В этом месяце', 'В этом месяце можешь отдыхать ;)'],
    }

    query = update.callback_query
    answer = await query.answer()  # Подтверждаем нажатие кнопки
    data = query.data


    choosed_option = options[data]
    days_count = choosed_option[0]
    response_start = choosed_option[1]
    response_none_lessons = choosed_option[2]

    role_func = user_role[user_r]
    lessons_informations, lessons_count = await role_func(days_count, user_name)
    first_lesson = lessons_informations[0]

    start_inf, end_inf, kid_name = first_lesson
    day_start_inf, start_lesson, finish_lesson = await message_creator(start_inf, end_inf)


    if lessons_count.__eq__(0):
        response_dayly = (
        f'{response_start} у тебя нет занятий.\n{response_none_lessons}'
    )
    else:

        response_dayly = (
            f'{response_start} у тебя есть занятия.\n'
            f'Ближайшее состоится {day_start_inf}\n\n'
            f'{start_lesson}.\n'
            f'{finish_lesson}.'
        )

    if user_r.__eq__('teacher'):
        response_dayly = response_dayly.__add__(f'\nИмя ученика: {kid_name}.')
    # await context.bot.send_message(chat_id=user_id, text=response_dayly)
    
    keyboard = [
        [InlineKeyboardButton('Занятия на этой неделе', callback_data='week')],
        [InlineKeyboardButton('Занятия в этом месяце', callback_data='month')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=response_dayly, reply_markup=reply_markup)


    # text = query.data[1]
    # Обрабатываем нажатие кнопки
    # await query.edit_message_text(text=f"Selected option: {query.data}", reply_markup=reply_markup)
    # await query.edit_message_text(text=f"{vacancy_id}\nВы откликнулись на вакансию\n{text_v}")
    # await query.answer(f'{text_v}')


# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_inf = update.effective_user
    user_id = user_inf.id

    scheduler = AsyncIOScheduler()
    scheduler.add_job(partial(test_f, update, context), 'interval', seconds=10)  # Запрашиваем события каждый час
    scheduler.start()

    keyboard = [
        [InlineKeyboardButton('Занятия на этой неделе', callback_data='week')],
        [InlineKeyboardButton('Занятия в этом месяце', callback_data='month')],
    ]

    # Создаем разметку для кнопок
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Отправляем сообщение с инлайн кнопками
    
    message_text = (
        'Приветствую!\n\n'
        'Я буду подсказывать, когда у тебя предстоят занятия.\n'
        'Ты будешь получать от меня сообщения за день и за час до занятия\n\n'
        'Кроме того, ты можешь обратиться ко мне в любой момент, '
        'чтобы узнать когда у тебя ближайшее занятие на неделе или в этом месяце.'
    )

    await context.bot.send_message(chat_id=user_id, text=message_text)
    time.sleep(0)

    second_message = 'Есть что-то, что ты бы хотел(-ла) сейчас узнать?'
    await update.message.reply_text(second_message, reply_markup=reply_markup)


async def send_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(second_message, reply_markup=reply_markup)


# Функция для обработки нажатий кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_text = update.message.text
    pass

    # await current_menu(current_text, update, context)


async def main(telegram_bot_token) -> None:
    
    nest_asyncio.apply()

    application = Application.builder().token(telegram_bot_token).build()

    # Регистрируем обработчики команд и сообщений
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_callback))  # Добавляем обработчик для инлайн кнопок
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND | filters.PHOTO, button_handler))

    


    # Запускаем бота
    logging.info('Бот запущен')
    try:
        # Запускаем бота
          # Запуск планировщика
        await application.run_polling()
    except (KeyboardInterrupt, SystemExit):
        # Обрабатываем исключения, чтобы избежать вывода в терминал
        logging.error(f"Бот остановлен", exc_info=True)
        await application.stop()
    

if __name__ == '__main__':
    
    try:
        # Замените 'YOUR_TOKEN' на токен вашего бота
        bot_token = os.getenv('BOT_TOKEN')
    except Exception as er:
        logging.error(f'Не получилось получить токен телеграм бота.\n{er}\nПроверьте наличие .env')

    asyncio.run(main(bot_token))
        