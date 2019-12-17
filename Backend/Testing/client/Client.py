import pyaudio
from Backend.DHT.Utils import *
import time

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
Pyro4.config.THREADPOOL_SIZE = THREADPOOL
sys.excepthook = Pyro4.util.excepthook


def show_song_list():
    while True:
        songs = list(get_song_list())

        if len(songs) > 0:
            break

        print("Seems there is nobody alive ... retrying")

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

        except ValueError:
            pass

    print("Selected %s song" % songs[option].name)

    receiving_song(songs[option])


def receiving_song(song):
    print(f"song.name = {song.name}, hash = {song.hash}")

    node = None
    stream = None
    cur_time = 0
    p = pyaudio.PyAudio()

    while True:
        try:
            downloader = node.download_song(song.name, CHUNK_LENGTH_CLIENT)

            if stream is None:
                sample_width, channels, frame_rate = downloader.get_song_data()

                stream = p.open(format=p.get_format_from_width(sample_width),
                                channels=channels,
                                rate=frame_rate,
                                output=True)

            gen = downloader.get_song(cur_time)

            print(f"Reproducing at time = {cur_time} ms")

            for i, segment in enumerate(gen):
                print(f"playing from node h={node.hash} segment number {i}, len={len(segment)} time={time.asctime()}")
                stream.write(segment.raw_data)
                cur_time += len(segment)

            break

        except (AttributeError, OSError, PyroError) as e:
            print("Node that was streaming song is down ... retrying")

            node = get_anyone_alive()

            if node is None:
                continue

            node = node.find_successor(song.hash)

            if not Utils.ping(node) or not node.is_song_available(song.name):
                print(f"Could not find node that has the song {song.name} ... retrying")

            else:
                print(f"Okok node h={node.hash} has the song {song.name}, It will start streaming now...")

    if stream is not None:
        stream.stop_stream()
        stream.close()

    p.terminate()


print("-" * 40 + "Test client" + "-" * 40)

while True:
    show_song_list()
