import socketserver
import threading
from Backend.DHT.Utils import *
from pydub import AudioSegment
import zmq
import time
from random import randint


def handle_client(sock):
    all_songs = list(get_local_songs_tuple_set("SONGS_DIRECTORY_DEBUG"))
    path = all_songs[0][0] + "/" + all_songs[0][1]

    print("Loading audio ....")

    audio = AudioSegment.from_file(path)

    print("Audio len = %d" % len(audio))

    blk = (len(audio) + CHUNK_LENGTH - 1) // CHUNK_LENGTH

    blocks = []

    for i in range(0, len(audio), CHUNK_LENGTH):
        blocks.append(audio[i:min(len(audio), i + CHUNK_LENGTH)])

    print("Ok just divided in %d blocks" % blk)

    song_data = [audio.sample_width, audio.channels, audio.frame_rate]

    for i in range(10000):
        msg = pickle.loads(sock.recv())
        sock.send(pickle.dumps(blk))

        print("Doing Stuff")

        msg = pickle.loads(sock.recv())
        sock.send(pickle.dumps(song_data))

    #
    #
    # recieve(sock)
    # send(sock, song_data)
    #
    # print("Sending %d blocks each of %d seconds at most" % (blk, CHUNK_LENGTH))

    # for i in range(10000):
    #     x = recieve(sock)
    #
    #     # ctrl-c detected, have to stop the connection
    #     # if x == -1:
    #     #     send(sock, "") # nothing
    #     #     break
    #
    #     r = randint(0, blk - 1)
    #     print("Client asking for block = %d, block size = %d" % (r, len(blocks[r])))
    #     send(sock, blocks[r])
    #     # blk -= 1

    # print("Succesfully send the song!")


if __name__ == '__main__':
    context = zmq.Context()

    with context.socket(zmq.REP) as sock:
        sock.bind("tcp://*:12345")

        while True:
            handle_client(sock)
