from project_config.settings import *
from constants.constants import DEVELOPER_ID

from functools import wraps


def exception_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Ошибка в функции {func.__name__}: {e}")
            # Здесь можно добавить дополнительную логику, например, отправку сообщения пользователю
            await args[1].bot.send_message(chat_id=DEVELOPER_ID, text=f"Ошибка в функции {func.__name__}: {e}")
            await args[1].bot.send_message(chat_id=args[0].effective_user.id, text="Если вы видите это сообщение, значит произошла ошибка в работе бота.\nУведомление об этом уже отправлено разработчику, но вы можете также уведомить преподавателя.")
    return wrapper