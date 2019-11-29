import hashlib
from random import randint

LEN = 3 # number of bits in DHT
MOD = 2 ** LEN

class Node:
    def __init__(self, ip: str, port: int, h: int = None):
        """
        :param ip: ip address
        :param port: port
        :param h: hash of node
        """
        self.ip = ip
        self.port = port

        if h is None:
            self.hash = hashlib.sha1((ip + str(port)).encode()).hexdigest()
            self.hash = int(self.hash, 16)

        else: self.hash = h

        #fingertable data
        self.to = [self] * LEN
        self.start = [(self.hash + 2 ** i) % MOD for i in range(LEN)]
        self.predecessor = self

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

        while not Utils.on_interval(id, (x.hash + 1) % MOD, x.to[0].hash):
            x = x.find_closest_pred(id)

        return x

    def find_closest_pred(self, id: int):
        """
        Find node closest predecessor of id
        :param id: identifier
        :return: Node
        """
        for i in reversed(range(LEN)):
            if Utils.on_interval(self.to[i].hash, (self.hash + 1) % MOD, (id - 1) % MOD):
                return self.to[i]

        return self

    def join(self, other):
        """
        Add node self based on info of other
        :param other: Node
        :return: None
        """
        self.init_finger_table(other)
        self.update_others()

        #move keys

    def init_finger_table(self, other):
        """
        Initialize finger table of self based on correct data of other
        :param other: Node
        :return: None
        """
        self.to[0] = other.find_successor(self.to[0].start[0])
        self.predecessor = self.to[0].predecessor
        self.to[0].predecessor = self

        for i in range(1, LEN):
            if Utils.on_interval(self.start[i], self.hash, (self.to[i - 1].hash - 1) % MOD):
                self.to[i] = self.to[i - 1]

            else: self.to[i] = other.find_successor(self.start[i])

    def update_others(self):
        """
        Update all nodes such that self must be in their fingertable
        :return: None
        """
        pw = 1
        for i in range(LEN):
            p = self.find_antecessor((self.hash - pw + 1) % MOD) #check but i think is plus 1
            p.update_finger_table(self, i)
            pw *= 2

    def update_finger_table(self, added, i):
        """
        Update fingertable[i] of node self
        :param added: new node added
        :param i: position in fingertable
        :return: None
        """
        if added.hash != self.hash and Utils.on_interval(added.hash, self.hash, (self.to[i].hash - 1) % MOD):
            self.to[i] = added
            p = self.predecessor
            p.update_finger_table(added, i)

    def stabilize(self):
        """
        fix succesor of node self
        :return: None
        """
        x = self.to[0].predecessor

        if Utils.on_interval(x.hash, (self.hash + 1) % MOD, self.to[0].hash):
            self.to[0] = x

        self.to[0].notify(self)

    def notify(self, other):
        """
        check if node other is predecessor of self
        :param other: None
        :return:
        """
        if Utils.on_interval(other.hash, self.predecessor.hash, (self.hash - 1) % MOD):
            self.predecessor = other

    def fix_to(self):
        """
        fix to array
        :return: None
        """
        i = randint(1, LEN - 1)
        self.to[i] = self.find_successor(self.start[i])

    def __str__(self):
        return "%s:%d, hash = %d" % (self.ip, self.port, self.hash)

    def debug(self):
        print("Node %s" % self.__str__())
        print("start values")
        for i in range(LEN):
            print("i =", i, self.start[i])

        print("succ nodes")
        for i in range(LEN):
            print("i =", i, self.to[i].hash)

        print("----------------------")

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
    def randomIp():
        s = ""

        for i in range(4):
            s += str(randint(0, 255)) + "."

        return s[:-1]

    @staticmethod
    def randomPort():
        return randint(8000, 10000)