from Backend.DHT.Node import *
import argparse
import sys
import Pyro4

sys.excepthook = Pyro4.util.excepthook

parser = argparse.ArgumentParser(description="Node creation script")
parser.add_argument("--hash", default=None, type=int, help="Hash value of a node, default is None")
parser.add_argument("--sec", default=None, type=int, help="Seconds to wait before start processing jobs")
args = parser.parse_args()


def register_node(cur_node):
    daemon = Pyro4.Daemon()
    uri = daemon.register(cur_node)

    if args.hash is None:
        cur_node.initialize(Utils.get_hash(uri.location))

    else:
        cur_node.initialize(args.hash)

    print("Node location", uri.location)
    cur_node.debug()

    with Pyro4.locateNS() as ns:
        ns.register("Node:" + str(cur_node.hash), uri)
    print('requesting loop')

    daemon.requestLoop()


if __name__ == "__main__":
    curNode = Node()
    register_node(curNode)
