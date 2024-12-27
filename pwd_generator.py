import asyncio
import os


async def get_current_directory():
    """Возвращает текущую директорию, в которой находится исполняемый файл."""
    # Получаем абсолютный путь к текущему файлу
    current_file_path = os.path.abspath(__file__)
    # Извлекаем директорию из полного пути
    current_directory = os.path.dirname(current_file_path)
    return current_directory

# Пример использования
async def main():
    pwd = await get_current_directory()
    print(pwd)


if __name__ == "__main__":
    asyncio.run(main())
