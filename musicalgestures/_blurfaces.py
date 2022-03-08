import os
import cv2
import subprocess
import numpy as np
import skimage.draw

import musicalgestures
from musicalgestures._centerface import CenterFace
from musicalgestures._utils import MgProgressbar, convert_to_avi, generate_outfilename, wrap_str

def scaling_mask(x1, y1, x2, y2, mask_scale=1.0):
    s = mask_scale - 1.0
    h, w = y2 - y1, x2 - x1
    y1 -= h * s
    y2 += h * s
    x1 -= w * s
    x2 += w * s
    return np.round([x1, y1, x2, y2]).astype(int)

def mg_blurfaces(self, mask='blur', mask_image=None, mask_scale=1.0, ellipse=True, draw_scores=False, color=(0, 0, 0), target_name=None, overwrite=False):

    of, fex = os.path.splitext(self.filename)

    if fex != '.avi':
        # first check if there already is a converted version, if not create one and register it to self
        if "as_avi" not in self.__dict__.keys():
            file_as_avi = convert_to_avi(of + fex, overwrite=overwrite)
            # register it as the avi version for the file
            self.as_avi = musicalgestures.MgVideo(file_as_avi)
        # point of and fex to the avi version
        of, fex = self.as_avi.of, self.as_avi.fex
        filename = of + fex
    else:
        filename = self.filename
    
    if target_name == None:
        target_name = of + '_blurred.avi'
    else:
        # enforce avi
        target_name = os.path.splitext(target_name)[0] + '.avi'
    if not overwrite:
        target_name = generate_outfilename(target_name)
    if os.path.isfile(target_name):
        os.remove(target_name)       
    temp_file_name = of + '_temp.avi'

    vidcap = cv2.VideoCapture(filename)
    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

    pb = MgProgressbar(total=length, prefix='Blurring faces:')

    centerface = CenterFace()

    ret, frame = vidcap.read()
    output_stream = cv2.VideoWriter(temp_file_name, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame.shape[1], frame.shape[0]))

    i = 0

    while vidcap.isOpened():

        ret, frame = vidcap.read()
       
        if ret == True:

            h, w = frame.shape[:2]
            dets, lms = centerface(frame, h, w, threshold=0.2)

            for x, det in enumerate(dets):

                boxes, score = det[:4], det[4]
                x1, y1, x2, y2 = boxes.astype(int)
                x1, y1, x2, y2 = scaling_mask(x1, y1, x2, y2, mask_scale)
                # Clip bb coordinates to valid frame region
                y1, y2 = max(0, y1), min(frame.shape[0] - 1, y2)
                x1, x2 = max(0, x1), min(frame.shape[1] - 1, x2)

                # Mask faces with rectangles
                if mask == 'rectangle':
                    # Color is set to black by default but can be changed using the color parameter.
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, -1)

                # Mask faces with blurred rectangles
                elif mask == 'blur':
                    bf = 2  # blur factor (number of pixels in each dimension that the face will be reduced to)
                    blurred_box = cv2.blur(frame[y1:y2, x1:x2], (abs(x2 - x1) // bf, abs(y2 - y1) // bf))
                    # Mask faces with blurred ellipses
                    if ellipse:
                        roibox = frame[y1:y2, x1:x2]
                        # Get y and x coordinate lists of the "bounding ellipse"
                        ey, ex = skimage.draw.ellipse((y2 - y1) // 2, (x2 - x1) // 2, (y2 - y1) // 2, (x2 - x1) // 2)
                        roibox[ey, ex] = blurred_box[ey, ex]
                        frame[y1:y2, x1:x2] = roibox
                    else:
                        frame[y1:y2, x1:x2] = blurred_box

                # Mask faces with a choosen image
                elif mask == 'image':
                    target_size = (x2 - x1, y2 - y1)
                    # Reading image with opencv
                    mask_image = cv2.imread(mask_image, cv2.IMREAD_UNCHANGED)
                    # Resizing with the target size
                    resized_mask_image = cv2.resize(mask_image, target_size)
                    if mask_image.shape[2] == 3:  # RGB
                        frame[y1:y2, x1:x2] = resized_mask_image
                    elif mask_image.shape[2] == 4:  # RGBA
                        frame[y1:y2, x1:x2] = frame[y1:y2, x1:x2] * (1 - resized_mask_image[:, :, 3:] / 255) + resized_mask_image[:, :, :3] * (resized_mask_image[:, :, 3:] / 255)
                
                # Mask nothing
                elif mask == 'none':
                    pass

                # Draw the faceness score (between 0 and 1) that roughly corresponds to the detector's confidence that something is a face.
                if draw_scores:
                    cv2.putText(frame, f'{score:.2f}', (x1 + 0, y1 - 20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0))

            output_stream.write(frame)

        else:
            pb.progress(length)
            break
       
        pb.progress(i)
        i += 1

    output_stream.release()
    vidcap.release()

    cmd = f'ffmpeg -i {temp_file_name} -c:v copy -c:a aac -strict experimental {wrap_str(target_name)}'
    subprocess.check_call(cmd, shell=True)   
    os.remove(temp_file_name)

    # save warped video as warping_audiovisual_beats for parent MgVideo
    # we have to do this here since we are not using mg_warping_audiovisual_beats (that would normally save the result itself)
    self.blur_faces = musicalgestures.MgVideo(target_name, color=self.color, returned_by_process=True)

    return self.blur_faces
    
