import zmq
import pickle
from pydub import AudioSegment
from Backend.DHT.Utils import get_local_songs_tuple_set

CHUNK = 10000 # time length of each CHUNK

context = zmq.Context()


socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

song_list = list(get_local_songs_tuple_set("SONGS_DIRECTORY_DEBUG"))

while True:
    msg = socket.recv()

    if pickle.loads(msg) == "list":
        socket.send(pickle.dumps(song_list))

    else:
        option = pickle.loads(msg)

        print("Ok recieved option=%d, will send song = %s" % (option, song_list[option][1]))

        audio = AudioSegment.from_file(song_list[option][0] + "/" + song_list[option][1])

        print("audio len = %d" % len(audio))

        blk = (len(audio) + CHUNK - 1) // CHUNK
        k = 0

        blocks = []

        for i in range(0, len(audio), CHUNK):
            blocks.append(audio[i:min(len(audio), i + CHUNK)])

        socket.send(pickle.dumps(blk))

        new_msg = pickle.loads(socket.recv())

        socket.send(pickle.dumps([audio.sample_width, audio.channels, audio.frame_rate]))

        while blk > 0:
            x = pickle.loads(socket.recv())

            print("Client asking for block = %d, block size = %d" % (x, len(blocks[x])))

            socket.send(pickle.dumps(blocks[x]))
