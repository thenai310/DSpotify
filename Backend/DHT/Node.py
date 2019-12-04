import Pyro4
import random
import hashlib
import sys
from typing import Union
from Backend.DHT.Utils import Utils
from Backend.DHT.Settings import *
from Pyro4.errors import *

sys.excepthook = Pyro4.util.excepthook

@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Node:
    def __init__(self):
        self._hash = None
        self._finger = None
        self._predecessor = None
        self._logger = None
        self._successor_list = None
        self._proxy = None

        # is node added to DHT
        self._added = False

    @property
    def hash(self):
        return self._hash

    @hash.setter
    def hash(self, h):
        self._hash = h

    @property
    def finger(self):
        return self._finger

    @finger.setter
    def finger(self, finger):
        self._finger = finger

    @property
    def predecessor(self):
        return self._predecessor

    @predecessor.setter
    def predecessor(self, predecessor):
        self._predecessor = predecessor

    @property
    def successor_list(self):
        return self._successor_list

    @successor_list.setter
    def successor_list(self, successor_list):
        self._successor_list = successor_list

    @property
    def added(self):
        return self._added

    @added.setter
    def added(self, added):
        self._added = added

    def initialize(self, hash: int, proxy: Pyro4.Proxy) -> None:
        """
        Initialize node self
        :param hash: hash of node
        :param proxy: proxy that identifies node
        :return: None
        """
        self.hash = hash
        self._proxy = proxy

        self.finger = [None] * LOG_LEN
        self.successor_list = []
        self.predecessor = None

        self._logger = Utils.init_logger("Node h=%d Log" % self.id())

        self.finger[0] = proxy

    def ping(self):
        """
        Is node self alive
        :return: bool
        """
        return True

    def id(self, off: int = 0) -> int:
        """
        Returns id of a self + some offset off
        :param off: offset to add
        :return: int
        """
        return (self.hash + off) % SIZE

    def successor(self) -> Pyro4.Proxy:
        """
        Return successor of node self
        :return: [ Pyro4.Proxy | None ]
        """

        for other in [self.finger[0]] + self.successor_list:
            if other is None:
                continue

            if Utils.ping(other):
                self.finger[0] = other
                return other

        self._logger.error("No successor available :(")

    def find_successor(self, id: int):
        """
        Find successor of id
        :param id: identifier
        :return: Pyro4.Proxy
        """
        self._logger.info("Finding successor of id = %d" % id)

        if (self.predecessor is not None) and \
           Utils.ping(self.predecessor) and \
           NodeUtils.between(id, self.predecessor.id(1), self.id(1)):
            return self

        node = self.find_predecessor(id)

        self._logger.info("Done")
        return node.successor()

    def find_predecessor(self, id: int):
        node = self

        if node.successor().id() == node.id():
            return node

        while not NodeUtils.between(id, node.id(1), node.successor().id(1)):
            node = node.closest_preceding_finger(id)

        return node

    def closest_preceding_finger(self, id: int):
        """
        Returns closest preceding finger from id
        :param id: identifier
        :return: Pyro4.Proxy
        """
        for other in reversed(self.successor_list + self.finger):
            if (other is not None) and Utils.ping(other) and \
               NodeUtils.between(other.id(), self.id(1), id):
                    return other

        return self

    def join(self, other: Pyro4.Proxy) -> None:
        """
        Join to DHT using node other
        :param other: node other
        :return: None
        """
        self._logger.info("Joined to DHT using node other (h = %d)" % other.id())

        self.finger[0] = other.find_successor(self.id())

    def stabilize(self) -> None:
        """
        Stabilize node self
        :return: None
        """
        self._logger.info("stabilizing...")

        succ = self.successor()

        if succ.id() != self.finger[0].id():
            self.finger[0] = succ

        x = succ.predecessor

        if (x is not None) and \
            Utils.ping(x) and \
            NodeUtils.between(x.id(), self.id(1), succ.id()) and \
            self.id(1) != succ.id():
                self.finger[0] = x

        self.successor().notify(self)

    def notify(self, other) -> None:
        """
        Fixing predecessor
        :param other: other node
        :return: None
        """
        self._logger.info("notifying...")

        if self.predecessor is None or \
            not Utils.ping(self.predecessor) or \
            NodeUtils.between(other.id(), self.predecessor.id(1), self.id()):
                self.predecessor = other

    def fix_fingers(self) -> None:
        """
        Fixing fingers of node self
        :return: None
        """
        self._logger.info("fixing fingers...")

        i = random.randint(1, LOG_LEN - 1)
        self.finger[i] = self.find_successor(self.id(1 << i))

    def update_successor_list(self) -> None:
        """
        Updates successor list of self
        :return: None
        """
        self._logger.info("updating successor list....")

        suc = self.successor()

        if suc.id() != self.id():
            successors = [suc]
            suc_list = suc.successor_list[:SUCC_LIST_LEN - 1]

            if suc_list and len(suc_list):
                successors += suc_list

            self.successor_list = successors

class NodeUtils:
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
