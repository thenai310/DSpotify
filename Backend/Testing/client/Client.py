import pyaudio
from Backend.DHT.Utils import *
import time

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
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
    print("Hash of song is h=%d" % song.hash)

    while True:
        node = get_anyone_alive()

        if node is None:
            print("Seems there is nobody alive ... retrying")
            continue

        succ = node.find_successor(song.hash)

        if Utils.ping(succ) and succ.is_song_available(song.name):
            print("Ok node h=%d has your song!" % succ.hash)
            break

        else:
            print("Failed, retrying...")
            continue

    print("Downloading now...")

    downloader = succ.download_song(song.name, CHUNK_LENGTH_CLIENT)
    sample_width, channels, frame_rate = downloader.get_song_data()

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(sample_width),
                    channels=channels,
                    rate=frame_rate,
                    output=True)

    cur_time = 0

    while True:
        try:
            node = get_anyone_alive()

            if node is None:
                print("Seems there is nobody alive ... retrying")
                continue

            succ = node.find_successor(song.hash)

            if not Utils.ping(succ) or not succ.is_song_available(song.name):
                print("Failed, retrying...")
                continue

            downloader = succ.download_song(song.name, CHUNK_LENGTH_CLIENT)
            gen = downloader.get_song(cur_time)

            print(f"Reproducing at time = {cur_time} ms")

            for i, segment in enumerate(gen):
                print(f"playing from node h={node.hash} segment number {i}, len={len(segment)} time={time.asctime()}")
                stream.write(segment.raw_data)
                cur_time += len(segment)

            break
        except (OSError, PyroError):
            print("Waiting for the server to go up again...")

    stream.stop_stream()
    stream.close()

    p.terminate()


print("-" * 40 + "Test client" + "-" * 40)

while True:
    show_song_list()
