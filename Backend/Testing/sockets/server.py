import socketserver
import threading
from Backend.DHT.Utils import *
from Backend.DHT.Settings import BLOCK_SIZE
from pydub import AudioSegment


class ThreadedEchoRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        all_songs = list(get_local_songs_tuple_set())
        path = all_songs[0][0] + "/" + all_songs[0][1]

        print("Loading audio ....")

        audio = AudioSegment.from_file(path)

        print("Audio len = %d" % len(audio))

        print("Serializing Audio")
        sr_audio = pickle.dumps(audio)

        blk = (len(sr_audio) + BLOCK_SIZE - 1) // BLOCK_SIZE

        blocks = []

        for i in range(0, len(sr_audio), BLOCK_SIZE):
             blocks.append(audio[i:min(len(sr_audio), i + BLOCK_SIZE)])

        print("Ok just divided in %d blocks" % blk)

        #send(self.request, blk)

        song_data = [audio.sample_width, audio.channels, audio.frame_rate]
        song_data = pickle.

        # send(self.request, song_data)

        # print("Sending %d blocks each of %d seconds at most" % (blk, CHUNK_LENGTH))

        k = 0

        while blk > 0:
            x = pickle.loads(self.request.recv(BLOCK_SIZE))
            # x = recieve(self.request)

            # ctrl-c detected, have to stop the connection
            if x == -1:
                break

            print("Client asking for block = %d, block size = %d" % (x, len(blocks[x])))

            # send(self.request, blocks[x])
            blk -= 1

        print("Succesfully send the song!")


class ThreadedEchoServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == '__main__':
    print("Listening....")

    address = ('localhost', 12345)  # let the kernel give us a port
    server = ThreadedEchoServer(address, ThreadedEchoRequestHandler)
    server.serve_forever()
