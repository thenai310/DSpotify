from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *
from MediaPlayer.MainWindow import Ui_MainWindow
import Pyro4
import sys
from Backend.DHT.Utils import *
from Pyro4.errors import PyroError

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
        self.playButton.pressed.connect(self.get_audio_stream)
        # self.pauseButton.pressed.connect(self.player.pause)
        # self.stopButton.pressed.connect(self.player.stop)
        # self.volumeSlider.valueChanged.connect(self.player.setVolume)

        # self.previousButton.pressed.connect(self.playlist.previous)
        # self.nextButton.pressed.connect(self.playlist.next)

        # self.model = PlaylistModel(self.playlist)
        # self.playlistView.setModel(self.model)
        # self.playlist.currentIndexChanged.connect(self.playlist_position_changed)
        # selection_model = self.playlistView.selectionModel()
        # selection_model.selectionChanged.connect(self.playlist_selection_changed)

        self.playlist.doubleClicked.connect(self.get_audio_stream)

        self.hash_list = []  # list of hashes of songs on playlist

        # self.player.durationChanged.connect(self.update_duration)
        # self.player.positionChanged.connect(self.update_position)
        # self.timeSlider.valueChanged.connect(self.player.setPosition)

        self.open_file_action.triggered.connect(self.open_file)
        self.lineedit.returnPressed.connect(self.search_song)
        self.refreshButton.pressed.connect(self.refresh_list)
        self.setAcceptDrops(True)

        self.logger = Utils.init_logger("MediaPlayer Logger")

        self.show()

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

    def get_audio_stream(self, *args):
        song_name = self.playlist.currentItem().text()
        row = self.playlist.currentRow()
        print(f"song = {song_name}, row = {row}")

        song_hash = self.hash_list[row]

        self.logger.info(f"song_name = {song_name}, hash = {song_hash}")

        node = get_anyone_alive()

        if node is None:
            self.error_alert("Could not find any alive node on the network")
            return

        succ = node.find_successor(song_hash)

        if Utils.ping(succ) and succ.is_song_available(song_name):
            pass

        else:
            self.error_alert(f"Could not find alive node that has song {song_name}")
            return


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
