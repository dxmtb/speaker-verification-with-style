rm data_wav.lst data_wav.scp
for f in wav/*.wav; do
  name=`basename $f .wav`
  echo $name >> data_wav.lst
  echo data/$f data/prm/$name.tmp.prm >>data_wav.scp
done
