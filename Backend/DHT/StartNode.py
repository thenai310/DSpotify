from Backend.DHT.Node import Node
from Backend.DHT.Utils import *
from Backend.DHT.Settings import *
import subprocess
import argparse
import sys
import Pyro4
import os
import time

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook

parser = argparse.ArgumentParser(description="Node creation script")
parser.add_argument("--hash", default=None, type=int, help="Hash value of a node, default is None")
args = parser.parse_args()


def start_socket(h):
    logger.debug("okok starting socket, h = %d" % h)
    subprocess.run(["python3 -m Backend.DHT.Prep_socket --hash " + str(h)], shell=True, universal_newlines=True)


def register_node(cur_node):
    logger.info("Registering node...")

    daemon = Pyro4.Daemon()
    uri = daemon.register(cur_node)

    n = os.fork()

    if n > 0:
        ip = uri.location.split(":")[0]

        assigned_hash = 0

        if args.hash is None:
            cur_node.initialize(Utils.get_hash(uri.location), Pyro4.Proxy(uri), ip)
            assigned_hash = Utils.get_hash(uri.location)

        else:
            cur_node.initialize(args.hash, Pyro4.Proxy(uri), ip)
            assigned_hash = args.hash

        if assigned_hash < 0 or assigned_hash >= SIZE:
            logger.error("Hash of node is not in range [0, SIZE). Exiting ...")
            exit(-1)

        alive = get_alive_nodes()

        for name, uri in alive:
            proxy = Pyro4.Proxy(uri)

            if Utils.ping(proxy):
                if proxy.id() == assigned_hash:
                    logger.error("There exists other node with the same hash. Exiting ...")
                    exit(-1)

        logger.debug("Node location %s" % uri.location)

        with Pyro4.locateNS() as ns:
            ns.register("Node:" + str(cur_node.hash), uri)

        logger.info("Daemon Loop will run now ... Node is waiting for requests!")
        daemon.requestLoop()

    else:
        t = 3
        logger.debug("On child process, waiting %d secs" % t)
        time.sleep(t)

        cur_node = Pyro4.Proxy(uri)
        start_socket(cur_node.hash)


if __name__ == "__main__":
    logger = Utils.init_logger("StartNode Log")
    curNode = Node()
    register_node(curNode)
