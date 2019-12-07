import socketserver

SIZE = 1024


class ThreadedEchoRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        word = self.request.recv(SIZE).decode()
        response = "this is server: " + word
        print("got: " + word)
        self.request.send(response.encode())


class ThreadedEchoServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


if __name__ == '__main__':
    print("Listening....")

    address = ('localhost', 12345)  # let the kernel give us a port
    server = ThreadedEchoServer(address, ThreadedEchoRequestHandler)
    server.serve_forever()
