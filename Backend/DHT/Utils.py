import logging
from Pyro4.errors import *
from Backend.DHT.Settings import *

class Utils:
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

    @staticmethod
    def debug_node(node):  #recibe un Pyro4.Proxy
        s = str.format("\nNode with hash = %d\n" % node.hash)

        try:
            s += str.format("Predecessor hash = %d\n" % node.predecessor.hash)

        except CommunicationError:
            s += str.format("Predecessor hash = None (node down maybe?)\n")

        start = list(node.start)
        to = list(node.to)

        s += "Info on start entries\n"
        for i in range(len(start)):
            s += str.format("i = %d, start = %d\n" % (i, start[i]))

        s += "Info on finger table entries\n"
        for i in range(len(to)):
            try:
                if to[i] is None:
                    s += str.format("i = %d, hash = None\n" % i)

                else:
                    s += str.format("i = %d, hash = %d\n" % (i, to[i].hash))

            except CommunicationError:
                s += str.format("i = %d, hash = None (node down maybe?)\n" % i)

        succesor_list = node.succesor_list

        s += "Info on succesor list\n"
        for i in range(SUCC_LIST_LEN):
            try:
                if succesor_list[i] is None:
                    s += str.format("i = %d, hash = None\n" % i)

                else:
                    s += str.format("i = %d, hash = %d\n" % (i, succesor_list[i].hash))

            except CommunicationError:
                s += str.format("i = %d, hash = None (node down maybe?)\n" % i)

        return s
