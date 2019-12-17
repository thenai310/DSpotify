import logging
import hashlib
from Pyro4.errors import *
from Backend.DHT.Settings import *
import Pyro4
import sys
import socket
import os

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
Pyro4.config.THREADPOOL_SIZE = THREADPOOL
sys.excepthook = Pyro4.util.excepthook

# get current alive nodes
def get_alive_nodes():
    ns = Pyro4.locateNS()
    return list(ns.list(prefix="Node:").items())


def get_anyone_alive():
    alive = get_alive_nodes()

    for name, uri in alive:
        node = Pyro4.Proxy(uri)

        if Utils.ping(node):
            return node

        node._pyroRelease()

    return None


# return set of tuples (dir, name) of local songs
# Note local, NOT shared!!!
def get_local_songs_tuple_set(dir_address):
    s = set()

    for (dir, _, files) in os.walk(dir_address):
        for name in files:
            s.add((dir, name))

    return s


# return set of Song
def get_song_list():
    alive = get_alive_nodes()

    songs = set()

    for name, uri in alive:
        node = Pyro4.Proxy(uri)

        if Utils.ping(node):
            songs |= node.get_all_songs()

        node._pyroRelease()

    return songs


def get_unused_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        addr, port = sock.getsockname()
        return port


class Song:
    def __init__(self, full_path, name, hash, who=None):
        self.full_path = full_path
        self.name = name
        self.hash = hash
        self.node = who

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return self.hash


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
    def debug_node(node):  # recibe un Pyro4.Proxy
        s = "\n" + "-" * 100 + "\n"
        s += str.format("Node with hash = %d\n" % node.hash)


        try:
            if node.predecessor is None:
                s += str.format("Predecessor hash = None\n")
            else:
                s += str.format("Predecessor hash = %d\n" % node.predecessor.hash)

        except CommunicationError:
            s += str.format("Predecessor hash = None (node down maybe?)\n")

        s += "-" * 100 + "\n"

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

        s += "-" * 100 + "\n"

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

        s += "-" * 100 + "\n"

        s += "Local songs\n"
        songs = node.local_songs

        for song in songs:
            s += str.format("name = %s, hash = %d\n" % (song.name, song.hash))

        s += "-" * 100 + "\n"

        s += "Shared songs\n"

        songs = node.shared_songs

        for song in songs:
            s += str.format("name = %s, hash = %d\n" % (song.name, song.hash))

        s += "-" * 100 + "\n"

        return s
