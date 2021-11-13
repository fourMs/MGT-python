# Downloading body pose (MPI) model...
OPENPOSE_URL="https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-python/pose-models/"
BODY_25_FOLDER="$1"
# 
BODY_25_MODEL="body25/pose_iter_584000.caffemodel"
wget -c ${OPENPOSE_URL}${BODY_25_MODEL} -P ${BODY_25_FOLDER} --no-check-certificate 
# Download finished.