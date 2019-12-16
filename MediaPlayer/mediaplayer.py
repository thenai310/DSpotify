from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from MediaPlayer.MainWindow import Ui_MainWindow
from Backend.DHT.Utils import *
from Pyro4.errors import PyroError
import pyaudio
import time
from threading import Thread

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook

def hhmmss(ms):
    # s = 1000
    # m = 60000
    # h = 360000
    h, r = divmod(ms, 36000)
    m, r = divmod(r, 60000)
    s, _ = divmod(r, 1000)
    return ("%d:%02d:%02d" % (h, m, s)) if h else ("%d:%02d" % (m, s))


class PlaylistModel(QAbstractListModel):
    def __init__(self, playlist, *args, **kwargs):
        super(PlaylistModel, self).__init__(*args, **kwargs)
        self.playlist = playlist

    def data(self, index, role):
        if role == Qt.DisplayRole:
            media = self.playlist.media(index.row())
            return media.canonicalUrl().fileName()

    def rowCount(self, index):
        return self.playlist.mediaCount()


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        # Connect control buttons/slides for media player.
        self.playButton.pressed.connect(self.parallel_get_audio_stream)
        self.pauseButton.pressed.connect(self.pause_audio)
        self.stopButton.pressed.connect(self.stop_audio)
        # self.volumeSlider.valueChanged.connect(self.player.setVolume)

        self.previousButton.pressed.connect(self.play_previous_song)
        self.nextButton.pressed.connect(self.play_next_song)

        # self.model = PlaylistModel(self.playlist)
        # self.playlistView.setModel(self.model)
        # self.playlist.currentIndexChanged.connect(self.playlist_position_changed)
        # selection_model = self.playlistView.selectionModel()
        # selection_model.selectionChanged.connect(self.playlist_selection_changed)

        self.playlist.doubleClicked.connect(self.parallel_get_audio_stream)

        self.hash_list = []  # list of hashes of songs on playlist

        # self.player.durationChanged.connect(self.update_duration)
        # self.player.positionChanged.connect(self.update_position)
        # self.timeSlider.valueChanged.connect(self.player.setPosition)

        self.open_file_action.triggered.connect(self.open_file)
        self.lineedit.returnPressed.connect(self.search_song)
        self.refreshButton.pressed.connect(self.refresh_list)
        self.setAcceptDrops(True)

        self.logger = Utils.init_logger("MediaPlayer Logger")

        # is the audio playing
        self.audio_playing = False

        # stop current music stream
        self.stop_music_stream = False

        self.show()

    def closeEvent(self, QCloseEvent):
        self.stop_audio()

    def search_song(self):
        print(self.lineedit.text())
        self.lineedit.setText('')

    def refresh_list(self):
        try:
            song_list = list(get_song_list())
        except (OSError, PyroError):
            self.error_alert("Could not find any node on the network")
            return

        if len(song_list) == 0:
            self.info_alert("Could not find songs on the network")
            return

        self.playlist.clear()
        self.hash_list = []

        for song in song_list:
            self.playlist.addItem(song.name)
            self.hash_list.append(song.hash)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "mp3 Audio (*.mp3)")

        if path:
            self.playlist.addItem(path)

    def parallel_get_audio_stream(self):
        if self.playlist.count() == 0:
            return

        self.stop_audio()
        t = Thread(target=self.get_audio_stream)
        t.start()

    def get_audio_stream(self, *args):
        self.audio_playing = True

        song_name = self.playlist.currentItem().text()
        row = self.playlist.currentRow()
        song_hash = self.hash_list[row]

        self.logger.debug(f"song_name = {song_name}, row = {row}, hash = {song_hash}")

        node = None
        stream = None
        cur_time = 0
        p = pyaudio.PyAudio()

        while True:
            try:
                downloader = node.download_song(song_name, CHUNK_LENGTH_CLIENT)

                if stream is None:
                    sample_width, channels, frame_rate = downloader.get_song_data()

                    stream = p.open(format=p.get_format_from_width(sample_width),
                                    channels=channels,
                                    rate=frame_rate,
                                    output=True)

                gen = downloader.get_song(cur_time)

                self.logger.info(f"Reproducing at time = {cur_time} ms")

                for i, segment in enumerate(gen):
                    self.logger.debug(f"playing from node h={node.hash} segment number {i}, len={len(segment)} time={time.asctime()}")
                    stream.write(segment.raw_data)

                    if self.stop_music_stream:
                        break

                    cur_time += len(segment)

                break

            except (AttributeError, OSError, PyroError):
                self.logger.error("Node that was streaming song is down ... retrying")

                node = get_anyone_alive()

                if node is None:
                    continue

                node = node.find_successor(song_hash)

                if not Utils.ping(node) or not node.is_song_available(song_name):
                    self.logger.error(f"Could not find node that has the song {song_name} ... retrying")

                else:
                    self.logger.info(f"Okok node h={node.hash} has the song {song_name}, It will start streaming now...")

            finally:
                if self.stop_music_stream:
                    break

        if stream is not None:
            stream.stop_stream()
            stream.close()

        p.terminate()

        self.audio_playing = False
        self.logger.info("Played song successfully!")

    def pause_audio(self):
        pass

    def stop_audio(self):
        if self.audio_playing:
            self.stop_music_stream = True

            while self.audio_playing:
                pass

            self.logger.debug("Ok stopped audio successfully!")
            self.stop_music_stream = False

    def play_previous_song(self):
        if self.playlist.count() == 0:
            return

        row = self.playlist.currentRow()

        if row > 0:
            self.playlist.setCurrentRow(row - 1)
            self.parallel_get_audio_stream()

    def play_next_song(self):
        if self.playlist.count() == 0:
            return

        row = self.playlist.currentRow()

        if row < self.playlist.count() - 1:
            self.playlist.setCurrentRow(row + 1)
            self.parallel_get_audio_stream()

    def update_duration(self, mc):
        self.timeSlider.setMaximum(self.player.duration())
        duration = self.player.duration()

        if duration >= 0:
            self.totalTimeLabel.setText(hhmmss(duration))

    def update_position(self, *args):
        position = self.player.position()
        if position >= 0:
            self.currentTimeLabel.setText(hhmmss(position))

        # Disable the events to prevent updating triggering a setPosition event (can cause stuttering).
        self.timeSlider.blockSignals(True)
        self.timeSlider.setValue(position)
        self.timeSlider.blockSignals(False)

    def playlist_selection_changed(self, ix):
        # We receive a QItemSelection from selectionChanged.
        i = ix.indexes()[0].row()
        self.playlist.setCurrentIndex(i)

    def playlist_position_changed(self, i):
        if i > -1:
            ix = self.model.index(i)
            self.playlist.setCurrentIndex(ix)

    def error_alert(self, *args):
        QMessageBox.critical(self, "Error", args[0], QMessageBox.Close)

    def info_alert(self, *args):
        QMessageBox.information(self, "Info", args[0], QMessageBox.Ok)


if __name__ == '__main__':
    app = QApplication([])
    app.setApplicationName("DSpotify")
    app.setStyle("Fusion")

    # # Fusion dark palette from https://gist.github.com/QuantumCD/6245215.
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    # app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")

    window = MainWindow()
    app.exec_()
