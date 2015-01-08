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


class TrainUBMThread(QtCore.QThread):
    jobDone = QtCore.pyqtSignal(object)
    def __init__(self, recognizer, wavPath):
        super(TrainUBMThread, self).__init__()
        self.recognizer = recognizer
        self.wavPath = wavPath
    def run(self):
        print 'trainning'
        self.recognizer.trainAndLoadUBM(self.wavPath)
        self.jobDone.emit(None)

class TrainSpeakerThread(QtCore.QThread):
    jobDone = QtCore.pyqtSignal(object)
    def __init__(self, recognizer, wavPath, ranges):
        super(TrainSpeakerThread, self).__init__()
        self.recognizer = recognizer
        self.wavPath = wavPath
        self.ranges = ranges
    def run(self):
        print 'training speaker'
        self.recognizer.trainAndLoadSpeakerByRange(self.wavPath, self.ranges)
        self.jobDone.emit(None)

class PredictSpeakerThread(QtCore.QThread):
    jobDone = QtCore.pyqtSignal(object)
    def __init__(self, recognizer, wavPath):
        super(PredictSpeakerThread, self).__init__()
        self.recognizer = recognizer
        self.wavPath = wavPath
    def run(self):
        print 'predicting speaker'
        result = self.recognizer.recognize(self.wavPath)
        self.jobDone.emit(result)

class SpeakerBar(QtOpenGL.QGLWidget):
    dataChanged = QtCore.pyqtSignal(object)
    rangelen = 10000

    def __init__(self, linkedMedia, audioPath, recognizer, parent):
        super(SpeakerBar, self).__init__(parent=parent)
        self.setMinimumSize(100, 10)
        self.linkedMedia = linkedMedia
        self.audioPath = audioPath
        self.recognizer = recognizer
        self.ranges = []
        self.markingRange = False
        self.leftPoint = 0

    def initializeGL(self):
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClearDepth(1.0)
        GL.glLoadIdentity()

    def resizeGL(self, w, h):
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        padding = self.rangelen / 100
        GL.glOrtho(- padding, self.rangelen + padding, 0, 10, -50.0, 50.0)
        GL.glViewport(0, 0, w, h)

    def paintGL(self):
        if self.hasFocus():
            GL.glClearColor(0.5, 0.5, 0.5, 1.0)
            color = QtGui.QColor('yellow')
        else:
            GL.glClearColor(0.0, 0.0, 0.0, 1.0)
            color = QtGui.QColor('red')
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        for r in self.ranges:
            st = r[0] * self.rangelen / self.linkedMedia.totalTime()
            ed = r[1] * self.rangelen / self.linkedMedia.totalTime()
            GL.glColor3f(color.red() / 255.0,
                         color.green() / 255.0,
                         color.blue() / 255.0)
            GL.glRectf(st, 0, ed, self.height())

    def addRange(self, start, end):
        self.ranges.append((start, end))

    def mousePressEvent(self, event):
        self.setFocus()

    def keyPressEvent(self, event):
        if type(event) == QtGui.QKeyEvent:
            if event.key() == 32:  # space
                if self.markingRange:  # close it
                    self.addRange(self.leftPoint, self.linkedMedia.currentTime())
                    self.markingRange = False
                    self.glDraw()
                else:
                    self.markingRange = True
                    self.leftPoint = self.linkedMedia.currentTime()
            elif event.key() == 80:  # p for predict
                self.predict = PredictSpeakerThread(self.recognizer,
                        self.audioPath)
                self.predict.jobDone.connect(self.handlePredict)
                self.predict.start()
            elif event.key() == 84:  # t for train
                ranges = [tuple([y / 1000.0 for y in x]) for x in self.ranges]
                self.train = TrainSpeakerThread(self.recognizer,
                        self.audioPath, ranges)
                self.train.connect(self.handleTrainSpeakerDone)
                self.train.start()

    def handleTrainSpeakerDone(self):
        QtGui.QMessageBox.information(self, 'Done!', 'Speaker Trained',
                QtGui.QMessageBox.Ok)

    def handlePredict(self, result):
        for r in result:
            if r[2] > 0:
                self.addRange(int(r[0] * 1000), int(r[1] * 1000))
        self.glDraw()

class Window(QtGui.QWidget):
    speakers = []
    def __init__(self):
        super(Window, self).__init__()

        self.recognizer = SpeakerRecognizer.SpeakerRecognizer()

        self.functionButtons = QtGui.QWidget(self)
        self.functionButtons.layout = QtGui.QHBoxLayout(self.functionButtons)

        self.trainUBMButton = QtGui.QPushButton('Train UBM', self.functionButtons)
        self.loadUBMButton = QtGui.QPushButton('Load UBM', self.functionButtons)
        self.saveUBMButton = QtGui.QPushButton('Save UBM', self.functionButtons)
        self.addSpeakerButton = QtGui.QPushButton('Add Speaker', self.functionButtons)

        self.trainUBMButton.clicked.connect(self.handleTrainUBMButton)
        self.loadUBMButton.clicked.connect(self.handleLoadUBMButton)
        self.saveUBMButton.clicked.connect(self.handleSaveUBMButton)
        self.addSpeakerButton.clicked.connect(self.handleAddSpeakerButton)

        self.functionButtons.layout.addWidget(self.trainUBMButton)
        self.functionButtons.layout.addWidget(self.loadUBMButton)
        self.functionButtons.layout.addWidget(self.saveUBMButton)
        self.functionButtons.layout.addWidget(self.addSpeakerButton)

        self.media = Phonon.MediaObject(self)

        self.video = Phonon.VideoWidget(self)
        self.video.setAspectRatio(Phonon.VideoWidget.AspectRatioWidget)
        self.video.setMinimumSize(640, 360)

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

        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addWidget(self.video, 1)
        self.layout.addWidget(self.buttons)
        self.layout.addWidget(self.functionButtons)
        self.layout.addWidget(self.progress)

    def tick(self):
        if self.media.state() == Phonon.PlayingState:
            self.progress.setValue(self.media.currentTime())

    def progressMoved(self, newValue):
        if self.media.state() == Phonon.PlayingState or \
            self.media.state() == Phonon.PausedState:
            self.media.seek(newValue)

    def handleTrainUBMButton(self):
        self.train = TrainUBMThread(self.recognizer, self.audioPath)
        self.train.jobDone.connect(self.handleTrainUBMDone)
        self.train.start()

    def handleTrainUBMDone(self):
        QtGui.QMessageBox.information(self, 'Done!', 'UBM Trained',
                QtGui.QMessageBox.Ok)

    def handleLoadUBMButton(self):
        path = QtGui.QFileDialog.getOpenFileName(self,
                self.loadUBMButton.text(), 'data')
        if path:
            self.recognizer.loadUBM(unicode(path))

    def handleSaveUBMButton(self):
        path = QtGui.QFileDialog.getSaveFileName(self,
                self.loadUBMButton.text(), 'data')
        if path:
            self.recognizer.saveUBM(unicode(path))

    def handleAddSpeakerButton(self):
        newBar = SpeakerBar(linkedMedia=self.media, audioPath=self.audioPath,
                            recognizer=self.recognizer, parent=self)
        self.layout.addWidget(newBar)

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
                self.audioPath = dumpAudio(unicode(self.videoPath))
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
