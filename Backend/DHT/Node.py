import random
import argparse
import os
import threading
import time
import Pyro4
import uuid
import zmq
from pydub import AudioSegment
from Backend.DHT.Utils import *
from Backend.DHT.Settings import *
from timeloop import Timeloop
from datetime import timedelta

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Node:
    def __init__(self, ip, port = 0, hash = None):
        # ip and port of the node
        self._ip = ip
        self._port = port

        if self._port == 0:
            self._port = get_unused_port()

        # node DHT data
        self._finger = [None] * LOG_LEN  # finger table
        self._predecessor = None  # predecessor of node
        self._successor_list = []  # successor list

        # these are songs that the node has locally but they ARE NOT shared
        self._local_songs = set()

        # these are songs that the node has locally too but they ARE shared
        self._shared_songs = set()

        # port of the socket that is running on the node,
        # will be initialized when the socket is up and running
        self._port_socket = None

        # hash of the node
        self._hash = hash

        if hash is None:
            self._hash = Utils.get_hash(self._ip + ":" + str(self._port))

        # logger of the node
        self.logger = Utils.init_logger("Node h=%d Log" % self._hash)

        unique_identifier = str(uuid.uuid1())
        address = os.getcwd() + "/Song_Data/" + unique_identifier

        self.local_songs_dir_address = address + "/local_songs"
        self.shared_songs_dir_address = address + "/shared_songs"


        os.mkdir(address)
        os.mkdir(self.local_songs_dir_address)
        os.mkdir(self.shared_songs_dir_address)

        if DEBUG_MODE:
            os.system("cp songs_small/*.mp3 %s" % self.local_songs_dir_address)

    ##############################################
    
    @property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, ip):
        self._ip = ip

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        self._port = port
        
    ##############################################

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

    ##############################################

    @property
    def local_songs(self):
        return self._local_songs

    @local_songs.setter
    def local_songs(self, local_songs):
        self._local_songs = local_songs

    @property
    def shared_songs(self):
        return self._shared_songs

    @shared_songs.setter
    def shared_songs(self, shared_songs):
        self._shared_songs = shared_songs

    ##############################################

    @property
    def port_socket(self):
        return self._port_socket

    @port_socket.setter
    def port_socket(self, port_socket):
        self._port_socket = port_socket

    ##############################################
    
    @property
    def hash(self):
        return self._hash

    @hash.setter
    def hash(self, h):
        self._hash = h

    ##############################################

    # this is for loading the local songs
    # returns a set of tuples (dir, name)
    def load_local_songs(self):
        return get_local_songs_tuple_set(self.local_songs_dir_address)

    def get_all_songs(self):
        return self.local_songs | self.shared_songs

    def is_song_available(self, song_name):
        all_songs = self.get_all_songs()

        for song in all_songs:
            if song.name == song_name:
                return True

        return False

    def set_succesor_as_self(self):
        # setting successor initially to a proxy of self
        # this is called at register_node method
        self.finger[0] = Pyro4.Proxy("PYRONAME:Node:" + str(self.hash))

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

        self.logger.error("No successor available :(")

    def find_successor(self, id: int):
        """
        Find successor of id
        :param id: identifier
        :return: Pyro4.Proxy
        """
        self.logger.info("Finding successor of id = %d" % id)

        if (self.predecessor is not None) and \
           Utils.ping(self.predecessor) and \
           Utils.between(id, self.predecessor.id(1), self.id(1)):
            return self

        node = self.find_predecessor(id)

        self.logger.info("Done")
        return node.successor()

    def find_predecessor(self, id: int):
        node = self

        if node.successor().id() == node.id():
            return node

        while not Utils.between(id, node.id(1), node.successor().id(1)):
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
               Utils.between(other.id(), self.id(1), id):
                    return other

        return self

    def join(self, other: Pyro4.Proxy) -> None:
        """
        Join to DHT using node other
        :param other: node other
        :return: None
        """
        self.logger.info("Joined to DHT using node other (h = %d)" % other.id())

        self.finger[0] = other.find_successor(self.id())

    def stabilize(self) -> None:
        """
        Stabilize node self
        :return: None
        """
        self.logger.info("stabilizing...")

        succ = self.successor()

        if succ.id() != self.finger[0].id():
            self.finger[0] = succ

        x = succ.predecessor

        if (x is not None) and \
            Utils.ping(x) and \
            Utils.between(x.id(), self.id(1), succ.id()) and \
            self.id(1) != succ.id():
                self.finger[0] = x

        self.successor().notify(self)

    def notify(self, other) -> None:
        """
        Fixing predecessor
        :param other: other node
        :return: None
        """
        self.logger.info("notifying...")

        if self.predecessor is None or \
            not Utils.ping(self.predecessor) or \
            Utils.between(other.id(), self.predecessor.id(1), self.id()):
                self.predecessor = other

    def fix_fingers(self) -> None:
        """
        Fixing fingers of node self
        :return: None
        """
        self.logger.info("fixing fingers...")

        i = random.randint(1, LOG_LEN - 1)
        self.finger[i] = self.find_successor(self.id(1 << i))

    def update_successor_list(self) -> None:
        """
        Updates successor list of self
        :return: None
        """
        self.logger.info("updating successor list....")

        suc = self.successor()

        if suc.id() != self.id():
            successors = [suc]
            suc_list = suc.successor_list[:SUCC_LIST_LEN - 1]

            if suc_list and len(suc_list):
                successors += suc_list

            self.successor_list = successors


class ThreadedServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.logger = Utils.init_logger("Socket Logger")

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            client.settimeout(60)
            threading.Thread(target = self.listen_to_client,args = (client,address)).start()

    def listen_to_client(self, client, address):
        while True:
            try:
                self.manage_client(client, address)
            except EOFError:
                break

    def manage_client(self, sock, addr):
        song_name = recieve(sock)

        self.logger.info("Sending song %s to client %s" % (song_name, addr))

        all_songs = cur_pyro_node.get_all_songs()

        full_path = ""
        for song in all_songs:
            if song.name == song_name:
                full_path = song.full_path
                break

        self.logger.info("Loading audio ....")

        audio = AudioSegment.from_file(full_path)

        self.logger.debug("Audio len = %d" % len(audio))

        self.logger.info("Sending...")
        send(sock, audio)

def register_node():
    cur_node.logger.info("Registering node...")

    daemon = Pyro4.Daemon(cur_node.ip, cur_node.port)
    uri = daemon.register(cur_node)

    if cur_node.hash < 0 or cur_node.hash >= SIZE:
        cur_node.logger.error("Hash of node is not in range [0, SIZE). Exiting ...")
        exit(-1)

    alive = get_alive_nodes()

    for name, _uri in alive:
        proxy = Pyro4.Proxy(_uri)

        if Utils.ping(proxy):
            if proxy.hash == cur_node.hash:
                cur_node.logger.error("There exists other node with the same hash. Exiting ...")
                exit(-1)

    cur_node.logger.debug("Node location %s" % uri.location)

    with Pyro4.locateNS() as ns:
        ns.register("Node:" + str(cur_node.hash), uri)

    cur_node.set_succesor_as_self()

    cur_node.logger.info("Daemon Loop will run now ... Node is waiting for requests!")

    daemon.requestLoop()


def auto_connect():
    cur_node.logger.info("Autoconnecting...")

    connected = False

    while True:
        alive = get_alive_nodes()

        for name, uri in alive:
            if name != "Node:" + str(cur_node.hash):
                try:
                    other_node = Pyro4.Proxy(uri)

                    cur_node.logger.info("Trying to connect with h = %d" % other_node.hash)

                    cur_pyro_node = Pyro4.Proxy("PYRONAME:Node:" + str(cur_node.hash))
                    cur_pyro_node.join(other_node)

                    connected = True

                    cur_node.logger.info("Connected succesfully to node h = %d" % other_node.hash)
                    return None

                except CommunicationError:
                    pass

        if not connected:
            cur_node.logger.error("Autoconnecting didnt work, maybe it is the only node on the network?")

        time.sleep(1)


