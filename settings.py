import logging


logging.basicConfig(
    level=logging.INFO,
    filename='bot_log.log',

    format=('%(levelname)s\n%(asctime)s\n%(message)s\n'
            '%(name)s, %(filename)s, '
            '%(funcName)s, %(lineno)s\n'),
    filemode='w',
    encoding='utf-8'
)