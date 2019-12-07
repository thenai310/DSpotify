import socket
import time
import random
from Backend.DHT.Utils import *

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect(('127.0.0.1', 12345))

    print("Connected!")

    blk = recieve(sock)

    print("Number of blocks to expect = %d" % blk)

    data = recieve(sock)

    print("Just got sample width, channels and frame rate of audio")

    # p = pyaudio.PyAudio()
    #
    # stream = p.open(format=p.get_format_from_width(data[0]),
    #                 channels=data[1],
    #                 rate=data[2],
    #                 output=True)

    print("Playing....")

    for i in range(blk):
        try:
            send(sock, i)
            segment = recieve(sock)
        except KeyboardInterrupt:
            send(sock, -1)
            break

        # time.sleep(0.5)

        # try:
        #     stream.write(segment.raw_data)
        #
        # except KeyboardInterrupt:
        #     if i < blk - 1:
        #         send(sock, -1)
        #
        #     print("\nctrl-c detected stopping...")
        #     break

        print("Recieved %d block ... %d seconds" % (i, segment.duration_seconds))

    # stream.stop_stream()
    # stream.close()
    #
    # p.terminate()
