import asyncio

import aiosqlite

from project_config.wrapper import exception_handler
from project_config.settings import *
DATABASE_NAME = "database/students.db"


@exception_handler
async def create_database():
    logging.info("Создание базы данных и таблицы студентов.")
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                tg_id TEXT NOT NULL
            )
        ''')
        await db.commit()
    logging.info("Таблица студентов успешно создана.")


@exception_handler
async def add_student(first_name, last_name, tg_id):
    logging.info(f"Добавление студента: {first_name} {last_name} с tg_id: {tg_id}.")
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute('''
            INSERT INTO students (first_name, last_name, tg_id)
            VALUES (?, ?, ?)
        ''', (first_name, last_name, tg_id))
        await db.commit()
    logging.info("Студент успешно добавлен.")


@exception_handler
async def get_student(tg_id):
    logging.info(f"Получение студента с tg_id: {tg_id}.")
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute('''
            SELECT * FROM students WHERE tg_id = ?
        ''', (tg_id,)) as cursor:
            student = await cursor.fetchone()
            if student:
                logging.info(f"Студент найден: {student}.")
            else:
                logging.warning(f"Студент с tg_id: {tg_id} не найден.")
            return student


@exception_handler
async def get_all_students():
    logging.info("Получение всех студентов.")
    async with aiosqlite.connect(DATABASE_NAME) as db:
        query = "SELECT * FROM students"
        students = await db.execute(query)
        students_list = await students.fetchall()
    logging.info(f"Количество студентов: {len(students_list)}.")
    return students_list


@exception_handler
async def get_all_telegram_ids():
    logging.info("Получение всех tg_id студентов.")
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute('''
            SELECT tg_id FROM students
        ''') as cursor:
            tg_ids = await cursor.fetchall()
            logging.info(f"Количество tg_id получено: {len(tg_ids)}.")
            return [tg_id[0] for tg_id in tg_ids]


@exception_handler
async def update_student(tg_id, first_name=None, last_name=None):
    logging.info(f"Обновление студента с tg_id: {tg_id}.")
    async with aiosqlite.connect(DATABASE_NAME) as db:
        if first_name:
            await db.execute('''
                UPDATE students SET first_name = ? WHERE tg_id = ?
            ''', (first_name, tg_id))
            logging.info(f"Имя студента обновлено на: {first_name}.")
        if last_name:
            await db.execute('''
                UPDATE students SET last_name = ? WHERE tg_id = ?
            ''', (last_name, tg_id))
            logging.info(f"Фамилия студента обновлена на: {last_name}.")
        await db.commit()
    logging.info("Данные студента успешно обновлены.")


@exception_handler
async def delete_student(tg_id):
    logging.info(f"Удаление студента с tg_id: {tg_id}.")
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute('''
            DELETE FROM students WHERE tg_id = ?
        ''', (tg_id,))
        await db.commit()
    logging.info("Студент успешно удален.")


@exception_handler
async def main():
    # await create_database()
    # await add_student("Иван", "Иванов", "123456")

    # student = await get_student("123456")
    # print(f"Найденный студент: {student}")

    # # await update_student("123456", last_name="Цуканов")
    # updated_student = await get_student("123456")
    # print(f"Обновленный студент: {updated_student}")

    # await delete_student("123456")
    students = await get_all_telegram_ids()
    print(students)


if __name__ == "__main__":
    asyncio.run(main())
