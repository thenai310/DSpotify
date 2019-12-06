import Pyro4
from Pyro4.errors import *
import sys
import pickle
import zmq
import pyaudio
from pydub import AudioSegment
from Backend.DHT.Utils import Utils, STREAM, STATIC

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook

context = zmq.Context()
socket = context.socket(zmq.REQ)


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
    while True:
        songs = list(get_song_list())

        if len(songs) > 0:
            break

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

    if succ.is_song_available(songs[option].name):
        print("Ok node h=%d has your song!" % succ.id())
        print("Downloading now...")

        receiving_song(succ, songs[option].name)

    else:
        print("Failed node h=%d does not have your song ... try again later" % succ.id())


def receiving_song(succ, song_name):
    location = succ.ip + ":" + str(succ.port_socket)

    print("Connecting to socket %s ..." % location)

    socket.connect("tcp://" + location)

    print("Connected!")

    socket.send(pickle.dumps(STREAM))
    socket.recv()  # should be ok

    print("Sending song name = %s ..." % song_name)

    socket.send(pickle.dumps(song_name))

    blk = pickle.loads(socket.recv())

    print("Number of blocks to expect = %d" % blk)

    socket.send(pickle.dumps(b"audio data"))
    data = pickle.loads(socket.recv())

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(data[0]),
                    channels=data[1],
                    rate=data[2],
                    output=True)

    print("Playing....")

    # audio = AudioSegment.empty()
    for i in range(blk):
        socket.send(pickle.dumps(i))
        segment = pickle.loads(socket.recv())

        try:
            stream.write(segment.raw_data)

        except KeyboardInterrupt:
            if i < blk - 1:
                socket.send(pickle.dumps(-1))
                socket.recv()
            print("ctrl-c detected stopping...")
            break

        print("Recieved %d block ... %d seconds" % (i, segment.duration_seconds))

    stream.stop_stream()
    stream.close()



print("-" * 20 + "Test client" + "-" * 20)

while True:
    show_song_list()
