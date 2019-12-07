import Pyro4
from Pyro4.errors import *
import sys
import pickle
import zmq
import pyaudio
from pydub import AudioSegment
from Backend.DHT.Utils import *

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook


def show_song_list():
    while True:
        songs = list(get_song_list())

        if len(songs) > 0:
            break

    print("These are all the songs on the server")

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
    ip_server = succ.ip
    port_server = succ.port_socket

    print("Connecting to socket %s:%d ..." % (ip_server, port_server))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip_server, port_server))

        print("Connected!")

        send(sock, STREAM)

        print("Sending song name = %s ..." % song_name)

        send(sock, song_name)

        blk = recieve(sock)

        print("Number of blocks to expect = %d" % blk)

        data = recieve(sock)

        print("Just got sample width, channels and frame rate of audio")

        # p = pyaudio.PyAudio()
        #
        # stream = p.open(format=p.get_format_from_width(data[0]),
        #                 channels=data[1],
        #                 rate=data[2],
        #                 output=True)

        print("Playing....")

        for i in range(blk):
            try:
                send(sock, i)
                segment = recieve(sock)
            except KeyboardInterrupt:
                send(sock, -1)
                break

            # try:
            #     stream.write(segment.raw_data)
            #
            # except KeyboardInterrupt:
            #     if i < blk - 1:
            #         send(sock, -1)
            #
            #     print("\nctrl-c detected stopping...")
            #     break

            print("Recieved %d block ... %d seconds" % (i, segment.duration_seconds))

        # stream.stop_stream()
        # stream.close()
        #
        # p.terminate()


print("-" * 40 + "Test client" + "-" * 40)

while True:
    show_song_list()
