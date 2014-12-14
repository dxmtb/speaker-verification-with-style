from dump_iv import read_iv, dump_iv
import numpy as np
import theano
import theano.tensor as T
from scipy.optimize import fmin_l_bfgs_b as fmin
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[%(lineno)d] %(levelname)s %(message)s', datefmt='%H:%M:%S')
import gflags

FLAGS = gflags.FLAGS
gflags.DEFINE_string('iv_path', '../ivector-system/iv/raw_512', 'path to iv')
gflags.DEFINE_string('task', 'train', 'train or dump(then test)')
gflags.DEFINE_string('model', 'linear', 'bias or projection')

def load_data(fname):
    with open(fname) as fin:
        speakers = [x.strip() for x in fin]

    X = [[], [], []]
    dim = None
    for speaker in speakers:
        tmp = []
        for label in ['01', '03', '06']:
            path = '%s/%s_%s.y' % (FLAGS.iv_path, speaker, label)
            iv = read_iv(path)
            if np.isnan(iv[0]):
                print 'Wrong: ', path
                continue
            tmp.append(iv)
            if dim:
                assert len(iv) == dim
            else:
                dim = len(iv)
        if len(tmp) == 3:
            for i, x in enumerate(tmp):
                X[i].append(x)

    X = np.array(X, dtype=theano.config.floatX)
    return X

def do_train():
    X0, X1, X2 = load_data('./train_speakers')
    dim = len(X0[0])
    N = len(X0)

    print 'N %d Dim %d' % (N, dim)

    if FLAGS.model == 'bias':
        theta = theano.shared(value=np.zeros(dim*2, dtype=theano.config.floatX))
        b0 = theta[:dim].reshape((dim,))
        b0_init = np.zeros((dim))
        b0.name = 'b0'
        b1 = theta[dim: 2*dim].reshape((dim, ))
        b1_init = np.zeros((dim))
        b1.name = 'b1'
        theta.set_value(np.concatenate((b0_init, b1_init)))
        diff = T.sum((X0 + b0 - X2) ** 2) + T.sum((X1 + b1 - X2) ** 2)
    elif FLAGS.model == 'projection':
        theta = theano.shared(value=np.zeros(dim*2+2*dim*dim, dtype=theano.config.floatX))
        W0 = theta[0:dim*dim].reshape((dim,dim))
        W0_init = np.identity(dim)
        W0.name = 'W0'
        b0 = theta[dim*dim:dim*dim+dim].reshape((dim,))
        b0_init = np.zeros((dim))
        b0.name = 'b0'
        W1 = theta[dim*dim+dim: 2*dim*dim+dim].reshape((dim,dim))
        W1_init = np.identity(dim)
        W1.name = 'W1'
        b1 = theta[2*dim*dim+dim:].reshape((dim, ))
        b1_init = np.zeros((dim))
        b1.name = 'b1'

        theta.set_value(np.concatenate((W0_init.ravel(), b0_init, W1_init.ravel(), b1_init)))

        diff = T.sum((T.dot(X0, W0) + b0 - X2) ** 2) + T.sum((T.dot(X1, W1) + b1 - X2) ** 2)
    elif FLAGS.model == 'linear':
        theta = theano.shared(value=np.zeros(dim*4, dtype=theano.config.floatX))
        W0 = theta[0:dim].reshape((dim,))
        W0_init = np.ones((dim,))
        W0.name = 'W0'
        b0 = theta[dim:dim*2].reshape((dim,))
        b0_init = np.zeros((dim))
        b0.name = 'b0'
        W1 = theta[dim*2: dim*3].reshape((dim,))
        W1_init = np.ones((dim,))
        W1.name = 'W1'
        b1 = theta[dim*3:].reshape((dim, ))
        b1_init = np.zeros((dim))
        b1.name = 'b1'

        theta.set_value(np.concatenate((W0_init.ravel(), b0_init, W1_init.ravel(), b1_init)))

        diff = T.sum((X0 * W0 + b0 - X2) ** 2) + T.sum((X1 * W1 + b1 - X2) ** 2)
    else:
        logging.info('Unknown model: %s' % FLAGS.model)

#    for arg in [W0, b0, W1, b1]:
#        loss += T.sum(arg**2) * 0.5

    loss = diff / N
    loss_func = theano.function([], loss)
    grad_func = theano.function([], T.grad(loss, theta))

    def train_fn(theta_value):
        theta.set_value(theta_value, borrow=True)
        return loss_func()

    def train_fn_grad(theta_value):
        theta.set_value(theta_value, borrow=True)
        return grad_func()

    epoch = [0]

    def callback(theta_value):
        epoch[0] += 1
        logging.info('epoch %d, loss %f' % (epoch[0], train_fn(theta_value)))

    fmin(train_fn, fprime=train_fn_grad, x0=theta.get_value(), disp=0)

    print loss_func()

#    print W0.eval()
#    print X2[0], np.dot(X0[0], W0.eval()) + b0.eval()
#    print X2[0], X0[0] + b0.eval()

    np.save('theta', theta.get_value())

def do_test():
    theta = np.load('theta.npy')
    if FLAGS.model == 'bias':
        dim = len(theta)/2
        #W0 = theta[0:dim]
        b0 = theta[:dim]
        #W1 = theta[dim*2:dim*3]
        b1 = theta[dim:dim*2]
        transform0 = lambda iv: iv + b0
        transform1 = lambda iv: iv + b1
    elif FLAGS.model == 'projection':
        for i in xrange(1000):
            if i*i*2 + 2*i == len(theta):
                dim = i
                break
        W0 = theta[0:dim*dim].reshape((dim,dim))
        b0 = theta[dim*dim:dim*dim+dim].reshape((dim,))
        W1 = theta[dim*dim+dim: 2*dim*dim+dim].reshape((dim,dim))
        b1 = theta[2*dim*dim+dim:].reshape((dim, ))
        transform0 = lambda iv: np.dot(W0, iv) + b0
        transform1 = lambda iv: np.dot(W1, iv) + b1
    elif FLAGS.model == 'linear':
        dim = len(theta)/4
        W0 = theta[0:dim].reshape((dim,))
        b0 = theta[dim:dim*2].reshape((dim,))
        W1 = theta[dim*2: dim*3].reshape((dim,))
        b1 = theta[dim*3:].reshape((dim, ))
        transform0 = lambda iv: W0 * iv + b0
        transform1 = lambda iv: W1 * iv + b1
    else:
        assert False

    with open('./all_speakers') as fin:
        speakers = [x.strip() for x in fin]

    import os
    os.system('mkdir -p %s_new' % (FLAGS.iv_path))

    dim = None
    for speaker in speakers:
        before = None
        for label in ['06', '01', '03']:
            path = '%s/%s_%s.y' % (FLAGS.iv_path, speaker, label)
            iv = read_iv(path)
            if np.isnan(iv[0]):
                dump_iv('%s_new/%s_%s.y' % (FLAGS.iv_path, speaker, label), iv)
                print 'Wrong: ', path
                continue
            if dim:
                assert len(iv) == dim
            else:
                dim = len(iv)
            if label == '01':
                iv = transform0(iv)
                #iv = before
            elif label == '03':
                iv = transform1(iv)
                #iv = before
            else:
                before = iv
            dump_iv('%s_new/%s_%s.y' % (FLAGS.iv_path, speaker, label), iv)

    logging.info('Dumped new ivectors to %s_new.' % (FLAGS.iv_path))

def main(argv):
    argv = FLAGS(argv)
    if FLAGS.task == 'train':
        do_train()
    else:
        do_test()

if __name__ == '__main__':
    import sys
    main(sys.argv)
