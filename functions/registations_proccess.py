from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from constants.constants import *
from functions.bd_functions import add_student, get_student, update_student
from functions.bot_functions import hi_again
from project_config.wrapper import exception_handler
from project_config.settings import *

@exception_handler
async def register_process(context, update):
    logging.info("Запуск процесса регистрации.")
    
    reg_status = context.user_data.get('reg_status', 'start')

    register_status = {
        'start': name_asking,
        'correction': correction_ask,
        'confirmation': confirmation_process,
    }

    step = register_status.get(reg_status)
    if step:
        await step(context, update)
    else:
        logging.error(f"Неизвестный статус регистрации: {reg_status}.")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, начните регистрацию заново.")


@exception_handler
async def name_asking(context, update):
    logging.info("Запрос имени и фамилии у пользователя.")
    
    context.user_data['reg_status'] = 'correction'
    ask_text = (
        'Сперва укажите пожалуйста свои настоящие Имя и Фамилию\n'
        'Пример: Александр Пушкин'
    )
    await update.message.reply_text(ask_text, reply_markup=ReplyKeyboardRemove())


@exception_handler
async def correction_ask(context, update):
    logging.info("Запрос подтверждения имени и фамилии.")
    
    context.user_data['reg_status'] = 'confirmation'
    current_text = update.message.text
    
    try:
        name, surname = current_text.split(' ')
        context.user_data['full_name'] = (name, surname)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите имя и фамилию через пробел.")
        return await name_asking(context, update)

    correction_ask_text = (
        f'Твое имя: {name}\n'
        f'А фамилия: {surname}\n'
        'Верно?'
    )

    keyboard = [
        ['Да'],
        ['Нет']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(correction_ask_text, reply_markup=reply_markup)


@exception_handler
async def confirmation_process(context, update):
    logging.info("Подтверждение регистрации.")
    
    current_text = update.message.text
    if current_text == 'Да':
        user_id = update.effective_user.id
        name, surname = context.user_data['full_name']

        student = await get_student(user_id)
        if student:
            await update_student(user_id, name, surname)
            logging.info(f"Данные студента обновлены: {name} {surname}.")
        else:
            await add_student(name, surname, user_id)
            logging.info(f"Новый студент добавлен: {name} {surname}.")

        keyboard = [
            ['Расписание'],
            ['Изменить имя']
        ]
        if user_id in special_users:
            keyboard.append(['Рассылка'])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f'Регистрация успешно завершена!\nРад знакомству, {name} {surname}\n\nДля окончания регистрации необходимо переслать это сообщение Ринату Бахтияровичу.', reply_markup=reply_markup)
        context.user_data.pop('reg_status')
        await hi_again(update, context)
    else:
        context.user_data['reg_status'] = 'start'
        await update.message.reply_text(f'Давай попробуем еще раз.', reply_markup=ReplyKeyboardRemove())
        await name_asking(context, update)
