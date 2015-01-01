import os
import subprocess
import tempfile
import scipy.spatial

DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(DIR, 'bin')
CONFIG_DIR = os.path.join(DIR, 'cfg')
WINDOW = 3 # seconds window

def check_output(*args):
    print ' '.join(args[0])
    print subprocess.call(*args, stderr=subprocess.STDOUT)

class SpeakerRecognizer(object):
    def __init__(self, workdir=None):
        if workdir:
            self.workdir = workdir
        else:
            self.workdir = tempfile.mkdtemp(prefix='speaker_recognizer_')
        self.mfccdir = os.path.join(self.workdir, 'mfcc') + '/'
        self.gmmdir = os.path.join(self.workdir, 'gmm') + '/'
        self.matdir = os.path.join(self.workdir, 'mat') + '/'
        self.modelpath = os.path.join(self.workdir, 'iv') + '/'
        self.datapath = os.path.join(self.workdir, 'data') + '/'

        try:
            os.mkdir(self.mfccdir)
            os.mkdir(self.gmmdir)
            os.mkdir(self.matdir)
            os.mkdir(self.modelpath)
            os.mkdir(self.datapath)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise e
            pass

    def trainAndLoadUBM(self, wavpath):
        self.extract_feat(wavpath, 'ubm')

        check_output(
            [os.path.join(BIN_DIR, 'TrainWorld'),
             '--config', os.path.join(CONFIG_DIR, 'TrainWorld.cfg'),
             '--featureFilesPath', self.mfccdir,
             '--mixtureFilesPath', self.gmmdir])

        check_output(
            [os.path.join(BIN_DIR, 'TotalVariability'),
             '--config', os.path.join(CONFIG_DIR, 'TotalVariability_fast.cfg'),
             '--ndxFilename', 'ubm',
             '--featureFilesPath', self.mfccdir,
             '--mixtureFilesPath', self.gmmdir,
             '--matrixFilesPath', self.matdir])

    def trainAndLoadSpeaker(self, wavpath):
        self.extract_feat(wavpath, 'speaker')

        check_output(
            [os.path.join(BIN_DIR, 'IvExtractor'),
             '--config', os.path.join(CONFIG_DIR, 'ivExtractor_fast.cfg'),
             '--ndxFilename', 'speaker',
             '--featureFilesPath', self.mfccdir,
             '--mixtureFilesPath', self.gmmdir,
             '--matrixFilesPath', self.matdir,
             '--saveVectorFilesPath', self.modelpath])

    def duration(self, wavpath):
        import wave
        import contextlib
        with contextlib.closing(wave.open(wavpath,'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
        return int(duration)

    def recognize(self, wavpath):
        duration = self.duration(wavpath)
        n = duration / WINDOW
        assert n > 0
        ndx = os.path.join(self.datapath, 'recognize.ndx')
        with open(ndx, 'w') as fout:
            for i in xrange(n):
                name = 'frame-%d' % i
                new_wav = os.path.join(self.datapath, '%s.wav' % name)
                self.cut_wav(wavpath, new_wav,
                             WINDOW * i, WINDOW * (i+1))
                self.extract_feat(new_wav, name)
                fout.write(name + '\n')

        check_output(
            [os.path.join(BIN_DIR, 'IvExtractor'),
             '--config', os.path.join(CONFIG_DIR, 'ivExtractor_fast.cfg'),
             '--ndxFilename', ndx,
             '--featureFilesPath', self.mfccdir,
             '--mixtureFilesPath', self.gmmdir,
             '--matrixFilesPath', self.matdir,
             '--saveVectorFilesPath', self.modelpath])

        std = self.load_iv('speaker')

        ret = []
        for i in xrange(n):
            now = self.load_iv('frame-%d' % i)
            result = 1 - spatial.distance.cosine(std, now)
            if result < self.threshold:
                ret.append([WINDOW * i, WINDOW * (i+1)])
        return ret

    def saveUBM(ubmpath):
        # save self.gmmdir/world.gmm and
        pass

    def extract_feat(self, wavpath, output):
        check_output(
            [os.path.join(BIN_DIR, 'HCopy'),
             '-C', os.path.join(CONFIG_DIR, 'hcopy_sph.cfg'), wavpath,
             os.path.join(self.mfccdir, '%s.tmp.prm' % output)])

        check_output(
            [os.path.join(BIN_DIR, 'NormFeat'),
             '--config', os.path.join(CONFIG_DIR, 'NormFeat_HTK.cfg'),
             '--featureFilesPath', self.mfccdir,
             '--inputFeatureFilename', output])

    def load_iv(self, name):
        ivpath = os.path.join(self.modelpath, name + '.y')
        with open(ivpath) as fin:
            row, col = unpack('i'*2, fin.read(8))
            vecs = unpack('d'*(row*col), fin.read(8 * row * col))
            return vecs

if __name__ == '__main__':
    recognizer = SpeakerRecognizer()
    print 'Workdir', recognizer.workdir
    recognizer.trainAndLoadUBM('/home/tb/short.wav')
