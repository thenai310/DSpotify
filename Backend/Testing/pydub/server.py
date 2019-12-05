import zmq
import pickle
from pydub import AudioSegment
from Backend.DHT.NetworkWorker import get_songs_set

context = zmq.Context()

HEADER_SIZE = 20

def prep_msg(msg):
    return f"{len(msg):<{HEADER_SIZE}}" + msg


socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

song_list = list(get_songs_set())

while True:
    msg = socket.recv()

    if pickle.loads(msg) == "list":
        socket.send(pickle.dumps(song_list))

    else:
        option = pickle.loads(msg)

        print("Ok recieved option=%d, will send song = %s" % (option, song_list[option][1]))

        audio = AudioSegment.from_file(song_list[option][0] + "/" + song_list[option][1])

        print("audio len = %d" % len(audio))

        CHUNK = 2 ** 12
        blk = (len(audio) + CHUNK - 1) // CHUNK
        k = 0

        blocks = []

        for i in range(0, len(audio), CHUNK):
            blocks.append(audio[i:min(len(audio), i + CHUNK)])

        socket.send(pickle.dumps(blk))

        while blk > 0:
            x = pickle.loads(socket.recv())

            print("Client asking for block = %d, block size = %d" % (x, len(blocks[x])))

            socket.send(pickle.dumps(blocks[x]))
