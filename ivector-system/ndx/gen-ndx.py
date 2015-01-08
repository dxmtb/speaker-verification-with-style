import os

os.system("paste -d ' ' ../lst/all.lst ../lst/all.lst >./ivExtractor.ndx")

def gen_trainModel(inp, out1, out2):
    tot = 0
    spks = []
    lines = []
    with open(out1, 'w') as fout:
        with open(inp) as fin:
            for line in fin:
                line = line.strip()
                spk = 'spk%03d' % tot
                fout.write('%s %s\n' % (spk, line))
                spks.append(spk)
                lines.append(line)
                tot += 1
    with open(out2, 'w') as fout:
        for line in lines:
            fout.write(' '.join([line]+spks) + '\n')

gen_trainModel('../lst/UBM.lst', './trainModel_train.ndx', './ivTest_plda_target-seg_train.ndx')
gen_trainModel('../lst/test.lst', './trainModel_test.ndx', './ivTest_plda_target-seg_test.ndx')

