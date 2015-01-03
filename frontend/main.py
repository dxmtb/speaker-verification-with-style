import tempfile
import os
import time

from OpenGL import GL, GLU
from PyQt4 import QtGui, QtCore, QtOpenGL
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

class RangeBar(QtOpenGL.QGLWidget):
    ranges = []
    def __init__(self, *args, **kargs):
        super(RangeBar, self).__init__(*args, **kargs)
        self.setMinimumSize(100, 10)

    def initializeGL(self):
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClearDepth(1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glLoadIdentity()

    def resizeGL(self, w, h):
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(0, 100, 0, 10, -50.0, 50.0)
        GL.glViewport(0, 0, w, h)

    def paintGL(self):
        for r in self.ranges:
            print r
            st = r[0]
            ed = r[1]
            color = r[2]
            GL.glColor3f(color.red() / 255.0,
                         color.green() / 255.0,
                         color.blue() / 255.0)
            GL.glRectf(st, 0, ed, self.height())

    def addRange(self, start, end, color):
        self.ranges.append((start, end, color))

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

        self.speakers.addRange(0, 10, QtGui.QColor('red'))

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
