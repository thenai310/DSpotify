import socket
import threading
from Backend.DHT.Utils import *
from pydub import AudioSegment
import pyaudio

class ThreadedServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            client.settimeout(60)
            threading.Thread(target = self.listen_to_client,args = (client,address)).start()

    def listen_to_client(self, client, address):
        while True:
            try:
                self.manage_client(client, address)

            except EOFError:
                break
                
    def manage_client(self, sock, addr):
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

        send(sock, blk)

        song_data = [audio.sample_width, audio.channels, audio.frame_rate]
        send(sock, song_data)

        print("Sending %d blocks each of %d seconds at most" % (blk, CHUNK_LENGTH))

        while blk > 0:
            x = recieve(sock)

            # ctrl-c detected, have to stop the connection
            if x == -1:
                break

            print("Client %s asking for block = %d, block size = %d" % (addr, x, len(blocks[x])))

            send(sock, blocks[x])

            blk -= 1

        print("Succesfully send the song!")


if __name__ == "__main__":
    print("Listening...")
    ThreadedServer('', 12345).listen()
