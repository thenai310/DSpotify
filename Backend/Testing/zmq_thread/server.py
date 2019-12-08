import zmq
import threading

context = zmq.Context()


class ThreadedServer(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = context.socket(zmq.REP)
        self.sock.bind("tcp://" + self.host + ":" + self.port)

    def listen(self):
        self.sock.listen(5)
        while True:
            client, address = self.sock.accept()
            client.settimeout(60)
            threading.Thread(target=self.listen_to_client, args=(client, address)).start()

    def listen_to_client(self, client, address):
        while True:
            try:
                self.manage_client(client, address)

            except EOFError:
                break

    def manage_client(self, sock, addr):
        pass
