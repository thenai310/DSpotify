import random
import argparse
import time
import uuid
from pydub import AudioSegment
from Backend.DHT.Utils import *
from Backend.DHT.Settings import *
from timeloop import Timeloop
from datetime import timedelta

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook


@Pyro4.expose
class SongDownloader:
    def __init__(self, path, chunk_size):
        self.audio = AudioSegment.from_file(path)
        self.chunk_size = chunk_size

    def get_song_data(self):
        return [self.audio.sample_width, self.audio.channels, self.audio.frame_rate]

    def get_song(self, start_time):
        for i in range(start_time, len(self.audio), self.chunk_size):
            segment = self.audio[i:i + self.chunk_size]
            yield segment


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Node:
    def __init__(self, ip, port = 0, hash = None):
        # ip and port of the node
        self.ip = ip
        self.port = port

        if self.port == 0:
            self.port = get_unused_port()

        # node DHT data
        self.finger = [None] * LOG_LEN  # finger table
        self.predecessor = None  # predecessor of node
        self.successor_list = []  # successor list

        # these are songs that the node has locally but they ARE NOT shared
        self.local_songs = set()

        # these are songs that the node has locally too but they ARE shared
        self.shared_songs = set()

        # hash of the node
        self.hash = hash

        if hash is None:
            self.hash = Utils.get_hash(self.ip + ":" + str(self.port))

        # logger of the node
        self.logger = Utils.init_logger("Node h=%d Log" % self.hash)

        self.songs_to_download = []

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
        return self.__ip

    @ip.setter
    def ip(self, ip):
        self.__ip = ip

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, port):
        self.__port = port
        
    ##############################################

    @property
    def finger(self):
        return self.__finger

    @finger.setter
    def finger(self, finger):
        self.__finger = finger

    @property
    def predecessor(self):
        return self.__predecessor

    @predecessor.setter
    def predecessor(self, predecessor):
        self.__predecessor = predecessor

    @property
    def successor_list(self):
        return self.__successor_list

    @successor_list.setter
    def successor_list(self, successor_list):
        self.__successor_list = successor_list

    ##############################################

    @property
    def local_songs(self):
        return self.__local_songs

    @local_songs.setter
    def local_songs(self, local_songs):
        self.__local_songs = local_songs

    @property
    def local_songs_dir_address(self):
        return self.__local_songs_dir_address

    @local_songs_dir_address.setter
    def local_songs_dir_address(self, local_songs_dir_address):
        self.__local_songs_dir_address = local_songs_dir_address

    @property
    def shared_songs_dir_address(self):
        return self.__shared_songs_dir_address

    @shared_songs_dir_address.setter
    def shared_songs_dir_address(self, shared_songs_dir_address):
        self.__shared_songs_dir_address = shared_songs_dir_address

    @property
    def shared_songs(self):
        return self.__shared_songs

    @shared_songs.setter
    def shared_songs(self, shared_songs):
        self.__shared_songs = shared_songs

    @property
    def songs_to_download(self):
        return self.__songs_to_download

    @songs_to_download.setter
    def songs_to_download(self, songs_to_download):
        self.__songs_to_download = songs_to_download

    ##############################################
    
    @property
    def hash(self):
        return self.__hash

    @hash.setter
    def hash(self, h):
        self.__hash = h

    ##############################################

    def download_song(self, song_name, chunk_size):
        if not self.is_song_available(song_name):
            return

        all_songs = self.get_all_songs()

        path = ""

        for song in all_songs:
            if song.name == song_name:
                path = song.full_path
                break

        downloader = SongDownloader(path, chunk_size)
        self._pyroDaemon.register(downloader)
        return downloader

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
        # this is called at register_node method, also is
        # called in successor method in case it does not find
        # a successor
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

        self.logger.error("No successor available :(, setting self as successor")
        self.set_succesor_as_self()

    def find_successor(self, id: int):
        """
        Find successor of id
        :param id: identifier
        :return: Pyro4.Proxy
        """

        if (self.predecessor is not None) and \
           Utils.ping(self.predecessor) and \
           Utils.between(id, self.predecessor.id(1), self.id(1)):
            return self

        node = self.find_predecessor(id)

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

        if Utils.ping(other) and other.id() == self.id():
            return None

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

        cur_node.logger.info("Downloading songs I need")
        for data in cur_pyro_node.songs_to_download:
            cur_node.logger.info("name = %s" % data[0])

        for data in cur_pyro_node.songs_to_download:
            song_name = data[0]
            song_hash = data[1]
            node = data[2]

            if not Utils.ping(node):
                continue

            path = cur_pyro_node.shared_songs_dir_address + "/" + song_name

            if not DEBUG_MODE:
                # test!
                cur_node.logger.info("Ok node h=%d has the song %s, starting comunication..." % (node.hash, song_name))

                downloader = node.download_song(song_name, CHUNK_LENGTH_SERVER)

                audio = AudioSegment.empty()
                gen = downloader.get_song(0)

                for i, segment in enumerate(gen):
                    cur_node.logger.info(f"Recieving segment number {i}")
                    audio += segment

                audio.export(path)

            cur_song = Song(path, song_name, song_hash)

            cur_set = node.shared_songs
            cur_set.add(cur_song)
            node.shared_songs = cur_set

        cur_pyro_node.songs_to_download = []

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

                    lst = node.songs_to_download
                    lst.append((song_name, song_hash, node))
                    node.songs_to_download = lst

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

            if not DEBUG_MODE:
                os.remove(song.full_path)

        cur_node.logger.info("Done distributing songs")

    cur_node.logger.info("Maintenaince jobs will run now....")
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
            auto_connect()

        else:
            run_jobs()
