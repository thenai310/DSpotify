from Backend.DHT.Node import *
import argparse
import sys
from timeloop import Timeloop
from datetime import timedelta

sys.excepthook = Pyro4.util.excepthook

parser = argparse.ArgumentParser(description="Node creation script")
parser.add_argument("--hash", default=None, type=int, help="Hash value of a node, default is None")
parser.add_argument("--sec", default=None, type=int, help="Seconds to wait before start processing jobs")
args = parser.parse_args()

def register_node(curNode):
    daemon = Pyro4.Daemon()
    uri = daemon.register(curNode)

    if args.hash is None:
        curNode.initialize(Utils.get_hash(uri.location))

    else:
        curNode.initialize(args.hash)

    print("Node location", uri.location)
    curNode.debug()

    with Pyro4.locateNS() as ns:
        ns.register("Node:" + str(curNode.hash), uri)

    run_jobs(curNode)

    print('requesting loop')
    daemon.requestLoop()


def run_jobs(curNode):
    def connect_node():
        print("Try joining to the DHT", flush=True)

        tl = Timeloop()

        @tl.job(timedelta(seconds=0.5))
        def try_connect():
            ns = Pyro4.locateNS()
            alive = list(ns.list(prefix="Node:").items())

            print("Alive list")
            for name, uri in alive:
                print(name, uri)
            print("------------------------")

            for name, uri in alive:
                if name != "Node:" + str(curNode.hash):
                    otherNode = Pyro4.Proxy(uri)
                    print('try doing join kkk')
                    curNode.join(otherNode)
                    print('join completed')
                    # tl.stop()

            print(".", end="", flush=True)

        tl.start(block=True)
        print("Joined succesfully", flush=True)

    # time.sleep(args.sec)
    connect_node()

if __name__ == "__main__":
    curNode = Node() #instance of node
    register_node(curNode)