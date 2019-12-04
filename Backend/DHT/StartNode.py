from Backend.DHT.Node import Node, NodeUtils
from Backend.DHT.Utils import Utils
import argparse
import sys
import Pyro4
from Pyro4.errors import *

sys.excepthook = Pyro4.util.excepthook

parser = argparse.ArgumentParser(description="Node creation script")
parser.add_argument("--hash", default=None, type=int, help="Hash value of a node, default is None")
args = parser.parse_args()


def auto_connect(ns, cur_node):
    logger.info("Autoconnecting...")

    connected = False
    for name, uri in ns.list(prefix="Node:").items():
        if name != "Node:" + str(cur_node.hash):
            try:
                other_node = Pyro4.Proxy(uri)
                logger.info("Trying to connect with h = %d" % other_node.hash)
                cur_node.join(other_node)
                connected = True
                logger.info("Connected succesfully to node h = %d" % other_node.hash)
                break

            except CommunicationError:
                pass

    if not connected:
        logger.error("Autoconnecting didnt work, maybe it is the only node on the network?")


def register_node(cur_node):
    logger.info("Registering node...")

    daemon = Pyro4.Daemon()
    uri = daemon.register(cur_node)

    if args.hash is None:
        cur_node.initialize(NodeUtils.get_hash(uri.location), Pyro4.Proxy(uri))

    else:
        cur_node.initialize(args.hash, Pyro4.Proxy(uri))

    logger.debug("Node location %s" % uri.location)

    with Pyro4.locateNS() as ns:
        ns.register("Node:" + str(cur_node.hash), uri)

    # auto_connect(ns, cur_node)

    logger.info("Daemon Loop will run now ... Node is waiting for requests!")
    daemon.requestLoop()


if __name__ == "__main__":
    logger = Utils.init_logger("StartNode Log")
    curNode = Node()
    register_node(curNode)
