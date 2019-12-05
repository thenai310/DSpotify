from pydub import AudioSegment
import pickle
import pyaudio
from pydub.playback import play
import wave
import sys

audio = AudioSegment.from_file("../../../Songs/1.mp3")
# print(len(audio))
#
# test = pickle.dumps(audio)
#
# CHUNK = 2 ** 20
#
# b = bytearray()
# for i in range(0, len(test), CHUNK):
#     for j in range(i, min(len(test), i + CHUNK)):
#         b.append(test[j])
#
#     print(len(b))
#
# get_back = pickle.loads(b)
# print(len(get_back))
# print(audio)

# from pydub import AudioSegment
# from pydub.playback import play
#
# song = AudioSegment.from_file("../../../Songs/1.mp3")
#
# while True:
#     try:
#         play(song)
#     except KeyboardInterrupt:
#         print("Stopping playing")
#         break #to exit out of loop, back to main program

p = pyaudio.PyAudio()

stream = p.open(format=p.get_format_from_width(audio.sample_width),
                channels=audio.channels,
                rate=audio.frame_rate,
                output=True)

CHUNK = 10000 #ms

print(len(audio))

k = 0
for i in range(0, len(audio), CHUNK):
    arr = audio[i:min(len(audio), i + CHUNK)]
    stream.write(arr.raw_data)
    print(k, arr)
    k += 1

    if k == 1:
        break

stream.stop_stream()
stream.close()

p.terminate()
