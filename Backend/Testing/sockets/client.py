import socket
import time
import random
from Backend.Testing.sockets.utils import *

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as socket:
    socket.connect(('127.0.0.1', 12345))

    for i in range(15):
        word = "word #" + str(random.randint(1, 15))

        print("sending %s" % word)
        send(socket, word)

        resp = recieve(socket)

        print("from server got %s" % resp)

        time.sleep(1)
