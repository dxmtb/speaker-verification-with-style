import sys
from struct import unpack

def read_iv(fname):
  with open(fname) as fin:
    row, col = unpack('i'*2, fin.read(8))
    vecs = unpack('d'*(row*col), fin.read(8 * row * col))
  return vecs

if __name__ == '__main__':
  print read_iv(sys.argv[1])
