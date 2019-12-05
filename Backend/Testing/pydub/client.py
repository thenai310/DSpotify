import zmq
import pickle
import pydub
from pydub.playback import play
from pydub import AudioSegment

HEADER_SIZE = 20


def prep_msg(msg):
    return f"{len(msg):<{HEADER_SIZE}}" + msg


context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

socket.send(pickle.dumps("list"))
response = socket.recv()
song_list = pickle.loads(response)

print("Song list")

for i, song in enumerate(song_list):
    print("%d- %s" % (i, song[1]))

while True:
    option = 0

    while True:
        try:
            option = int(input("Please select an option to play\n"))

            if option < 0 or option >= len(song_list):
                continue

            break

        except Exception:
            pass

    print("Selected %s song, nice now downloading song..." % song_list[option][1])

    socket.send(pickle.dumps(option))

    blk = pickle.loads(socket.recv())

    print("Number of blocks to expect = %d" % blk)

    audio = AudioSegment.empty()
    for i in range(blk):
        socket.send(pickle.dumps(i))
        segment = pickle.loads(socket.recv())

        if i == 0:
            play(segment)

        audio += segment

        print("Recieved %d block ... %d seconds" % (i, segment.duration_seconds))

    print("Recieved %s" % type(audio))
    print("Playing....")
