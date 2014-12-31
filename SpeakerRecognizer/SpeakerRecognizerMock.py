import os
import subprocess
import tempfile
import random

DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(DIR, 'bin')
CONFIG_DIR = os.path.join(DIR, 'cfg')

def check_output(*args):
    print ' '.join(args[0])
    print subprocess.call(*args, stderr=subprocess.STDOUT)

class SpeakerRecognizer(object):
    def __init__(self, workdir=None):
        pass

    def trainAndLoadUBM(self, wavpath):
        pass

    def loadUBM(self, ubmpath):
        pass

    def saveUBM(self, ubmpath):
        # save self.gmmdir/world.gmm and
        pass

    def loadSpeaker(self, modelpath):
        pass

    def saveSpeaker(self, modelpath):
        pass

    def recognize(self, wavpath):
        import wave
        import contextlib
        with contextlib.closing(wave.open(wavpath,'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
        ret = []
        step = int(duration/10)
        for i in xrange(10):
            start = random.randint(step*i, step*(i+1))
            end = random.randint(step*i, step*(i+1))
            if start > end:
                start, end = end, start
            ret.append([start, end])
        return ret

if __name__ == '__main__':
    recognizer = SpeakerRecognizer()
    print recognizer.recognize('/Users/tb/new.wav')
