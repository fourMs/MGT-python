# Downloading body pose (COCO) model...
COCO_FOLDER="$1"
# COCO_MODEL="coco/pose_iter_440000.caffemodel"
wget -c "https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-python/pose-models/coco/pose_iter_440000.caffemodel" -P ${COCO_FOLDER} --no-check-certificate 
# Download finished.
