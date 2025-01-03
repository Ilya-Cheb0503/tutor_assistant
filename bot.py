import asyncio
import os
from functools import partial

import nest_asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

load_dotenv()

from constants import *
from constants.constants import *
from functions.bd_functions import *
from functions.bot_functions import *
from functions.postboy import *
from functions.registations_proccess import *
from project_config.settings import *
from project_config.wrapper import exception_handler


@exception_handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("Обработка нажатия кнопки.")
    
    user_inf = update.effective_user
    user_id = user_inf.id

    query = update.callback_query
    await query.answer()  # Подтверждаем нажатие кнопки

    days_count = 7
    response_start = 'В ближайшее время'
    response_none_lessons = 'Можешь отдыхать, ты и так молодец ;)'

    lessons_informations, lessons_count = await get_kids_lessons(days_count, student_tg_id=user_id)
    
    if lessons_count == 0:
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
            f'{finish_lesson}.\n\n'
            f'🕑 Время занятия указано по Московскому часовому поясу.'
        )

    keyboard = [
        [InlineKeyboardButton('Ближайшее занятие', callback_data='near_lesson')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text=response_dayly, reply_markup=reply_markup)


@exception_handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("Запуск команды /start.")
    
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
    if user_id in special_users:
        keyboard.append(['Рассылка'])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    student = await get_student(user_id)
    
    if not student:
        context.user_data['reg_status'] = 'start'
        await context.bot.send_message(chat_id=user_id, text=message_text)
        await register_process(context, update)
    else:
        name = student[1]
        message_text = f'Привет, {name}!'
        await update.message.reply_text(message_text, reply_markup=reply_markup)


@exception_handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("Обработка нажатия кнопки.")
    
    user_id = update.effective_user.id
    current_text = update.message.text
    
    if 'reg_status' in context.user_data:
        await register_process(context, update)
    elif 'message_state' in context.user_data and user_id in special_users: 
        await send_messages(update, context)
    elif current_text == 'Расписание':
        await hi_again(update, context)
    elif current_text == 'Изменить имя':
        context.user_data['reg_status'] = 'start'
        await register_process(context, update)
    elif current_text == 'Рассылка' and user_id in special_users:
        await send_messages(update, context)
    else:
        logging.warning(f"Неизвестная команда: {current_text}")
        await update.message.reply_text("Извините, я не понимаю эту команду.")


@exception_handler
async def start_notion(update, context):
    user_id = update.effective_user.id
    if str(user_id) == '2091023767':
        logging.info('Запускаем рассылку уведомлений.')

        await test_f(update, context)  # Стартуем уведомления здесь и сейчас

        scheduler = AsyncIOScheduler()
        scheduler.add_job(partial(test_f, update, context), 'interval', minutes=30)  # Запрашиваем события каждые 30 минут
        scheduler.start()

        logging.info('Запустили рассылку уведомлений.')
        await context.bot.send_message(chat_id=user_id, text='Уведомления запущены')
    else:
        logging.warning(f"Попытка запуска рассылки от пользователя с ID: {user_id}, доступ запрещен.")


@exception_handler
async def main(telegram_bot_token) -> None:
    nest_asyncio.apply()

    application = Application.builder().token(telegram_bot_token).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('developer_hand', start_notion))
    application.add_handler(CallbackQueryHandler(button_callback))  # Добавляем обработчик для инлайн кнопок
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND | filters.PHOTO, button_handler))

    # Запускаем бота
    logging.info('Бот запущен.')
    try:
        await application.run_polling()
    except (KeyboardInterrupt, SystemExit):
        logging.error("Бот остановлен.", exc_info=True)
        await application.stop()

if __name__ == '__main__':
    try:
        bot_token = os.getenv('BOT_TOKEN')
        if not bot_token:
            raise ValueError("Токен бота не найден.")
    except Exception as er:
        logging.error(f'Не удалось получить токен телеграм бота.\n{er}\nПроверьте наличие .env')

    asyncio.run(main(bot_token))