def run_jobs():
    tl = Timeloop()

    @tl.job(timedelta(seconds=MAINTENANCE_JOBS_TIME))
    def jobs():
        cur_node.logger.info("Running stabilizing, fix_fingers and update successors on all nodes...")

        cur_pyro_node = Pyro4.Proxy("PYRONAME:Node:" + str(cur_node.hash))

        cur_node.logger.debug("Stabilizing node h=%d..." % cur_node.hash)
        cur_pyro_node.stabilize()
        cur_node.logger.debug("Done stabilize node h=%d" % cur_node.hash)

        cur_node.logger.debug("Fixing node h=%d..." % cur_node.hash)
        cur_pyro_node.fix_fingers()
        cur_node.logger.debug("Done fix fingers node h=%d" % cur_node.hash)

        cur_node.logger.debug("Updating successors of node h=%d" % cur_node.hash)
        cur_pyro_node.update_successor_list()
        cur_node.logger.debug("Done updating successors list")

        cur_node.logger.info("Done running all maintenance tasks")

    @tl.job(timedelta(seconds=SHOW_CURRENT_STATUS_TIME))
    def show_current_status():
        cur_pyro_node = Pyro4.Proxy("PYRONAME:Node:" + str(cur_node.hash))
        cur_node.logger.debug(Utils.debug_node(cur_pyro_node))

    @tl.job(timedelta(seconds=DISTRIBUTE_SONGS_TIME))
    def distribute_songs():
        cur_node.logger.info("Distributing songs ...")
        cur_node.logger.info("Refreshing local songs...")

        cur_pyro_node = Pyro4.Proxy("PYRONAME:Node:" + str(cur_node.hash))
        song_set = cur_pyro_node.load_local_songs()

        for song_dir, song_name in song_set:
            song_hash = Utils.get_hash(song_name)

            if DEBUG_MODE:
                song_hash = int(song_name.split(".")[0])

            succ = cur_pyro_node.find_successor(song_hash)
            cur_song = Song(song_dir + "/" + song_name, song_name, song_hash)

            cur_set = cur_pyro_node.local_songs
            cur_set.add(cur_song)
            cur_pyro_node.local_songs = cur_set

            for node in succ.successor_list:
                if Utils.ping(node):
                    cur_node.logger.info("Adding local song %s to node h=%d" % (song_name, node.hash))

                    if cur_song in node.shared_songs:
                        continue

                    cur_set = node.shared_songs
                    cur_set.add(cur_song)
                    node.shared_songs = cur_set

                    # copy song!
                    # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    #     try:
                    #         sock.connect((node.ip, node.port_socket))
                    #
                    #         send(sock, TRANSFER)
                    #
                    #         audio = AudioSegment.from_file(cur_song.full_path)
                    #         send(sock, audio)
                    #     except (OSError, PyroError):
                    #         # node is down
                    #         pass


        cur_node.logger.info("Refreshing shared songs...")

        to_remove = set()
        for song in cur_pyro_node.shared_songs:
            succ = cur_pyro_node.find_successor(song.hash)

            found_self = False
            for node in succ.successor_list:
                if Utils.ping(node) and node.hash == cur_pyro_node.hash:
                    found_self = True

            if not found_self:
                to_remove.add(song)

        for song in to_remove:
            cur_node.logger.info("Deleting shared song %s from node self"
                                 "because it doesn't belong there anymore" % song.name)

            cur_set = cur_pyro_node.shared_songs
            cur_set.remove(song)
            cur_pyro_node.shared_songs = cur_set

            # OJOOOOOOOOO
            # hay q fisicamente borrar la cancion song de cur_pyro_node
            # idea tener dos carpetas una para las canciones locales, otra para las compartidas
            # ojo dentro de cada carpeta no hay duplicados pero una cancion x puede estar en local
            # y shared a la vez, no es problema

        cur_node.logger.info("Done distributing songs")

    # cur_node.logger.info("Maintenaince jobs will run now....")
    distribute_songs()
    tl.start(block=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Node creation script")
    parser.add_argument("--ip", default="127.0.0.1", type=str, help="IP address of a node, default is 127.0.0.1")
    parser.add_argument("--port", default=0, type=int, help="Port of node, default is 0 which means random port")
    parser.add_argument("--hash", default=None, type=int, help="Hash value of a node, default is None")
    args = parser.parse_args()

    cur_node = Node(args.ip, args.port, args.hash)

    # node will register as Pyro Daemon with args.ip and args.port as location

    if os.fork() > 0:
        # parent process
        register_node()

    else:
        time.sleep(2)

        if os.fork() > 0:
            server = ThreadedServer(cur_node.ip, get_unused_port())

            cur_pyro_node = Pyro4.Proxy("PYRONAME:Node:" + str(cur_node.hash))
            cur_pyro_node.port_socket = server.port
            cur_node.port_socket = server.port

            server.logger.info("Server for transfer songs of node is running at %s:%d" % (server.host, server.port))
            server.listen()

        else:
            if os.fork() > 0:
                auto_connect()

            else:
                run_jobs()
