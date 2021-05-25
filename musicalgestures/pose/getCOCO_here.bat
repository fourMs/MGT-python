:: Avoid printing all the comments in the Windows cmd
@echo off

echo Downloading body pose (COCO) model...

SET WGET_EXE=..\3rdparty\windows\wget\wget.exe
SET OPENPOSE_URL=https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-python/pose-models/
SET COCO_FOLDER=coco/

echo:

SET COCO_MODEL=coco/pose_iter_440000.caffemodel
%WGET_EXE% -c %OPENPOSE_URL%%COCO_MODEL% -P %COCO_FOLDER% --no-check-certificate

echo Download finished.