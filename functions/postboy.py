import os

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from project_config.wrapper import exception_handler
from project_config.settings import *
from constants.constants import *
from functions.bd_functions import get_all_telegram_ids
from pwd_generator import get_current_directory


@exception_handler
async def send_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("Запуск процесса отправки сообщений.")
    
    message_creator = {
        'Creating': message_text_getting,
        'Edited': message_text_confirmation,
        'Completed': message_text_sending
    }
    
    if 'message_state' not in context.user_data:
        context.user_data['message_state'] = 'Creating'
    
    current_message_state = context.user_data.get('message_state')
    current_step = message_creator[current_message_state]

    await current_step(update, context)


@exception_handler
async def message_text_getting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    logging.info("Запрос текста сообщения от пользователя.")
    
    context.user_data['message_text'] = None

    keyboard = [
        ['Отмена'],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Пришлите мне сообщение, которое хотите разослать:', reply_markup=reply_markup)

    context.user_data['message_state'] = 'Edited'


@exception_handler
async def message_text_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    logging.info("Подтверждение текста сообщения.")
    
    user_id = update.effective_user.id
    message_text, image_path = await download_message_with_image(update, context)
    context.user_data['message_inf'] = (message_text, image_path)
    
    keyboard = [
        ['Да'],
        ['Нет']
    ]

    main_keyboard = [
        ['Расписание'],
        ['Изменить имя'],
        ['Рассылка']
    ]
    
    if message_text == 'Отмена':    
        context.user_data.pop('message_state')
        reply_markup = ReplyKeyboardMarkup(main_keyboard, resize_keyboard=True)
        await update.message.reply_text('Отмена рассылки', reply_markup=reply_markup)
        logging.info("Рассылка отменена пользователем.")
        return

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('Вы хотите отправить следующее сообщение?', reply_markup=reply_markup)
    await forward_message_with_image(update, context, message_text, image_path, user_id)
    context.user_data['message_state'] = 'Completed'


@exception_handler
async def message_text_sending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.info("Отправка сообщения пользователям.")
    
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
                logging.info(f"Сообщение отправлено пользователю с tg_id: {user_id}.")
            except Exception as error:
                logging.error(f"Ошибка при отправке сообщения пользователю с tg_id: {user_id}: {error}")
        
        if image_path:
            await delete_file(image_path)
        
        context.user_data.pop('message_state')
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('Рассылка завершена.', reply_markup=reply_markup)

    elif message_text == 'Нет':
        context.user_data['message_state'] = 'Creating'
        await message_text_getting(update, context)


@exception_handler
async def download_message_with_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Загрузка сообщения с изображением.")
    
    project_directory = await get_current_directory()
    message_text = update.message.text
    file_path = None

    if update.message.photo:
        message_text = update.message.caption
        context.user_data['current_text'] = message_text
        photo = update.message.photo[-1]  # Получаем самое высокое качество изображения
        file = await photo.get_file()
        file_path = f"{project_directory + DOWNLOAD_PATH}/{photo.file_id}.jpg"
        context.user_data['photo_path'] = file_path  # Путь для сохранения изображения
        
        await file.download_to_drive(file_path)
        logging.info(f"Изображение загружено и сохранено по пути: {file_path}.")
        return message_text, file_path

    logging.info("Изображение не найдено, возвращаем только текст сообщения.")
    return message_text, file_path


@exception_handler
async def forward_message_with_image(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text, image_path, user_id) -> None:
    logging.info(f"Пересылка сообщения пользователю с tg_id: {user_id}.")
    
    if image_path:
        # Отправляем новое сообщение с изображением и текстом
        try:
            with open(image_path, 'rb') as img_file:
                await context.bot.send_photo(chat_id=user_id, photo=img_file, caption=message_text, parse_mode='Markdown')
            logging.info("Сообщение с изображением успешно отправлено.")
        except Exception as error:
            logging.error(f"Ошибка при отправке изображения пользователю с tg_id: {user_id}: {error}")
    else:
        # Если изображения нет, просто отправляем текст
        await context.bot.send_message(chat_id=user_id, text=message_text, parse_mode='Markdown')
        logging.info("Сообщение без изображения успешно отправлено.")


@exception_handler
async def delete_file(file_path):
    """Удаляет файл по указанному пути, если он существует."""
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)  # Удаляем файл
            logging.info(f"Файл '{file_path}' успешно удален.")
        else:
            logging.warning(f"Файл '{file_path}' не найден.")
    except Exception as e:
        logging.error(f"Произошла ошибка при удалении файла: {e}")
