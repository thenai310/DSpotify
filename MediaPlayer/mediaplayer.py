from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *
from Backend.DHT.Utils import *
from Pyro4.errors import *
from MediaPlayer.MainWindow import Ui_MainWindow

import Pyro4
import sys
import pickle
import pydub
import os
import time
import socket

Pyro4.config.SERIALIZER = "pickle"
Pyro4.config.SERIALIZERS_ACCEPTED.add("pickle")
sys.excepthook = Pyro4.util.excepthook

def get_alive_nodes():
    ns = Pyro4.locateNS()
    return list(ns.list(prefix="Node:").items())


def get_song_list():
    alive = get_alive_nodes()

    songs = set()

    for name, uri in alive:
        node = Pyro4.Proxy(uri)

        if Utils.ping(node):
            songs |= node.get_all_songs()

    return songs


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

        self.player = QMediaPlayer()

        self.player.error.connect(self.error_alert)
        self.player.play()

        # Setup QListWidget
        self.song_listWidget.itemDoubleClicked.connect(self.download_song)

        # Setup the playlist.
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)

        # Connect control buttons/slides for media player.
        self.playButton.pressed.connect(self.player.play)
        self.pauseButton.pressed.connect(self.player.pause)
        self.stopButton.pressed.connect(self.player.stop)
        self.volumeSlider.valueChanged.connect(self.player.setVolume)

        self.previousButton.pressed.connect(self.playlist.previous)
        self.nextButton.pressed.connect(self.playlist.next)

        self.model = PlaylistModel(self.playlist)
        self.playlistView.setModel(self.model)
        self.playlist.currentIndexChanged.connect(self.playlist_position_changed)
        selection_model = self.playlistView.selectionModel()
        selection_model.selectionChanged.connect(self.playlist_selection_changed)

        self.player.durationChanged.connect(self.update_duration)
        self.player.positionChanged.connect(self.update_position)
        self.timeSlider.valueChanged.connect(self.player.setPosition)

        self.open_file_action.triggered.connect(self.open_file)
        self.lineedit.returnPressed.connect(self.search_song)
        self.refreshButton.pressed.connect(self.refresh_list)
        self.setAcceptDrops(True)

        self.songs_on_list = []
        self.songs_on_playlist = set()

        self.logger = Utils.init_logger("GUI App Logger")

        self.show()

    def search_song(self):
        print(self.lineedit.text())
        self.lineedit.setText('')

    def refresh_list(self):
        try:
            song_list = get_song_list()

        except (PyroError, OSError):
            self.error_alert("Could not refresh song list. It seems Pyro is not working")
            return None

        if len(song_list) == 0:
            self.info_alert("There are no songs on the server at the time")
            return None

        self.song_listWidget.clear()
        self.songs_on_list = song_list

        for song in song_list:
            self.song_listWidget.addItem(song.name)

        self.song_listWidget.update()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "mp3 Audio (*.mp3)")

        if path:
            self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(path)))

        self.model.layoutChanged.emit()

    def download_song(self, *args):
        song_name = self.song_listWidget.currentItem().text()

        if song_name in self.songs_on_playlist:
            return None

        while True:
            alive = get_alive_nodes()

            proxy = None
            for name, uri in alive:
                node = Pyro4.Proxy(uri)

                if Utils.ping(node):
                    proxy = node
                    break

            if proxy is None:
                self.erroralert("There is no node to connect to")
                return None

            song_hash = -1
            for song in self.songs_on_list:
                if song.name == song_name:
                    song_hash = song.hash
                    break

            # this cant happen
            if song_hash == -1:
                self.error_alert("Critical error, this should not be happening")
                return None

            audio = None

            self.logger.info("Talking with node h=%d" % proxy.hash)

            try:
                succ = proxy.find_successor(song_hash)

                if not Utils.ping(succ) or not succ.is_song_available(song_name):
                    self.error_alert("It seems the nodes containing the song are down.... retrying")
                    continue

                self.logger.info("Ok node h=%d has the song %s, starting comunication..." % (succ.id(), song_name))

                ip_server = succ.ip
                port_server = succ.port_socket

                self.logger.debug("Connecting to socket %s:%d ..." % (ip_server, port_server))

                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.connect((ip_server, port_server))
                    self.logger.debug("Connected!")

                    send(sock, STATIC)

                    self.logger.debug("Sleeping 10 seconds...")
                    time.sleep(10)

                    send(sock, song_name)
                    audio = recieve(sock)

                break

            except (OSError, EOFError, PyroError):
                self.error_alert("Retrying the connection it seems the song can't be found right know")

        path = os.getcwd() + "/" + song_name

        self.logger.info("Exporting song to %s" % path)

        audio.export(path)

        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(path)))
        self.songs_on_playlist.add(song_name)
        self.model.layoutChanged.emit()

        self.logger.info("Downloaded song %s succesfully!" % song_name)

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
            self.playlistView.setCurrentIndex(ix)

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
