echo "Extract MFCC :`date`"
COMMAND_LINE="bin/HCopy -C cfg/hcopy_sph.cfg -T 1 -S data/data_wav.scp"
echo $COMMAND_LINE
$COMMAND_LINE

echo "Normalise energy : `date` "
CMD_NORM_E="bin/NormFeat --config cfg/NormFeat_energy_HTK.cfg --inputFeatureFilename data/data_wav.lst --featureFilesPath data/prm/"
echo $CMD_NORM_E
$CMD_NORM_E
echo "End normalise energy : `date`\n "

echo "Energy Detector : `date` "
CMD_ENERGY="bin/EnergyDetector  --config cfg/EnergyDetector_HTK.cfg --inputFeatureFilename data/data_wav.lst --featureFilesPath data/prm/  --labelFilesPath  data/lbl/"
echo $CMD_ENERGY
$CMD_ENERGY
echo "End energy detector : `date`\n "

echo "Normalise Features : `date`"
CMD_NORM="bin/NormFeat --config cfg/NormFeat_HTK.cfg --inputFeatureFilename data/data_wav.lst --featureFilesPath  data/prm/   --labelFilesPath  data/lbl/"
echo $CMD_NORM
$CMD_NORM
echo "End Normalise Features : `date`"

