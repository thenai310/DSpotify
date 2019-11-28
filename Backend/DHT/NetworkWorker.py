from timeloop import Timeloop
from datetime import timedelta
import Pyro4
import argparse
from Backend.DHT.Utils import Utils

parser = argparse.ArgumentParser(description="Network Worker")
parser.add_argument("--st_time", default=1, type=int, help="How often stabilize each node, default 1s")
parser.add_argument("--ft_time", default=1, type=int, help="How often fix finger table indexes, default 1s")
args = parser.parse_args()


def get_alive_nodes():
    ns = Pyro4.locateNS()
    return list(ns.list(prefix="Node:").items())


def build_chord():
    logger.info("Building Chord...")

    alive = get_alive_nodes()

    logger.debug("Alive list")
    for name, uri in alive:
        logger.debug("name=%s, uri=%s" % (name, uri))

    for i in range(1, len(alive)):
        cur_node = Pyro4.Proxy(alive[i][1])
        prv_node = Pyro4.Proxy(alive[i - 1][1])
        cur_node.static_join(prv_node)

    logger.info("Ok just build chord with %d nodes" % len(alive))


def run_jobs():
    logger.info("Running jobs of stabilize and fix fingers...")

    tl = Timeloop()

    @tl.job(timedelta(seconds=args.st_time))
    def stabilize():
        logger.info("Stabilizing all nodes...")

        alive = get_alive_nodes()

        for name, uri in alive:
            cur_node = Pyro4.Proxy(uri)
            cur_node.stabilize()

        logger.info("Done")

    @tl.job(timedelta(seconds=args.ft_time))
    def fix_fingers():
        logger.info("Stabilizing all nodes...")

        alive = get_alive_nodes()

        for name, uri in alive:
            cur_node = Pyro4.Proxy(uri)
            cur_node.fix_to()

        logger.info("Done")


if __name__ == "__main__":
    logger = Utils.init_logger("Network Worker Logger")
    logger.info("Network Worker Initialized")

    build_chord()
    run_jobs()
