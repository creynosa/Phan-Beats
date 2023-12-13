import logging


def createLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        logger.propagate = False
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)-8s %(name)-20s %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger
