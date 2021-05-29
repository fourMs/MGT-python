# Downloading body pose (COCO) model...
OPENPOSE_URL="https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-python/pose-models/"
COCO_FOLDER="coco/"
#
COCO_MODEL="coco/pose_iter_440000.caffemodel"
wget -c ${OPENPOSE_URL}${COCO_MODEL} -P ${COCO_FOLDER} --no-check-certificate
# Download finished.
