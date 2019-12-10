import Pyro4
import sys
import pyaudio
import time
from Pyro4.errors import PyroError

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook

server = Pyro4.Proxy("PYRO:server@localhost:12345")

print("Server Data")
print(server.ip)
print(server.port)


sample_width, channels, frame_rate = server.get_song_data()

p = pyaudio.PyAudio()

stream = p.open(format=p.get_format_from_width(sample_width),
                channels=channels,
                rate=frame_rate,
                output=True)

cur_time = 0

while True:
    try:
        gen = server.get_song(cur_time)

        print(f"Reproducing at time = {cur_time} ms")

        for i, segment in enumerate(gen):
            print(f"playing segment number {i}, len={len(segment)} time={time.asctime()}")
            stream.write(segment.raw_data)
            cur_time += len(segment)

        break
    except PyroError:
        print("Waiting for the server to go up again...")

stream.stop_stream()
stream.close()

p.terminate()