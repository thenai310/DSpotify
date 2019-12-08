import zmq
import pickle
from pydub import AudioSegment
from pydub.playback import play
import uuid

def client_thread(ctx):
    dealer = ctx.socket(zmq.DEALER)
    dealer.connect("tcp://127.0.0.1:6000")
    dealer.send(b"fetch")

    total = 0       # Total bytes received
    chunks = 0      # Total chunks received

    data = bytes()

    while True:
        try:
            chunk = dealer.recv()
        except zmq.ZMQError as e:
            if e.errno == zmq.ETERM:
                return   # shutting down, quit
            else:
                raise

        chunks += 1
        size = len(chunk)
        total += size

        print("recieving")

        data += chunk

        if size == 0:
            break   # whole file received

    print ("%i chunks received, %i bytes" % (chunks, total))

    audio = pickle.loads(data)

    print("Exporting audio...")
    id = str(uuid.uuid1())
    audio.export("./1_copy_" + id + ".mp3", format="mp3", bitrate="256k")


if __name__ == "__main__":
    ctx = zmq.Context()
    client_thread(ctx)
