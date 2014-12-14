import sys
import numpy as np
from sklearn.metrics import roc_curve, auc

speakers = {}

print sys.argv

with open('../ivector-system/ndx/trainModel2.ndx') as fin:
    for line in fin:
        data = line.strip().split()
        speaker = data[0]
        speakers[speaker] = data[1] #'_'.join(data[1].split('_')[:2])


fname = sys.argv[1]
y_true = []
y_score = []
with open(fname) as fin:
    neg = 0
    for line in fin:
        _, speaker, _, wav, score = line.strip().split()
        if wav == speakers[speaker]:
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

best = 1.0
EER = 0.0
for i in xrange(len(fpr)):
    if abs(1-fpr[i]-tpr[i]) < best:
        EER = tpr[i]
        best = abs(1-fpr[i]-tpr[i])

import pylab as pl
import os
# Plot ROC curve
pl.clf()
pl.plot(fpr, tpr, label='(EER = %0.4f area = %0.4f)' % (EER, roc_auc))
pl.plot([0, 1], [1, 0], 'k--')
pl.xlim([0.0, 1.0])
pl.ylim([0.0, 1.0])
pl.xlabel('False Positive Rate')
pl.ylabel('True Positive Rate')
pl.title('Receiver operating characteristic example')
pl.legend(loc="lower right")
pl.show()
