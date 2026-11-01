import logging

from dependencies.logger.buffer_handler import BufferHandler


class Logging:
    buffer_handler = None

    @staticmethod
    def setup(level=logging.INFO):
        logging.basicConfig(level=level, format="%(asctime)s %(levelname)-8s %(name)s %(message)s")
        logging.getLogger("discord").setLevel(logging.WARNING)
        Logging.buffer_handler = BufferHandler()
        logging.getLogger().addHandler(Logging.buffer_handler)

    @staticmethod
    def get_logger(name):
        return logging.getLogger(f"zois.{name}")
