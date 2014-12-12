from dump_iv import read_iv
import numpy as np
import theano
import theano.tensor as T
from scipy.optimize import fmin_l_bfgs_b as fmin
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)s[%(lineno)d] %(levelname)s %(message)s', datefmt='%H:%M:%S')

def load_data():
    with open('train_speakers') as fin:
        speakers = [x.strip() for x in fin]

    X = [[], [], []]
    dim = None
    for speaker in speakers:
        tmp = []
        for label in ['01', '03', '06']:
            path = '../ivector-system/iv/raw_512/%s_%s.y' % (speaker, label)
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

    return X

X0, X1, X2 = load_data()
X0 = np.array(X0, dtype=theano.config.floatX)
X1 = np.array(X1, dtype=theano.config.floatX)
X2 = np.array(X2, dtype=theano.config.floatX)
print X0.shape, X1.shape, X2.shape
dim = len(X0[0])
N = len(X0)

print 'N %d Dim %d' % (N, dim)

theta = theano.shared(value=np.zeros(dim*4, dtype=theano.config.floatX))

W0 = theta[0:dim].reshape((dim,))
W0_init = np.ones((dim,))
W0.name = 'W0'
b0 = theta[dim: dim*2].reshape((dim,))
b0_init = np.zeros((dim))
b0.name = 'b0'
W1 = theta[dim*2: dim*3].reshape((dim,))
W1_init = np.ones((dim,))
W1.name = 'W1'
b1 = theta[dim*3: dim*4].reshape((dim, ))
b1_init = np.zeros((dim))
b1.name = 'b1'

theta.set_value(np.concatenate((W0_init, b0_init, W1_init, b1_init)))

diff = T.sum((X0 * W0 + b0 - X2) ** 2) + T.sum((X1 * W1 + b1 - X2) ** 2)
loss = diff / N
for arg in [W0, b0, W1, b1]:
    loss += T.sum(arg**2) * 0.5

loss_func = theano.function([], loss)
grad_func = theano.function([], T.grad(loss, theta))

def train_fn(theta_value):
    theta.set_value(theta_value, borrow=True)
    return loss_func()

def train_fn_grad(theta_value):
    theta.set_value(theta_value, borrow=True)
    return grad_func()

epoch = 0

def callback(theta_value):
    global epoch
    epoch += 1
    logging.info('epoch %d, loss %f' % (epoch, train_fn(theta_value)))

fmin(train_fn, fprime=train_fn_grad, x0=theta.get_value(), callback=callback, disp=0)

print theta.get_value()
