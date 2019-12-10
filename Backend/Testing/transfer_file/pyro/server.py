import Pyro4
import sys
from pydub import AudioSegment

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook


CHUNK = 100  # in ms


@Pyro4.expose
@Pyro4.behavior(instance_mode="single", instance_creator=lambda cls: cls.create_instance())
class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.audio = AudioSegment.from_file("/home/daniel/PycharmProjects/DSpotify/songs_small/3.mp3")
        print("Loaded audio!")

    @property
    def ip(self):
        return self.__ip

    @ip.setter
    def ip(self, ip):
        self.__ip = ip

    @property
    def port(self):
        return self.__port

    @port.setter
    def port(self, port):
        self.__port = port

    @classmethod
    def create_instance(cls):
        return cls("127.0.0.1", 12345)

    def get_song_data(self):
        return [self.audio.sample_width, self.audio.channels, self.audio.frame_rate]

    def get_song(self, start_time):
        for i in range(start_time, len(self.audio), CHUNK):
            segment = self.audio[i:i + CHUNK]
            yield segment


if __name__ == '__main__':
    daemon = Pyro4.Daemon(port=12345)
    uri = daemon.register(Server, "server")
    print(f"uri = {uri}")
    daemon.requestLoop()
