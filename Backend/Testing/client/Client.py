import Pyro4
from Pyro4.errors import *
import sys
from Backend.DHT.Utils import Utils

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
            songs |= set(node.songs)

    return songs


def show_song_list():
    songs = list(get_song_list())

    print("This are all the songs on the server")

    for i, song in enumerate(songs):
        print("%d- %s" % (i, song[1]))
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

    print("Selected %s song" % songs[option][1])

print("-" * 20 + "Test client" + "-" * 20)

show_song_list()