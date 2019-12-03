import Pyro4
import random
import hashlib
import copy
from Pyro4.errors import *
from Backend.DHT.Utils import Utils
from Backend.DHT.Settings import *


@Pyro4.expose
class Node:
    def __init__(self):
        self._hash = None
        self._to = None
        self._start = None
        self._predecessor = None
        self._logger = None
        self._succesor_list = None

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

    @property
    def succesor_list(self):
        return self._succesor_list

    @succesor_list.setter
    def succesor_list(self, succesor_list):
        self._succesor_list = succesor_list

    def get_succesor(self):
        return self.succesor_list[0]

    def initialize(self, h: int, proxy: Pyro4.Proxy):
        """
        :param h: hash of node
        """
        self.hash = h

        # fingertable data
        # this is fingertable it contains Proxies for each node from
        self.to = [proxy] * LEN
        self.to[0] = None

        self.start = [(self.hash + 2 ** i) % MOD for i in range(LEN)]

        self.predecessor = proxy

        # succesor list
        self.succesor_list = [None] * SUCC_LIST_LEN

        self._logger = Utils.init_logger('Node %d Log' % self.hash)

    def find_successor(self, id: int):
        """
        Find succesor of identifier id
        :param id: identifier
        :return: Node
        """
        return self.find_antecessor(id).get_succesor()

    def find_antecessor(self, id: int):
        """
        Find antecessor of identifier id
        :param id: identifier
        :return: Node
        """

        x = self

        while not NodeUtils.on_interval(id, (x.hash + 1) % MOD, x.get_succesor().hash):
            x = x.find_closest_pred(id)

        return x

    def find_closest_pred(self, id: int):
        """
        Find node closest predecessor of id
        :param id: identifier
        :return: Node
        """

        for i in reversed(range(LEN)):
            if i == 0:
                node = self.get_succesor()

            else:
                node = self.to[i]

            if NodeUtils.between(node.hash, self.hash, id):
                return node

        return self

    def dynamic_join(self, other):
        new_succ = other.find_successor(self.hash)
        succ_list = new_succ.succesor_list.copy()
        self.succesor_list = [new_succ] + succ_list[:-1]

    def stabilize(self):
        """
        fix succesor of node self
        :return: None
        """

        self._logger.debug(Utils.debug_node(self))

        for i in range(SUCC_LIST_LEN):
            try:
                cur_node = self.succesor_list[i]
            except CommunicationError:
                continue

            new_succ = cur_node.predecessor

            succ_list = cur_node.succesor_list.copy()
            succ_list = [cur_node] + succ_list[:-1]

            try:
                self._logger.debug("new succ hash = %d, self hash = %d, cur hash = %d" % (new_succ.hash, self.hash, cur_node.hash))
                self._logger.debug(Utils.debug_node(new_succ))

                if NodeUtils.between(new_succ.hash, self.hash, cur_node.hash):
                    succ_list = new_succ.succesor_list.copy()
                    succ_list = [new_succ] + succ_list[:-1]

            except CommunicationError:
                pass

            self.succesor_list = succ_list

            try:
                cur_node.notify(self)
            except CommunicationError:
                pass

            break

    def notify(self, other):
        """
        check if node new_pred is predecessor of self
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
    def between(x: int, a: int, b: int):
        if a < b:
            return a < x < b

        else:
            return a < x or x < b

    @staticmethod
    def get_hash(location: str):
        h = hashlib.sha1(location.encode()).hexdigest()
        h = int(h, 16)
        return h
