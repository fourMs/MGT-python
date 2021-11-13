# Downloading body pose (BODY_25) model...
BODY_25_FOLDER="$1"
# 
wget -c "https://www.uio.no/ritmo/english/research/labs/fourms/software/musicalgesturestoolbox/mgt-python/pose-models/body25/pose_iter_584000.caffemodel" -P ${BODY_25_FOLDER} --no-check-certificate 
# Download finished.