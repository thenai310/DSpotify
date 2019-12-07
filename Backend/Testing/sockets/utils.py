import pickle

BLOCK_SIZE = 1024


def send(socket, data):
    data = pickle.dumps(data)
    blocks = (len(data) + BLOCK_SIZE - 1) // BLOCK_SIZE

    socket.send(pickle.dumps(blocks))
    msg = socket.recv(BLOCK_SIZE)

    for i in range(0, len(data), BLOCK_SIZE):
        arr = data[i:min(i + BLOCK_SIZE, len(data))]

        socket.send(arr)
        socket.recv(BLOCK_SIZE)


def recieve(socket):
    blocks = pickle.loads(socket.recv(BLOCK_SIZE))
    socket.send(b"ok")

    data = bytearray()
    for i in range(blocks):
        arr = socket.recv(BLOCK_SIZE)
        socket.send(b"ok")
        data += arr

    return pickle.loads(data)
