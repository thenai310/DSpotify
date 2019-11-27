from timeloop import Timeloop
from datetime import timedelta
import Pyro4
import argparse

parser = argparse.ArgumentParser(description="Network Worker")
parser.add_argument("--st_time", default=1, type=int, help="How often stabilize each node, default 1s")
parser.add_argument("--ft_time", default=1, type=int, help="How often fix finger table indexes, default 1s")
args = parser.parse_args()

def get_alive_nodes():
    ns = Pyro4.locateNS()
    return list(ns.list(prefix="Node:").items())


def build_chord():
    alive = get_alive_nodes()

    print("Alive list")
    for name, uri in alive:
        print(name, uri)
    print("------------------------")

    for i in range(1, len(alive)):
        cur_node = Pyro4.Proxy(alive[i][1])
        prv_node = Pyro4.Proxy(alive[i - 1][1])
        cur_node.static_join(prv_node)


def run_jobs():
    tl = Timeloop()

    @tl.job(timedelta(seconds=args.st_time))
    def stabilize():
        alive = get_alive_nodes()

        for name, uri in alive:
            cur_node = Pyro4.Proxy(uri)
            cur_node.stabilize()

    @tl.job(timedelta(seconds=args.ft_time))
    def fix_fingers():
        alive = get_alive_nodes()

        for name, uri in alive:
            cur_node = Pyro4.Proxy(uri)
            cur_node.fix_to()


if __name__ == "__main__":
    build_chord()
    run_jobs()
