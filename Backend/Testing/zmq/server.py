import time
import zmq

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

while True:
    #  Wait for next request from client

    steps = 5000

    while steps > 0:
        message = socket.recv()
        print("Received request: %s" % message)

        #  Do some 'work'
        # time.sleep(1)

        #  Send reply back to client
        socket.send(b"World")

        ot = socket.recv()

        print("ot req %s" % ot)

        socket.send(b"World")

        steps -= 1