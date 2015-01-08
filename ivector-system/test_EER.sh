DIM=$1
mkdir -p res

rm res/scores_SphNorm_PLDA_"$DIM"_train.txt
rm mat/plda*
IVPATH=./iv/raw_"$DIM"
bin/IvTest --config cfg/ivTest_SphNorm_Plda.cfg --loadVectorFilesPath $IVPATH --testVectorFilesPath $IVPATH --outputFilename res/scores_SphNorm_PLDA_"$DIM"_train.txt --ndxFilename ndx/ivTest_plda_target-seg_train.ndx --targetIdList ndx/trainModel_train.ndx --iVectSize 100 >/dev/null
echo 'Train EER before transform'
python ../python/roc_curve.py res/scores_SphNorm_PLDA_"$DIM"_train.txt ndx/trainModel_train.ndx nodraw

rm res/scores_SphNorm_PLDA_"$DIM"_test.txt
rm mat/plda*
bin/IvTest --config cfg/ivTest_SphNorm_Plda.cfg --loadVectorFilesPath $IVPATH --testVectorFilesPath $IVPATH --outputFilename res/scores_SphNorm_PLDA_"$DIM"_test.txt --ndxFilename ndx/ivTest_plda_target-seg_test.ndx --targetIdList ndx/trainModel_test.ndx --iVectSize 100 >/dev/null
echo 'Test EER before transform'
python ../python/roc_curve.py res/scores_SphNorm_PLDA_"$DIM"_test.txt ndx/trainModel_test.ndx nodraw

IVPATH=./iv/raw_"$DIM"_new
mkdir -p $IVPATH
cd ../python
python train.py --iv_path ../ivector-system/iv/raw_"$DIM" --task train
python train.py --iv_path ../ivector-system/iv/raw_"$DIM" --task test

cd ../ivector-system

rm res/scores_SphNorm_PLDA_"$DIM"_train.txt
rm mat/plda*
bin/IvTest --config cfg/ivTest_SphNorm_Plda.cfg --loadVectorFilesPath $IVPATH --testVectorFilesPath $IVPATH --outputFilename res/scores_SphNorm_PLDA_"$DIM"_train.txt --ndxFilename ndx/ivTest_plda_target-seg_train.ndx --targetIdList ndx/trainModel_train.ndx --iVectSize 100 >/dev/null
echo 'Train EER after transform'
python ../python/roc_curve.py res/scores_SphNorm_PLDA_"$DIM"_train.txt ndx/trainModel_train.ndx nodraw

rm res/scores_SphNorm_PLDA_"$DIM"_test.txt
rm mat/plda*
bin/IvTest --config cfg/ivTest_SphNorm_Plda.cfg --loadVectorFilesPath $IVPATH --testVectorFilesPath $IVPATH --outputFilename res/scores_SphNorm_PLDA_"$DIM"_test.txt --ndxFilename ndx/ivTest_plda_target-seg_test.ndx --targetIdList ndx/trainModel_test.ndx --iVectSize 100 >/dev/null
echo 'Test EER after transform'
python ../python/roc_curve.py res/scores_SphNorm_PLDA_"$DIM"_test.txt ndx/trainModel_test.ndx nodraw
