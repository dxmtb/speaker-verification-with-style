import sys
from struct import unpack, pack
import numpy as np

def read_iv(fname):
    with open(fname) as fin:
        row, col = unpack('i'*2, fin.read(8))
        vecs = unpack('d'*(row*col), fin.read(8 * row * col))
        return vecs

def dump_iv(fname, iv):
    with open(fname, 'wb') as fout:
        fout.write(pack('ii' + 'd' * len(iv), 1, len(iv), *iv))
    assert np.isnan(iv[0]) or read_iv(fname) == tuple(iv)

if __name__ == '__main__':
    iv = read_iv(sys.argv[1])
    print iv
    dump_iv('tmp', iv)
    print read_iv('tmp')
