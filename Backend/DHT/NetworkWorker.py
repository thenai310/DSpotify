from timeloop import Timeloop
from datetime import timedelta
import Pyro4
import os
from Backend.DHT.Settings import *
import sys, time
from Backend.DHT.Utils import Utils
from Backend.DHT.Song import Song

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook


def get_alive_nodes():
    ns = Pyro4.locateNS()
    return list(ns.list(prefix="Node:").items())


def run_jobs():
    tl = Timeloop()

    @tl.job(timedelta(seconds=JOIN_NODES_TIME))
    def join_nodes():
        logger.info("ok looking for new nodes to join...")
        alive = get_alive_nodes()

        logger.debug(alive)

        someone_in_dht = None
        to_join = []

        for name, uri in alive:
            proxy = Pyro4.Proxy(uri)

            if Utils.ping(proxy):
                if proxy.added:
                    someone_in_dht = proxy

                else:
                    to_join.append(proxy)

        cnt = len(to_join)

        if not someone_in_dht:
            someone_in_dht = to_join[-1]
            to_join = to_join[:-1]

        someone_in_dht.added = True

        for node in to_join:
            node.join(someone_in_dht)
            node.added = True

        logger.info("done, joined %d nodes" % cnt)

    @tl.job(timedelta(seconds=MAINTENANCE_JOBS_TIME))
    def jobs():
        logger.info("Running stabilizing, fix_fingers and update successors on all nodes...")

        alive = get_alive_nodes()

        for name, uri in alive:
            cur_node = Pyro4.Proxy(uri)

            if Utils.ping(cur_node):
                logger.debug("Stabilizing node %s..." % name)
                cur_node.stabilize()
                logger.debug("Done stabilize node h = %d" % cur_node.hash)

                logger.debug("Fixing node %s..." % name)
                cur_node.fix_fingers()
                logger.debug("Done fix fingers node h = %d" % cur_node.hash)

                logger.debug("Updating successors of node h = %d" % cur_node.hash)
                cur_node.update_successor_list()
                logger.debug("Done updating successors list")

        logger.info("Done running all maintenance tasks")

    def get_songs_set():
        s = set()

        for (dir, _, files) in os.walk(SONGS_DIRECTORY):
            for name in files:
                s.add((dir, name))

        return s

    @tl.job(timedelta(seconds=DISTRIBUTE_SONGS_TIME))
    def distribute_songs():
        logger.info("Distributing songs...")

        alive = get_alive_nodes()

        for name, uri in alive:
            node = Pyro4.Proxy(uri)

            if Utils.ping(node):
                # clearing songs
                node.songs = set()
                logger.debug(type(node.songs))

        songs = get_songs_set()

        for song_dir, song_name in songs:
            song_hash = Utils.get_hash(song_name)

            if DEBUG_MODE:
                song_hash = int(song_name[0])

            proxy = None

            for name, uri in alive:
                node = Pyro4.Proxy(uri)

                if Utils.ping(node):
                    proxy = node
                    break

            if proxy is None:
                # try again later, altough this should not happen
                return None

            succ = proxy.find_successor(song_hash)
            ext_succ_list = [succ] + succ.successor_list[:-1]

            cur_song = Song(song_dir + song_name, song_name, song_hash)

            for node in ext_succ_list:
                if Utils.ping(node):
                    logger.debug("appending to node %d" % node.id())
                    song_list = node.songs
                    song_list.add(cur_song)
                    node.songs = song_list

        logger.info("Done distributing songs")


    @tl.job(timedelta(seconds=SHOW_CURRENT_STATUS_TIME))
    def show_current_status():
        # this is for debugging purposes
        alive = get_alive_nodes()

        for name, uri in alive:
            cur_node = Pyro4.Proxy(uri)

            if Utils.ping(cur_node):
                logger.debug(Utils.debug_node(cur_node))

    logger.info("Running jobs of stabilize and fix fingers...")
    tl.start(block=True)


if __name__ == "__main__":
    logger = Utils.init_logger("Network Worker Logger")
    logger.info("Network Worker Initialized")

    run_jobs()
