from timeloop import Timeloop
from datetime import timedelta
import Pyro4
from Pyro4.errors import *
import argparse
import sys
from Backend.DHT.Utils import Utils

sys.excepthook = Pyro4.util.excepthook

parser = argparse.ArgumentParser(description="Network Worker")
parser.add_argument("--st_time", default=1, type=int, help="How often stabilize each node, default 1s")
parser.add_argument("--ft_time", default=1, type=int, help="How often fix finger table indexes, default 1s")
parser.add_argument("--status_time", default=5, type=int, help="How often fix finger table indexes, default 5s")
args = parser.parse_args()


def get_alive_nodes():
    ns = Pyro4.locateNS()
    return list(ns.list(prefix="Node:").items())


def run_jobs():
    tl = Timeloop()

    @tl.job(timedelta(seconds=1))
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

    @tl.job(timedelta(seconds=args.st_time))
    def jobs():
        logger.info("Running stabilizing, fix_fingers and update successors on all nodes...")

        alive = get_alive_nodes()

        for name, uri in alive:
            try:
                cur_node = Pyro4.Proxy(uri)

                logger.debug("Stabilizing node %s..." % name)
                cur_node.stabilize()
                logger.debug("Done stabilize node h = %d" % cur_node.hash)

                logger.debug("Fixing node %s..." % name)
                cur_node.fix_fingers()
                logger.debug("Done fix fingers node h = %d" % cur_node.hash)

                logger.debug("Updating successors of node h = %d" % cur_node.hash)
                cur_node.update_successor_list()
                logger.debug("Done updating successors list")

            except CommunicationError:
                logger.error("It seems there have been some errors")

        logger.info("Done running all maintenance tasks")

    @tl.job(timedelta(seconds=args.status_time))
    def show_current_status():
        # this is for debugging purposes
        alive = get_alive_nodes()

        for name, uri in alive:
            try:
                cur_node = Pyro4.Proxy(uri)
                logger.debug(Utils.debug_node(cur_node))

            except CommunicationError:
                logger.error("It seems there have been some errors")

    logger.info("Running jobs of stabilize and fix fingers...")
    tl.start(block=True)


if __name__ == "__main__":
    logger = Utils.init_logger("Network Worker Logger")
    logger.info("Network Worker Initialized")
    logger.info("Stabilize frequency = %d, Fix fingers frequency = %d, Status Refreshing time = %d"
                % (args.st_time, args.ft_time, args.status_time))

    run_jobs()
