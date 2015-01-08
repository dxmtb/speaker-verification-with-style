mkdir -p wav
for f in old_wav/*.wav; do
  name=`basename $f .wav`
  ffmpeg -i $f -ss 0 -t 90 wav/$name-0.wav
  ffmpeg -i $f -ss 90 -t 90 wav/$name-1.wav
done
