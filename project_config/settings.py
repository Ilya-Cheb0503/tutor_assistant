import logging
from logging.handlers import RotatingFileHandler
import os

log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_file_path = os.path.join(log_directory, 'common_logs.log')
handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=10, encoding='utf-8')
formatter = logging.Formatter('%(levelname)s\n%(asctime)s\n%(message)s\n'
                              '%(name)s, %(filename)s, '
                              '%(funcName)s, %(lineno)s\n')
handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[handler],
)