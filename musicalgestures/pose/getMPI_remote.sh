# Downloading body pose (MPI) model...
OPENPOSE_URL="http://posefs1.perception.cs.cmu.edu/OpenPose/models/"
MPI_FOLDER="$1"

# 
MPI_MODEL="pose/mpi/pose_iter_160000.caffemodel"
sudo wget -c ${OPENPOSE_URL}${MPI_MODEL} -P ${MPI_FOLDER}

# Download finished.