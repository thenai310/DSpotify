import zmq
import pickle
import time
from pydub import AudioSegment

CHUNK_SIZE = 250000


def server_thread(ctx):
    print("Loading audio....")

    file = AudioSegment.from_file("./1.mp3", format="mp3")
    file = pickle.dumps(file)

    router = ctx.socket(zmq.ROUTER)

    router.bind("tcp://*:6000")

    while True:
        # First frame in each message is the sender identity
        # Second frame is "fetch" command
        try:
            identity, command = router.recv_multipart()
        except zmq.ZMQError as e:
            if e.errno == zmq.ETERM:
                return   # shutting down, quit
            else:
                raise

        assert command == b"fetch"

        for i in range(0, len(file), CHUNK_SIZE):
            data = file[i:min(i + CHUNK_SIZE, len(file))]
            print("sending data = %d" % len(data))
            router.send(data, zmq.NOBLOCK)

            time.sleep(1)

        router.send(b"", zmq.NOBLOCK)


if __name__ == "__main__":
    ctx = zmq.Context()
    server_thread(ctx)
