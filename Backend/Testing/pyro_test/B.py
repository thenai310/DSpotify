import Pyro4
from Backend.DHT.Node import *

B = Node()

with Pyro4.Daemon() as daemon:
    uri = daemon.register(B)

    print(uri.location)

    B.initialize(5)

    with Pyro4.locateNS() as ns:
        ns.register(str(B.hash), uri)

    daemon.requestLoop()