:: Avoid printing all the comments in the Windows cmd
@echo off

echo Downloading body pose (BODY_25) model...

SET WGET_EXE=..\3rdparty\windows\wget\wget.exe
SET OPENPOSE_URL=https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-python/pose-models/
SET BODY_25_FOLDER=body_25/

echo:

SET BODY_25_MODEL=body25/pose_iter_584000.caffemodel
%WGET_EXE% -c %OPENPOSE_URL%%BODY_25_MODEL% -P %BODY_25_FOLDER% --no-check-certificate

echo Download finished.