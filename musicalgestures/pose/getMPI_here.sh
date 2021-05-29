# Downloading body pose (MPI) model...
OPENPOSE_URL="https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-python/pose-models/"
MPI_FOLDER="mpi/"
# 
MPI_MODEL="mpi/pose_iter_160000.caffemodel"
wget -c ${OPENPOSE_URL}${MPI_MODEL} -P ${MPI_FOLDER} --no-check-certificate
# Download finished.