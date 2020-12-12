:: Avoid printing all the comments in the Windows cmd
@echo off

echo Downloading body pose (COCO) model...

SET WGET_EXE=..\3rdparty\windows\wget\wget.exe
SET OPENPOSE_URL=http://posefs1.perception.cs.cmu.edu/OpenPose/models/
SET COCO_FOLDER=coco/

echo:

SET COCO_MODEL=pose/coco/pose_iter_440000.caffemodel
%WGET_EXE% -c %OPENPOSE_URL%%COCO_MODEL% -P %COCO_FOLDER%

echo Download finished.