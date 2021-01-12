# Downloading body pose (COCO) model...

OPENPOSE_URL="http://posefs1.perception.cs.cmu.edu/OpenPose/models/"
COCO_FOLDER="$1"

#

COCO_MODEL="pose/coco/pose_iter_440000.caffemodel"
wget -c ${OPENPOSE_URL}${COCO_MODEL} -P ${COCO_FOLDER}

# Download finished.
