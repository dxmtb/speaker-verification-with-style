import os
import subprocess
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(DIR, 'bin')
CONFIG_DIR = os.path.join(DIR, 'cfg')

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

        try:
            os.mkdir(self.mfccdir)
            os.mkdir(self.gmmdir)
            os.mkdir(self.matdir)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise e
            pass

    def trainAndLoadUBM(self, wavpath):
        check_output(
            [os.path.join(BIN_DIR, 'HCopy'),
             '-C', os.path.join(CONFIG_DIR, 'hcopy_sph.cfg'), wavpath,
             os.path.join(self.mfccdir, 'ubm.tmp.prm')])

        check_output(
            [os.path.join(BIN_DIR, 'NormFeat'),
             '--config', os.path.join(CONFIG_DIR, 'NormFeat_HTK.cfg'),
             '--featureFilesPath', self.mfccdir])

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

    def saveUBM(ubmpath):
        # save self.gmmdir/world.gmm and
        pass

if __name__ == '__main__':
    recognizer = SpeakerRecognizer()
    print 'Workdir', recognizer.workdir
    recognizer.trainAndLoadUBM('/home/tb/short.wav')
