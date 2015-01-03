import tempfile
import os
import time

from PyQt4 import QtGui, QtCore
from PyQt4.phonon import Phonon

from converter import Converter

from SpeakerRecognizer import SpeakerRecognizer


def dumpAudio(videoPath):
    converter = Converter()
    f, path = tempfile.mkstemp(prefix='recognizer')
    conv = converter.convert(videoPath, path, {
        'format': 'wav',
        'audio': {
            'codec': 'pcm_s16le'
        }
    })
    for timecode in conv:
        print "Converting {} ...\r".format(timecode)
    print 'Audio dumped into {}'.format(path)
    return path


class TrainThread(QtCore.QThread):
    jobDone = QtCore.pyqtSignal(object)
    def __init__(self, recognizer, wavPath):
        super(TrainThread, self).__init__()
        self.recognizer = recognizer
        self.wavPath = wavPath
    def run(self):
        print 'trainning'
        self.recognizer.trainAndLoadUBM(self.wavPath)

class RangeBar(QtGui.QGraphicsView):
    def __init__(self, *args, **kargs):
        super(RangeBar, self).__init__(*args, **kargs)
        self.scene = QtGui.QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(QtCore.QRectF(0, 0, 100, 10))

    def addRange(self, start, end, color):
        self.scene.addRect(start, 0, end - start, 10,
                pen=QtGui.QPen(QtGui.QColor(0, 0, 0, 0)),
                brush=QtGui.QBrush(QtGui.QColor(color)))
        print self.scene.sceneRect()

class Window(QtGui.QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.recognizer = SpeakerRecognizer.SpeakerRecognizer()

        self.functionButtons = QtGui.QWidget(self)
        self.functionButtons.layout = QtGui.QHBoxLayout(self.functionButtons)

        self.trainUBMButton = QtGui.QPushButton('Train UBM', self.functionButtons)
        self.loadUBMButton = QtGui.QPushButton('Load UBM', self.functionButtons)

        self.trainUBMButton.clicked.connect(self.handleTrainUBMButton)

        self.functionButtons.layout.addWidget(self.trainUBMButton)
        self.functionButtons.layout.addWidget(self.loadUBMButton)

        self.media = Phonon.MediaObject(self)

        self.video = Phonon.VideoWidget(self)
        self.video.setMinimumSize(480, 320)

        self.audio = Phonon.AudioOutput(Phonon.VideoCategory, self)

        Phonon.createPath(self.media, self.audio)
        Phonon.createPath(self.media, self.video)

        self.buttons = QtGui.QWidget(self)
        self.buttons.layout = QtGui.QHBoxLayout(self.buttons)

        self.openButton = QtGui.QPushButton('Open', self.buttons)
        self.playButton = QtGui.QPushButton('Play', self.buttons)
        self.playButton.setEnabled(False)

        self.openButton.clicked.connect(self.handleOpenButton)
        self.playButton.clicked.connect(self.handlePlayButton)

        self.buttons.layout.addWidget(self.openButton)
        self.buttons.layout.addWidget(self.playButton)

        self.progress = QtGui.QSlider(self, orientation=QtCore.Qt.Horizontal)
        self.progress.sliderMoved.connect(self.progressMoved)

        self.media.stateChanged.connect(self.handleStateChanged)
        self.media.tick.connect(self.tick)

        self.speakers = RangeBar(self)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.video, 1)
        layout.addWidget(self.buttons)
        layout.addWidget(self.functionButtons)
        layout.addWidget(self.progress)
        layout.addWidget(self.speakers)

        self.speakers.addRange(0, 100, 'red')

    def tick(self):
        if self.media.state() == Phonon.PlayingState:
            self.progress.setValue(self.media.currentTime())

    def progressMoved(self, newValue):
        if self.media.state() == Phonon.PlayingState or \
            self.media.state() == Phonon.PausedState:
            self.media.seek(newValue)

    def handleTrainUBMButton(self):
        self.audioPath = dumpAudio(str(self.videoPath))
        self.train = TrainThread(self.recognizer, self.audioPath)
        self.train.start()

    def handleLoadUBMButton(self):
        pass

    def handlePlayButton(self):
        if self.media.state() == Phonon.PlayingState:
            self.playButton.setText('Play')
            self.media.pause()
        else:
            self.playButton.setText('Pause')
            self.media.play()

    def handleOpenButton(self):
        if self.media.state() == Phonon.PlayingState:
            self.media.stop()
            self.progress.setValue(0)
        else:
            path = QtGui.QFileDialog.getOpenFileName(self, self.openButton.text(),
                    'video')
            if path:
                self.videoPath = path
                self.media.setCurrentSource(Phonon.MediaSource(path))
                self.media.play()

    def handleStateChanged(self, newstate, oldstate):
        if newstate == Phonon.PlayingState:
            self.progress.setMaximum(self.media.totalTime())
            self.progress.setMinimum(0)
            self.openButton.setText('Stop')
            self.playButton.setText('Pause')
            self.playButton.setEnabled(True)
        elif (newstate != Phonon.LoadingState and
              newstate != Phonon.BufferingState):
            self.openButton.setText('Open')
            if newstate == Phonon.ErrorState:
                source = self.media.currentSource().fileName()
                print ('ERROR: could not play:', source.toLocal8Bit().data())
                print ('  %s' % self.media.errorString().toLocal8Bit().data())

if __name__ == '__main__':

    import sys
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('Phonon Player')
    window = Window()
    window.show()
    sys.exit(app.exec_())
