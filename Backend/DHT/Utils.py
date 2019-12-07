import logging
import hashlib
from Pyro4.errors import *
from Backend.DHT.Settings import *
import Pyro4
import sys
import pickle
import socket

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook

# connection mode
STREAM = 1
STATIC = 2

def get_alive_nodes():
    ns = Pyro4.locateNS()
    return list(ns.list(prefix="Node:").items())


# Network comunication sockets

# send data (real data)
def send(sock, data):
    data = pickle.dumps(data)
    blocks = (len(data) + BLOCK_SIZE - 1) // BLOCK_SIZE

    sock.send(pickle.dumps(blocks))
    msg = sock.recv(BLOCK_SIZE)

    for i in range(0, len(data), BLOCK_SIZE):
        arr = data[i:min(i + BLOCK_SIZE, len(data))]

        sock.send(arr)
        sock.recv(BLOCK_SIZE)


# it returns the real data
def recieve(sock):
    blocks = pickle.loads(sock.recv(BLOCK_SIZE))
    sock.send(b"ok")

    data = bytearray()
    for i in range(blocks):
        arr = sock.recv(BLOCK_SIZE)
        sock.send(b"ok")
        data += arr

    return pickle.loads(data)


def get_unused_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        addr, port = sock.getsockname()
        return port


class Utils:
    @staticmethod
    def ping(node):
        try:
            # always return True
            return node.ping()

        except CommunicationError:
            pass

        return False

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
    def between(c: int, a: int, b: int):
        """
        Is c in interval [a, b)
        if a == b then it is the whole circle so will return True
        :param c: id c
        :param a: id a
        :param b: id b
        :return: bool
        """
        a = a % SIZE
        b = b % SIZE
        c = c % SIZE
        if a < b:
            return a <= c and c < b
        return a <= c or c < b

    @staticmethod
    def get_hash(location: str):
        h = hashlib.sha1(location.encode()).hexdigest()
        h = int(h, 16)
        return h

    @staticmethod
    def debug_node(node):  #recibe un Pyro4.Proxy
        s = str.format("\nNode with hash = %d\n" % node.hash)

        try:
            if node.predecessor is None:
                s += str.format("Predecessor hash = None\n")
            else:
                s += str.format("Predecessor hash = %d\n" % node.predecessor.hash)

        except CommunicationError:
            s += str.format("Predecessor hash = None (node down maybe?)\n")

        to = list(node.finger)

        s += "Info on finger table entries\n"
        for i in range(len(to)):
            try:
                if to[i] is None:
                    s += str.format("i = %d, hash = None\n" % i)

                else:
                    s += str.format("i = %d, hash = %d\n" % (i, to[i].hash))

            except CommunicationError:
                s += str.format("i = %d, hash = None (node down maybe?)\n" % i)

        successor_list = node.successor_list

        s += "Info on successor list\n"
        for i in range(len(successor_list)):
            try:
                if successor_list[i] is None:
                    s += str.format("i = %d, hash = None\n" % i)

                else:
                    s += str.format("i = %d, hash = %d\n" % (i, successor_list[i].hash))

            except CommunicationError:
                s += str.format("i = %d, hash = None (node down maybe?)\n" % i)

        s += "Info on songs\n"

        songs = node.songs

        for song in songs:
            s += str.format("name = %s, hash = %d\n" % (song.name, song.hash))

        return s
