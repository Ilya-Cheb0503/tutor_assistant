import aiosqlite
import asyncio


DATABASE_NAME = "students.db"

async def create_database():
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

async def add_student(first_name, last_name, tg_id):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute('''
            INSERT INTO students (first_name, last_name, tg_id)
            VALUES (?, ?, ?)
        ''', (first_name, last_name, tg_id))
        await db.commit()

async def get_student(tg_id):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute('''
            SELECT * FROM students WHERE tg_id = ?
        ''', (tg_id,)) as cursor:
            student = await cursor.fetchone()
            return student


async def get_all_students():
    async with aiosqlite.connect(DATABASE_NAME) as db:
        query = "SELECT * FROM students"
        students = await database.fetch_all(query)
    
        return students


# Новая функция для извлечения всех telegram_id
async def get_all_telegram_ids():
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute('''
            SELECT tg_id FROM students
        ''') as cursor:
            tg_ids = await cursor.fetchall()
            return [tg_id[0] for tg_id in tg_ids]


async def update_student(tg_id, first_name=None, last_name=None):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        if first_name:
            await db.execute('''
                UPDATE students SET first_name = ? WHERE tg_id = ?
            ''', (first_name, tg_id))
        if last_name:
            await db.execute('''
                UPDATE students SET last_name = ? WHERE tg_id = ?
            ''', (last_name, tg_id))
        await db.commit()

async def delete_student(tg_id):
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute('''
            DELETE FROM students WHERE tg_id = ?
        ''', (tg_id,))
        await db.commit()


async def main():
    # await create_database()
    # await add_student("Иван", "Иванов", "123456")
    # await add_student("Петр", "Петров", "654321")

    # student = await get_student("123456")
    # print(f"Найденный студент: {student}")

    # await update_student("2091023767", last_name='123')
    # # await update_student("2091023767", last_name="Цуканов")
    # updated_student = await get_student("2091023767")
    # print(f"Обновленный студент: {updated_student}")

    # await delete_student("5086356786")
    # student1 = await get_student("7109530392")
    students = await get_all_telegram_ids()
    print(students)

if __name__ == "__main__":
    asyncio.run(main())