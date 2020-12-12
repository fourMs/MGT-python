:: Avoid printing all the comments in the Windows cmd
@echo off

echo Downloading body pose (MPI) model...

SET WGET_EXE=%1
SET OPENPOSE_URL=http://posefs1.perception.cs.cmu.edu/OpenPose/models/
SET MPI_FOLDER=%2

echo:

SET MPI_MODEL=pose/mpi/pose_iter_160000.caffemodel
%WGET_EXE% -c %OPENPOSE_URL%%MPI_MODEL% -P %MPI_FOLDER%

echo Download finished.