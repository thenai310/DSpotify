import Pyro4
import random
import hashlib
import sys
from Backend.DHT.Utils import Utils
from Backend.DHT.Settings import *
from Pyro4.errors import *

sys.excepthook = Pyro4.util.excepthook

@Pyro4.expose
class Node:
    def __init__(self):
        self._hash = None
        self._finger = None
        self._predecessor = None
        self._logger = None
        self._succesor_list = None
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
    def succesor_list(self):
        return self._succesor_list

    @succesor_list.setter
    def succesor_list(self, succesor_list):
        self._succesor_list = succesor_list

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
        self.succesor_list = [None] * SUCC_LIST_LEN
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
        Return succesor of node self
        :return: [ Pyro4.Proxy | None ]
        """

        self._logger.debug("in successor function")

        for other in [self.finger[0]] + self.succesor_list:
            if other is None:
                continue

            self._logger.debug("ok in node other trying doing ping... %d" % other.hash)
            try:
                Utils.ping(other)
            except PyroError:
                pass
            self._logger.debug("ok ping done")

            if Utils.ping(other):
                self._logger.debug("ok succ is other = %d" % other.id())
                self.finger[0] = other
                return other

        self._logger.error("No successor available :(")

    def find_successor(self, id: int) -> Pyro4.Proxy:
        """
        Find succesor of id
        :param id: identifier
        :return: Pyro4.Proxy
        """
        self._logger.info("Finding successor of id = %d" % id)

        self._logger.debug("pinging self res = %s" % Utils.ping(self.finger[0]))

        if (self.predecessor is not None) and \
           Utils.ping(self.predecessor) and \
           NodeUtils.between(id, self.predecessor.id(1), self.id(1)):
            return self._proxy

        self._logger.debug("finding predecessor")
        node = self.find_predecessor(id)

        self._logger.info("Done")
        return node.succesor()

    def find_predecessor(self, id: int) -> Pyro4.Proxy:
        self._logger.debug("here finding predecessor")
        node = self._proxy
        self._logger.debug("node here it is!!")

        self._logger.debug("type succ %s" % type(node.finger[0]))

        if node.successor().id() == node.id():
            return node

        self._logger.debug("finding antecessor of id=%d" % id)

        while not NodeUtils.between(id, node.id(1), node.succesor().id(1)):
            self._logger.debug("cur node h = %d" % node.id())
            node = node.closest_preceding_finger(id)

        return node

    def closest_preceding_finger(self, id: int) -> Pyro4.Proxy:
        """
        Returns closest preceding finger from id
        :param id: identifier
        :return: Pyro4.Proxy
        """
        for other in reversed(self.succesor_list + self.finger):
            if (other is not None) and Utils.ping(other) and \
               NodeUtils.between(other.id(), self.id(1), id):
                    return other

        return self._proxy

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

        succ = self.succesor()

        if succ.id() != self.finger[0].id():
            self.finger[0] = succ

        x = succ.predecessor()

        if (x is not None) and \
            Utils.ping(x) and \
            NodeUtils.between(x.id(), self.id(1), succ.id()) and \
            self.id(1) != succ.id():
                self.finger[0] = x

        self.succesor().notify(self)

    def notify(self, other) -> None:
        """
        Fixing predecessor
        :param other: other node
        :return: None
        """
        self._logger.info("notifying...")

        if self.predecessor is None or \
            not self.predecessor.ping() or \
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

        suc = self.succesor()

        if suc.id() != self.id():
            successors = [suc]
            suc_list = self.successor_list[:SUCC_LIST_LEN - 1]

            if suc_list and len(suc_list):
                successors += suc_list

            self.succesor_list = successors

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
