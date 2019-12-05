from pydub import AudioSegment
# import pickle
#
# audio = AudioSegment.from_file("../../../Songs/1.mp3")
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

from pydub import AudioSegment
from pydub.playback import play

song = AudioSegment.from_file("../../../Songs/1.mp3")

while True:
    try:
        play(song)
    except KeyboardInterrupt:
        print("Stopping playing")
        break #to exit out of loop, back to main program