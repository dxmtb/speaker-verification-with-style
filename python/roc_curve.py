import sys
import numpy as np
from sklearn.metrics import roc_curve, auc

speakers = {}

with open(sys.argv[2]) as fin:
    for line in fin:
        data = line.strip().split()
        speaker = data[0]
        speakers[speaker] = data[1] #'_'.join(data[1].split('_')[:2])


fname = sys.argv[1]
y_true = [[[], [], []], [[], [], []], [[], [], []]]
y_true_all = []
y_score = [[[], [], []], [[], [], []], [[], [], []]]
y_score_all = []
with open(fname) as fin:
    neg = 0
    for line in fin:
        _, speaker, _, wav, score = line.strip().split()
        if wav == speakers[speaker]:
            continue
        old_wav = wav
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
        dst_x = {'01':0, '03':1, '06':2}
        wav_style = old_wav.split('-')[0].split('_')[2]
        spk_style = speakers[speaker].split('-')[0].split('_')[2]
        y_true[dst_x[spk_style]][dst_x[wav_style]].append(label)
        y_score[dst_x[spk_style]][dst_x[wav_style]].append(score)
        y_true_all.append(label)
        y_score_all.append(score)

def get_EER(y_score, y_true):
    tmp = [(y_score[k], y_true[k]) for k in xrange(len(y_score))]
    tmp = sorted(tmp)
    count = [0, 0]
    nowcount = [0, 0]
    for _, true in tmp:
        count[true] += 1
    best = 1.0
    for threshold, true in tmp:
        nowcount[true] += 1
        fpr = float(count[0]-nowcount[0])/count[0]
        fnr = float(nowcount[1])/count[1]
        if abs(fpr-fnr) < best:
            best = abs(fpr - fnr)
            EER = fpr
    return EER

EERs = [[], [], []]
tot = 0
for i in xrange(3):
    for j in xrange(3):
        y_score[i][j] = np.nan_to_num(y_score[i][j])
        EER = get_EER(y_score[i][j], y_true[i][j])

#        fpr, tpr, thresholds = roc_curve(y_true[i][j], y_score[i][j])
#        roc_auc = auc(fpr, tpr)
#        #print "Area under the ROC curve : %f" % roc_auc
#
#        best = 1.0
#        EER = 0.0
#        for k in xrange(len(fpr)):
#            if abs(1-fpr[k]-tpr[k]) < best:
#                EER = tpr[k]
#                best = abs(1-fpr[k]-tpr[k])

        #print 'EER: ', EER
        EERs[i].append(EER)
    print ' '.join([str(x) for x in EERs[i]])

print 'Avg', sum(EERs[0] + EERs[1][1:])/6

if len(sys.argv) > 3 and sys.argv[3] != 'nodraw':
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
