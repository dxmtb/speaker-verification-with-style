import sys
import numpy as np
from sklearn.metrics import roc_curve, auc

speakers = {}

print sys.argv

with open(sys.argv[1]) as fin:
    for line in fin:
        data = line.strip().split()
        speaker = data[0]
        speakers[speaker] = data[1] #'_'.join(data[1].split('_')[:2])


fprs = []
tprs = []
aucs = []

fname = 'scores_SphNorm_PLDA_512.txt'
withouts = ['01', '03', '06']
for without in withouts:
    y_true = []
    y_score = []
    with open(fname) as fin:
        neg = 0
        for line in fin:
            _, speaker, _, wav, score = line.strip().split()
            if wav == speakers[speaker]:
                continue
            if wav.split('_')[-1] == without:
                continue
            wav = '_'.join(wav.split('_')[:2])
            score = float(score)
            if wav == '_'.join(speakers[speaker].split('_')[:2]):
                label = 1
                neg = 0
            else:
                label = 0
                neg += 1
    #            if neg > 3:
    #                continue
            y_true.append(label)
            y_score.append(score)

    y_score = np.nan_to_num(y_score)
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    roc_auc = auc(fpr, tpr)
    print "Area under the ROC curve : %f" % roc_auc
    fprs.append(fpr)
    tprs.append(tpr)
    aucs.append(roc_auc)

import pylab as pl
import os
# Plot ROC curve
pl.clf()
m = {'01': 'Spontaneous', '03': 'Reading', '06': 'Whisper'}
for i, fname in enumerate(withouts):
    name = 'Without %s' % m[fname]
    pl.plot(fprs[i], tprs[i], label='%s (area = %0.4f)' % (name, aucs[i]))
pl.plot([0, 1], [1, 0], 'k--')
pl.xlim([0.0, 1.0])
pl.ylim([0.0, 1.0])
pl.xlabel('False Positive Rate')
pl.ylabel('True Positive Rate')
pl.title('Receiver operating characteristic example')
pl.legend(loc="lower right")
pl.show()
