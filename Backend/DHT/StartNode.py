from Backend.DHT.Node import Node
from Backend.DHT.Utils import Utils
import argparse
import sys
import Pyro4

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook

parser = argparse.ArgumentParser(description="Node creation script")
parser.add_argument("--hash", default=None, type=int, help="Hash value of a node, default is None")
args = parser.parse_args()


def register_node(cur_node):
    logger.info("Registering node...")

    daemon = Pyro4.Daemon()
    uri = daemon.register(cur_node)

    ip = uri.location.split(":")[0]

    if args.hash is None:
        cur_node.initialize(Utils.get_hash(uri.location), Pyro4.Proxy(uri), ip)

    else:
        cur_node.initialize(args.hash, Pyro4.Proxy(uri), ip)

    logger.debug("Node location %s" % uri.location)

    with Pyro4.locateNS() as ns:
        ns.register("Node:" + str(cur_node.hash), uri)

    logger.info("Daemon Loop will run now ... Node is waiting for requests!")
    daemon.requestLoop()


if __name__ == "__main__":
    logger = Utils.init_logger("StartNode Log")
    curNode = Node()
    register_node(curNode)
