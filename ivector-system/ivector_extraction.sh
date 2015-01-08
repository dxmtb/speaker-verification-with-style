MIXTURE=$1

mkdir -p gmm mat log

# 1. UBM training
	echo "Train Universal Background Model by EM algorithm"
	bin/TrainWorld --config cfg/TrainWorld.cfg --outputWorldFilename "world_$MIXTURE" --mixtureDistribCount $MIXTURE &> log/TrainWorld_$MIXTURE.log
	echo "		done, see log/TrainWorld.log for details"

# 2. Total Variability matrix Estimation
	echo "Train TotalVariability matrix"
	bin/TotalVariability --config cfg/TotalVariability_fast.cfg --meanEstimate "newMeanMinDiv_it_$MIXTURE" --nullOrderStatSpeaker "TV_N_$MIXTURE" --firstOrderStatSpeaker "TV_F_X_$MIXTURE" --initTotalVariabilityMatrix "TV_init_$MIXTURE" --totalVariabilityMatrix "TV_$MIXTURE" --inputWorldFilename "world_$MIXTURE"  --totalVariabilityNumber 100 &> log/TotalVariability_$MIXTURE.log
	echo "		done, see log/TotalVariability.log for details"

# 3. I-vector extraction
	echo "Extract i-vectors"
	mkdir -p iv/raw_$MIXTURE
	bin/IvExtractor --config cfg/ivExtractor_fast.cfg --meanEstimate "newMeanMinDiv_it_$MIXTURE" --nullOrderStatSpeaker "TV_N_$MIXTURE" --firstOrderStatSpeaker "TV_F_X_$MIXTURE" --totalVariabilityMatrix "TV_$MIXTURE" --inputWorldFilename "world_$MIXTURE" --saveVectorFilesPath iv/raw_$MIXTURE/ --totalVariabilityNumber 100 &> log/IvExtractor_$MIXTURE.log
	echo "		done, see log/IvExtractor.log for details"

