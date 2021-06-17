# Downloading body pose (COCO) model...
OPENPOSE_URL="https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-python/pose-models/coco/pose_iter_440000.caffemodel"
COCO_FOLDER="$1"
#
wget -c ${OPENPOSE_URL} -P ${COCO_FOLDER} --no-check-certificate 
# Download finished.
