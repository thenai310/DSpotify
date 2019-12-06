import zmq
import argparse
import pickle
import Pyro4
import sys
import time
from pydub import AudioSegment
from random import randint
from Backend.DHT.Utils import Utils, STREAM, STATIC
from Backend.DHT.Settings import *

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook

parser = argparse.ArgumentParser(description="Node creation script")
parser.add_argument("--hash", default=None, type=int, help="Hash of node")
args = parser.parse_args()

logger = Utils.init_logger("Logger of Socket")

context = zmq.Context()
socket = context.socket(zmq.REP)

port = 0

while True:
    try:
        port = randint(2 ** 13, 2 ** 17)
        socket.bind("tcp://*:" + str(port))
        break

    except zmq.error.ZMQError:
        pass

logger.info("Socket of node h=%d is ready, waiting at localhost:%d" % (args.hash, port))

node = Pyro4.Proxy("PYRONAME:Node:%d" % args.hash)
node.port_socket = port

logger.info("location of socket is localhost:%d" % node.port_socket)
logger.info("Connected to node h=%d and now waiting the client for a request ..." % args.hash)

while True:
    who = pickle.loads(socket.recv())
    socket.send(pickle.dumps("ok"))

    if who == STREAM:
        # streaming

        song_name = pickle.loads(socket.recv())

        logger.info("sending song %s to a client" % song_name)

        full_path = ""
        for song in node.songs:
            if song.name == song_name:
                full_path = song.full_path
                break

        logger.info("Loading audio ....")

        audio = AudioSegment.from_file(full_path)

        logger.debug("audio len = %d" % len(audio))

        blk = (len(audio) + CHUNK_LENGTH - 1) // CHUNK_LENGTH
        k = 0

        blocks = []

        for i in range(0, len(audio), CHUNK_LENGTH):
            blocks.append(audio[i:min(len(audio), i + CHUNK_LENGTH)])

        logger.debug("ok just divided in %d blocks" % blk)

        socket.send(pickle.dumps(blk))

        new_msg = pickle.loads(socket.recv()) # this message should be asking for audio data

        socket.send(pickle.dumps([audio.sample_width, audio.channels, audio.frame_rate]))

        logger.debug("sending %d blocks each of %d seconds at most" % (blk, CHUNK_LENGTH))

        while blk > 0:
            x = pickle.loads(socket.recv())

            # have to stop connection
            if x == -1:
                socket.send(pickle.dumps("bye"))
                break

            logger.debug("Client asking for block = %d, block size = %d" % (x, len(blocks[x])))

            socket.send(pickle.dumps(blocks[x]))

        logger.debug("succesfully send the song!")

    else:
        # static download
        song_name = pickle.loads(socket.recv())

        logger.info("Sending song %s to a client" % song_name)

        full_path = ""
        for song in node.songs:
            if song.name == song_name:
                full_path = song.full_path
                break

        logger.info("Loading audio ....")

        audio = AudioSegment.from_file(full_path)

        logger.debug("Audio len = %d" % len(audio))
        logger.info("Serializing audio...")

        serialized_audio = pickle.dumps(audio)

        logger.info("Serialized audio has %d bytes" % len(serialized_audio))
        logger.info("Sending...")

        socket.send(serialized_audio)
