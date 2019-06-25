import numpy as np
import cv2

def contrast_brightness(of,vidcap,fps,width,height,contrast,brightness):
    count = 0;
    if brightness != 0 or contrast != 0:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_cb.avi',fourcc, fps, (width,height))
        success,image = vidcap.read()
        while success: 
            success,image = vidcap.read()
            if not success:
                break
            image = np.int16(image) * (contrast/127+1) - contrast + brightness
            image = np.clip(image, 0, 255)
            out.write(image.astype(np.uint8))  
            count += 1
        out.release()
        vidcap = cv2.VideoCapture(of + '_cb.avi')

    return vidcap

def skip_frames(of, vidcap, skip, fps, width, height):
    count = 0;
    if skip != 0:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_skip.avi',fourcc, int(fps/skip), (width,height))
        success,image = vidcap.read()
        while success: 
            success,image = vidcap.read()
            if not success:
                break
            # on every frame we wish to use
            if (count % skip ==0):
              out.write(image.astype(np.uint8))  
            
            count += 1
        out.release()
        vidcap = cv2.VideoCapture(of + '_skip.avi')

        length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(vidcap.get(cv2.CAP_PROP_FPS))
        width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return vidcap, length, fps, width, height