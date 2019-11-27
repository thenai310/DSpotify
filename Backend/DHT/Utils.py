from Backend.DHT.Node import MOD
import logging
import hashlib

class Utils:
    @staticmethod
    def on_interval(x: int, a: int, b: int):
        """
        Is x from a to b?

        :param x: parameter to search
        :param a: start of interval (inclusive)
        :param b: end of interval (inclusive)
        :return: Boolean
        """

        if a <= b:
            return a <= x <= b

        return Utils.on_interval(x, a, MOD - 1) or Utils.on_interval(x, 0, b)

    @staticmethod
    def get_hash(location: str):
        h = hashlib.sha1(location.encode()).hexdigest()
        h = int(h, 16)
        return h

    @staticmethod
    def init_logger(logger_name):
        # create logger
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to ch
        ch.setFormatter(formatter)

        # add ch to logger
        logger.addHandler(ch)

        return logger