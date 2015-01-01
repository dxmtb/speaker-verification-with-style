import os, errno
import subprocess
import tempfile
import scipy.spatial
from struct import unpack, pack

DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(DIR, 'bin')
CONFIG_DIR = os.path.join(DIR, 'cfg')
WINDOW = 1 # seconds window

def check_output(*args):
    print args[0]
    print ' '.join(args[0])
    print subprocess.call(*args, stderr=subprocess.STDOUT)

class SpeakerRecognizer(object):
    def __init__(self, workdir=None, threshold=0.5, dim=10):
        if workdir:
            self.workdir = workdir
        else:
            self.workdir = tempfile.mkdtemp(prefix='speaker_recognizer_')
        self.threshold = threshold
        self.dim = dim
        self.mfccdir = os.path.join(self.workdir, 'mfcc') + '/'
        self.gmmdir = os.path.join(self.workdir, 'gmm') + '/'
        self.matdir = os.path.join(self.workdir, 'mat') + '/'
        self.modeldir = os.path.join(self.workdir, 'iv') + '/'
        self.datadir = os.path.join(self.workdir, 'data') + '/'

        try:
            os.mkdir(self.mfccdir)
            os.mkdir(self.gmmdir)
            os.mkdir(self.matdir)
            os.mkdir(self.modeldir)
            os.mkdir(self.datadir)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise e
            pass

    def trainAndLoadUBM(self, wavpath):
	# generate gmm/world.gmm
	# generate mat/newMeanMinDiv_it.matx
	# generate mat/TV.matx
        self.extract_feat(wavpath, 'ubm')

        check_output(
            [os.path.join(BIN_DIR, 'TrainWorld'),
             '--config', os.path.join(CONFIG_DIR, 'TrainWorld.cfg'),
             '--featureFilesPath', self.mfccdir,
             '--mixtureFilesPath', self.gmmdir])

        n, ndx = self.cut_all(wavpath, 'ubm', True)

        check_output(
            [os.path.join(BIN_DIR, 'TotalVariability'),
             '--config', os.path.join(CONFIG_DIR, 'TotalVariability_fast.cfg'),
             '--totalVariabilityNumber', str(self.dim),
             '--ndxFilename', ndx,
             '--featureFilesPath', self.mfccdir,
             '--mixtureFilesPath', self.gmmdir,
             '--matrixFilesPath', self.matdir])

    def trainAndLoadSpeaker(self, wavpath):
	# generate iv/speaker.y
        self.extract_feat(wavpath, 'speaker')

        ndx = os.path.join(self.datadir, 'speaker.ndx')
        with open(ndx, 'w') as fout:
            fout.write('speaker speaker\n')

        check_output(
            [os.path.join(BIN_DIR, 'IvExtractor'),
             '--config', os.path.join(CONFIG_DIR, 'ivExtractor_fast.cfg'),
             '--totalVariabilityNumber', str(self.dim),
             '--targetIdList', ndx,
             '--featureFilesPath', self.mfccdir,
             '--mixtureFilesPath', self.gmmdir,
             '--matrixFilesPath', self.matdir,
             '--saveVectorFilesPath', self.modeldir])

    def duration(self, wavpath):
        import wave
        import contextlib
        with contextlib.closing(wave.open(wavpath,'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
        return int(duration)

    def recognize(self, wavpath):
        n, ndx = self.cut_all(wavpath, 'recognize', False)

        check_output(
            [os.path.join(BIN_DIR, 'IvExtractor'),
             '--config', os.path.join(CONFIG_DIR, 'ivExtractor_fast.cfg'),
             '--totalVariabilityNumber', str(self.dim),
             '--targetIdList', ndx,
             '--featureFilesPath', self.mfccdir,
             '--mixtureFilesPath', self.gmmdir,
             '--matrixFilesPath', self.matdir,
             '--saveVectorFilesPath', self.modeldir])

        std = self.load_iv('speaker')

        ret = []
        for i in xrange(n):
            now = self.load_iv('recognize-%d' % i)
            result = 1 - scipy.spatial.distance.cosine(std, now)
            ret.append([WINDOW * i, WINDOW * (i+1), result])
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

    def cut_all(self, wavpath, prefix, single):
        duration = self.duration(wavpath)
        n = duration / WINDOW
        assert n > 0
        ndx = os.path.join(self.datadir, '%s.ndx' % prefix)
        with open(ndx, 'w') as fout:
            for i in xrange(n):
                name = '%s-%d' % (prefix, i)
                new_wav = os.path.join(self.datadir, '%s.wav' % name)
                self.cut_wav(wavpath, new_wav,
                             WINDOW * i, WINDOW * (i+1))
                self.extract_feat(new_wav, name)
                if single:
                    fout.write(name + '\n')
                else:
                    fout.write(name + ' ' + name + '\n')
        return n, ndx

    def cut_wav(self, wavpath, new_wav, start, end):
        check_output(
            ['ffmpeg', '-i', wavpath, '-y',
             '-ss', str(start), '-t', str(end-start),
             new_wav])

    def load_iv(self, name):
        ivpath = os.path.join(self.modeldir, name + '.y')
        with open(ivpath) as fin:
            row, col = unpack('i'*2, fin.read(8))
            vecs = unpack('d'*(row*col), fin.read(8 * row * col))
            return vecs

if __name__ == '__main__':
    recognizer = SpeakerRecognizer()
    print 'Workdir', recognizer.workdir
    recognizer.trainAndLoadUBM('/home/tb/short.wav')
    recognizer.trainAndLoadSpeaker('/home/tb/speaker.wav')
    print recognizer.recognize('/home/tb/short.wav')
