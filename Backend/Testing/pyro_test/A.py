import Pyro4
from Backend.DHT.Node import *

A = Node()

with Pyro4.Daemon() as daemon:
    uri = daemon.register(A)

    print(uri.location)

    A.initialize(Utils.get_hash(uri.location))

    with Pyro4.locateNS() as ns:
        ns.register(str(A.hash), uri)

    daemon.requestLoop()