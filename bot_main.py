import asyncio

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

from settings import *
from bot_functions import *
from bd_functions import add_student, get_student, update_student
from registations_proccess import *
from constants import * 


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    user_inf = update.effective_user
    user_id = user_inf.id
    user_name = user_inf.username


    query = update.callback_query
    answer = await query.answer()  # Подтверждаем нажатие кнопки
    data = query.data


    # choosed_option = options[data]
    days_count = 7
    response_start = 'В ближайшее время'
    response_none_lessons = 'Можешь отдыхать, ты и так молодец ;)'

    lessons_informations, lessons_count = await get_kids_lessons(days_count, student_tg_id=user_id)
    


    if lessons_count.__eq__(0):
        response_dayly = (
        f'{response_start} у тебя нет занятий.\n{response_none_lessons}'
    )
    else:

        first_lesson = lessons_informations[0]

        start_inf, end_inf, kid_name = first_lesson
        day_start_inf, start_lesson, finish_lesson = await message_creator(start_inf, end_inf)

        response_dayly = (
            f'{response_start} у тебя есть занятия.\n'
            f'Ближайшее состоится {day_start_inf}\n\n'
            f'{start_lesson}.\n'
            f'{finish_lesson}.'
        )

    keyboard = [
        [InlineKeyboardButton('Ближайшее занятие', callback_data='near_lesson')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=response_dayly, reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_inf = update.effective_user
    user_id = user_inf.id

    message_text = (
        'Приветствую!\n\n'
        'Я буду подсказывать, когда у тебя предстоят занятия.\n'
        'Ты будешь получать от меня сообщения за день и за час до занятия\n\n'
        'Кроме того, ты можешь обратиться ко мне в любой момент, '
        'чтобы узнать когда у тебя ближайшее занятие на неделе или в этом месяце.'
    )
    keyboard = [
            ['Расписание'],
            ['Изменить имя']
        ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    student = await get_student(user_id)
    
    if not student:
        context.user_data['reg_status'] = 'start'
        await context.bot.send_message(chat_id=user_id, text=message_text)
        await register_proccess(context, update)
    
    else:
        name = student[1]
        message_text = f'Привет, {name}!'
        await update.message.reply_text(message_text, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_text = update.message.text
    if 'reg_status' in context.user_data:
        await register_proccess(context, update)
    
    elif current_text.__eq__('Расписание'):
        await hi_again(update, context)

    elif current_text.__eq__('Изменить имя'):
        context.user_data['reg_status'] = 'start'
        await register_proccess(context, update)


async def main(telegram_bot_token) -> None:
    
    nest_asyncio.apply()

    application = Application.builder().token(telegram_bot_token).build()

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
        