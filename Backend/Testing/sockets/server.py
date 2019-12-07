import socket
import threading
from Backend.Testing.sockets.utils import *


class ClientClosed(Exception):
    pass


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
        size = 1024
        while True:
            try:
                data = recieve(client)
                print("recieved %s from address %s" % (data, address))
                response = "this is the server: " + data

                send(client, response)

            except EOFError:
                break


if __name__ == "__main__":
    # print("Loading songs....")
    #
    # songs = get_songs_set()

    print("Listening...")
    ThreadedServer('', 12345).listen()
