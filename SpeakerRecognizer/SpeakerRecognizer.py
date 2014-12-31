import os
import subprocess
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(DIR, 'scripts')
BIN_DIR = os.path.join(DIR, 'bin')
CONFIG_DIR = os.path.join(SCRIPTS_DIR, 'config')


class SpeakerRecognizer(object):
    def __init__(self, workdir):
        if workdir:
            self.workdir = workdir
        else:
            self.workdir = tempfile.mkdtemp(prefix='speaker_recognizer_')
        self.mfccdir = os.path.join(self.workdir, 'mfcc')
        self.gmmdir = os.path.join(self.workdir, 'ubm')
        self.modeldir = os.path.join(self.workdir, 'model')
        self.configdir = os.path.join(self.workdir, 'model')

        try:
            os.mkdir(mfccdir)
            os.mkdir(gmmdir)
            os.mkdir(modeldir)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise e
            pass

    def trainAndLoadUBM(wavpath):
        subprocess.check_output(
            [os.path.join(BIN_DIR, 'HCopy'),
             '-C', 'cfg/hcopy_sph.cfg', wavpath,
             os.path.join(self.mfccdir, 'ubm.mfcc')])

        subprocess.check_output(
            [os.path.join(BIN_DIR, 'TrainWorld'),
             '--config', 'TrainWorld.cfg',
             '--featureFilesPath', self.mfccdir,
             '--mixtureFilesPath', self.gmmdir])

        subprocess.check_output(
            [os.path.join(BIN_DIR, 'TotalVariability'),
             '--config', 'TotalVariability_fast.cfg',
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
    recognizer.trainAndLoadUBM('')
