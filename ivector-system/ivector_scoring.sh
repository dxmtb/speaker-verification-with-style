echo "Compare models to test segments using PLDA native scoring"
DIM=$1
echo bin/IvTest --config cfg/ivTest_SphNorm_Plda.cfg --loadVectorFilesPath ./iv/raw_$DIM/ --testVectorFilesPath ./iv/raw_$DIM/ --iVectSize $DIM --outputFilename res/scores_SphNorm_PLDA_$DIM.txt " &> log/IvTest_SphNorm_Plda_$DIM.log"
echo " done, see log/IvTest_SphNorm_Plda.log for details"









