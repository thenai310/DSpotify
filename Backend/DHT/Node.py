import Pyro4
import random
import hashlib
from Backend.DHT.Utils import Utils

LEN = 3  # number of bits in DHT
MOD = 2 ** LEN


@Pyro4.expose
class Node:
    def __init__(self):
        self._hash = None
        self._to = None
        self._start = None
        self._predecessor = None
        self._logger = None

    @property
    def hash(self):
        return self._hash

    @hash.setter
    def hash(self, h):
        self._hash = h

    @property
    def to(self):
        return self._to

    @to.setter
    def to(self, to):
        self._to = to

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start

    @property
    def predecessor(self):
        return self._predecessor

    @predecessor.setter
    def predecessor(self, predecessor):
        self._predecessor = predecessor

    def initialize(self, h: int, proxy: Pyro4.Proxy):
        """
        :param h: hash of node
        """
        self.hash = h

        # fingertable data
        # this is fingertable it contains Proxies for each node from
        self.to = [proxy] * LEN
        self.start = [(self.hash + 2 ** i) % MOD for i in range(LEN)]
        self.predecessor = proxy # also proxy

        self._logger = Utils.init_logger('Node %d Log' % self.hash)

    def find_successor(self, id: int):
        """
        Find succesor of identifier id
        :param id: identifier
        :return: Node
        """
        return self.find_antecessor(id).to[0]

    def find_antecessor(self, id: int):
        """
        Find antecessor of identifier id
        :param id: identifier
        :return: Node
        """

        x = self

        while not NodeUtils.on_interval(id, (x.hash + 1) % MOD, x.to[0].hash):
            x = x.find_closest_pred(id)

        return x

    def find_closest_pred(self, id: int):
        """
        Find node closest predecessor of id
        :param id: identifier
        :return: Node
        """

        for i in reversed(range(LEN)):
            if NodeUtils.on_interval(self.to[i].hash, (self.hash + 1) % MOD, (id - 1) % MOD):
                return self.to[i]

        return self

    def dynamic_join(self, other):
        self.to[0] = other.find_successor(self.hash)

    def stabilize(self):
        """
        fix succesor of node self
        :return: None
        """
        x = self.to[0].predecessor

        if NodeUtils.on_interval(x.hash, (self.hash + 1) % MOD, self.to[0].hash):
            self.to[0] = x

        self.to[0].notify(self)

    def notify(self, other):
        """
        check if node other is predecessor of self
        :param other: None
        :return:
        """
        if NodeUtils.on_interval(other.hash, self.predecessor.hash, (self.hash - 1) % MOD):
            self.predecessor = other

    def fix_to(self):
        """
        fix to array
        :return: None
        """
        i = random.randint(1, LEN - 1)
        self.to[i] = self.find_successor(self.start[i])

    def __str__(self):
        return "hash = %d" % self.hash

    def debug(self):
        print("Node %s" % self.__str__())
        print("start values")
        for i in range(LEN):
            print("i =", i, self.start[i])

        print("succ nodes")
        for i in range(LEN):
            print("i =", i, self.to[i].hash)

        print("----------------------")


class NodeUtils:
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

        return NodeUtils.on_interval(x, a, MOD - 1) or NodeUtils.on_interval(x, 0, b)

    @staticmethod
    def get_hash(location: str):
        h = hashlib.sha1(location.encode()).hexdigest()
        h = int(h, 16)
        return h
