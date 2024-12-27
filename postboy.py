import asyncio
import os
import time
from functools import partial

import nest_asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)


from bd_functions import get_all_telegram_ids
from constants import *

async def send_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Запрос текста сообщения от пользователя
    message_creator = {
        'Creating' : message_text_getting,
        'Edited' : message_text_confirmation,
        'Completed' : message_text_sending
    }
    if 'message_state' not in context.user_data:
        context.user_data['message_state'] = 'Creating'
    current_message_state = context.user_data.get('message_state')

    current_step = message_creator[current_message_state]

    await current_step(update, context)


async def message_text_getting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    context.user_data['message_text'] = None

    await update.message.reply_text('Пришлите мне сообщение, которое хотите разослать:', reply_markup=ReplyKeyboardRemove())

    context.user_data['message_state'] = 'Edited'

async def message_text_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user_id = update.effective_user.id
    message_text, image_path = await download_message_with_image(update, context)
    context.user_data['message_inf'] = (message_text, image_path)
    
    keyboard = [
        ['Да'],
        ['Нет']
        
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Вы хотите отправить следующее сообщение?', reply_markup=reply_markup)
    await forward_message_with_image(update, context, message_text, image_path, user_id)
    context.user_data['message_state'] = 'Completed'


async def message_text_sending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    keyboard = [
            ['Расписание'],
            ['Изменить имя'],
            ['Рассылка']
        ]


    message_text = update.message.text
    if message_text == 'Да':
        current_message_text, image_path = context.user_data.get('message_inf')
        students_id = await get_all_telegram_ids()


        for user_id in students_id:
            try:
                await forward_message_with_image(update, context, current_message_text, image_path, user_id)
            except Exception as error:
                pass
        await delete_file(image_path)
        context.user_data.pop('message_state')
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('Рассылка завершена.', reply_markup=reply_markup)

    elif message_text == 'Нет':
        context.user_data['message_state'] = 'Creating'
        await message_text_getting(update, context)
    

async def download_message_with_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получаем текст сообщения
    message_text = update.message.text
    file_path = None

    if update.message.photo:
        message_text = update.message.caption
        context.user_data['current_text'] = message_text
        photo = update.message.photo[-1]  # Получаем самое высокое качество изображения
        file = await photo.get_file()
        file_path = f"{DOWNLOAD_PATH}/{photo.file_id}.jpg"
        context.user_data['photo_path'] = file_path  # Путь для сохранения изображения
        await file.download_to_drive(file_path)

        return message_text, file_path

    else:
        # Если изображения нет, просто отправляем текст
        return message_text, file_path


async def forward_message_with_image(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text, image_path, user_id) -> None:
    
    # Проверяем, есть ли вложение (изображение)
    if image_path:

        # Отправляем новое сообщение с изображением и текстом
        with open(image_path, 'rb') as img_file:
            await context.bot.send_photo(chat_id=user_id, photo=img_file, caption=message_text, parse_mode='Markdown')
    else:
        # Если изображения нет, просто отправляем текст
        await context.bot.send_message(chat_id=user_id, text=message_text, parse_mode='Markdown')


async def delete_file(file_path):
    """Удаляет файл по указанному пути, если он существует."""
    try:
        # Проверяем, существует ли файл
        if os.path.isfile(file_path):
            os.remove(file_path)  # Удаляем файл
            print(f"Файл '{file_path}' успешно удален.")
        else:
            print(f"Файл '{file_path}' не найден.")
    except Exception as e:
        print(f"Произошла ошибка при удалении файла: {e}")
