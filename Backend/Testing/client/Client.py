import Pyro4
from Pyro4.errors import *
import sys
from Backend.DHT.Utils import Utils

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook


def get_alive_nodes():
    ns = Pyro4.locateNS()
    return list(ns.list(prefix="Node:").items())


def get_song_list():
    alive = get_alive_nodes()

    songs = set()

    for name, uri in alive:
        node = Pyro4.Proxy(uri)

        if Utils.ping(node):
            songs |= node.songs

    return songs


def show_song_list():
    songs = list(get_song_list())

    print("This are all the songs on the server")

    for i, song in enumerate(songs):
        print("%d- %s" % (i, song.name))
    print()

    option = 0

    while True:
        try:
            option = int(input("Please select an option to play\n"))

            if option < 0 or option >= len(songs):
                continue

            break

        except Exception:
            pass

    print("Selected %s song" % songs[option].name)

    proxy = None

    while proxy is None:
        alive = get_alive_nodes()

        for name, uri in alive:
            node = Pyro4.Proxy(uri)

            if Utils.ping(node):
                proxy = node
                break

    print("Hash of song is h=%d" % songs[option].hash)

    succ = proxy.find_successor(songs[option].hash)

    if songs[option] in succ.songs:
        print("Ok node h=%d has your song!" % succ.id())

    else:
        print("Failed node h=%d does not have your song ... try again later" % succ.id())


print("-" * 20 + "Test client" + "-" * 20)

while True:
    show_song_list()
