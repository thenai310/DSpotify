import socket

SIZE = 1024

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect(('127.0.0.1', 12345))

    for i in range(500):
        word = "word #" + str(i)
        sock.send(word.encode())

        resp = sock.recv(SIZE).decode()

        print("resp: " + resp)
