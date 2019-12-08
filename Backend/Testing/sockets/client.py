import time
import random
import zmq
from Backend.DHT.Utils import *

context = zmq.Context()

with context.socket(zmq.REQ) as sock:
    sock.connect("tcp://localhost:12345")

    print("Connected!")

    for i in range(10000):
        sock.send(pickle.dumps("test"))
        blk = pickle.loads(sock.recv())

        # print("Number of blocks to expect = %d" % blk)

        sock.send(pickle.dumps("test"))
        data = pickle.loads(sock.recv())

        print(data)

    # send(sock, "test")
    # data = recieve(sock)
    #
    # print("Just got sample width, channels and frame rate of audio")

    # p = pyaudio.PyAudio()
    #
    # stream = p.open(format=p.get_format_from_width(data[0]),
    #                 channels=data[1],
    #                 rate=data[2],
    #                 output=True)

    # print("Playing....")
    #
    # for i in range(10000):
    #     # try:
    #     send(sock, i)
    #     segment = recieve(sock)
    #     # except KeyboardInterrupt:
    #     #     send(sock, -1)
    #     #     recieve(sock) # nothing
    #     #     break
    #
    #     # time.sleep(0.5)
    #
    #     # try:
    #     #     stream.write(segment.raw_data)
    #     #
    #     # except KeyboardInterrupt:
    #     #     if i < blk - 1:
    #     #         send(sock, -1)
    #     #
    #     #     print("\nctrl-c detected stopping...")
    #     #     break
    #
    #     print("Recieved %d block ... %d seconds" % (i, segment.duration_seconds))
    #
    # # stream.stop_stream()
    # # stream.close()
    # #
    # # p.terminate()