import logging

BASE_LOGGER = logging.getLogger('nowem')

BASE_HANDLER = logging.StreamHandler()

BASE_FORMATTER = logging.Formatter(f'[%(levelname)s] %(asctime)s @ %(name)s(%(funcName)s): %(message)s')

BASE_HANDLER.setFormatter(BASE_FORMATTER)
BASE_HANDLER.setLevel(logging.DEBUG)
BASE_LOGGER.addHandler(BASE_HANDLER)
BASE_LOGGER.setLevel(logging.INFO)


def enable_debug():
    BASE_LOGGER.setLevel(logging.DEBUG)


def disable_debug():
    BASE_LOGGER.setLevel(logging.INFO)
