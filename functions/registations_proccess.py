from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from functions.bd_functions import add_student, get_student, update_student
from functions.bot_functions import hi_again


from constants.constants import *

async def register_proccess(context, update):
    
    reg_status = context.user_data['reg_status']

    register_status = {
        'start': name_asking,
        'correction': correction_ask,
        'confirmation': confirmation_procces,
    }

    step = register_status[reg_status]

    await step(context, update)


async def name_asking(context, update):
    context.user_data['reg_status'] = 'correction'
    user_id = update.effective_user.id
    ask_text = (
        'Сперва укажите пожалуйста свои настоящие Имя и Фамилию\n'
        'Пример: Александр Пушкин'
    )
    await update.message.reply_text(ask_text, reply_markup=ReplyKeyboardRemove())
    # await context.bot.send_message(chat_id=user_id, text=ask_text)
    

async def correction_ask(context, update):
    context.user_data['reg_status'] = 'confirmation'
    # user_id = update.effective_user.id
    current_text = update.message.text
    name, sername = current_text.split(' ')
    context.user_data['full_name'] = (name, sername)
    correction_ask = (
        f'Твое имя: {name}\n'
        f'А фамилия: {sername}\n'
        'Верно?'
    )

    # await context.bot.send_message(chat_id=user_id, text=correction_ask)
    keyboard = [
        ['Да'],
        ['Нет']
        
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(correction_ask, reply_markup=reply_markup)


async def confirmation_procces(context, update):
    current_text = update.message.text
    if current_text.__eq__('Да'):
        user_id = update.effective_user.id
        name, sername = context.user_data['full_name']

        student = await get_student(user_id)
        if student:
            await update_student(user_id, name, sername)
        else:
            await add_student(name, sername, user_id)
        keyboard = [
            ['Расписание'],
            ['Изменить имя']
        ]
        if user_id in special_users:
            keyboard.append(['Рассылка'])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f'Регистрация успешно завершена!\nРад знакомству, {name}', reply_markup=reply_markup)
        context.user_data.pop('reg_status')
        await hi_again(update, context)
    else:
        context.user_data['reg_status'] = 'start'
        await update.message.reply_text(f'Давай попробуем еще раз.', reply_markup=ReplyKeyboardRemove())
        await name_asking(context, update)
