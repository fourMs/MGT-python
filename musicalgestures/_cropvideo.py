import cv2
import os
import numpy as np
import time
from musicalgestures._utils import MgProgressbar
from musicalgestures._filter import filter_frame


def mg_cropvideo(
        fps,
        width,
        height,
        length,
        of,
        fex,
        crop_movement='Auto',
        motion_box_thresh=0.1,
        motion_box_margin=1):
    """
    Crops the video.

    Parameters
    ----------
    - fps : int

        The FPS (frames per second) of the input video capture.
    - width : int

        The pixel width of the input video capture. 
    - height : int

        The pixel height of the input video capture. 
    - length : int

        The number of frames in the input video capture.
    - of : str

        'Only filename' without extension (but with path to the file).
    - fex : str

        File extension.
    - crop_movement : {'Auto','Manual'}, optional

        'Auto' finds the bounding box that contains the total motion in the video.
        Motion threshold is given by motion_box_thresh. 'Manual' opens up a simple 
        GUI that is used to crop the video manually by looking at the first frame.
    - motion_box_thresh : float, optional

        Only meaningful if `crop_movement='Auto'`. Takes floats between 0 and 1,
        where 0 includes all the motion and 1 includes none.
    - motion_box_margin : int, optional

        Only meaningful if `crop_movement='Auto'`. Adds margin to the bounding box.
    """

    global frame_mask, drawing, g_val, x_start, x_stop, y_start, y_stop
    x_start, y_start = -1, -1
    x_stop, y_stop = -1, -1

    drawing = False
    pb = MgProgressbar(total=length, prefix='Rendering cropped video:')

    vid2crop = cv2.VideoCapture(of + fex)
    vid2findbox = cv2.VideoCapture(of + fex)

    ret, frame = vid2crop.read()

    if crop_movement.lower() == 'manual':
        frame_mask = np.zeros(frame.shape)
        name_str = 'Draw rectangle and press "C" to crop'
        cv2.namedWindow(name_str)
        cv2.setMouseCallback(name_str, draw_rectangle, param=frame)
        g_val = 220
        while(1):
            cv2.imshow(name_str, frame*(frame_mask != g_val) +
                       frame_mask.astype(np.uint8))
            k = cv2.waitKey(1) & 0xFF
            if k == ord('c') or k == ord('C'):
                break
        cv2.destroyAllWindows()

        if x_stop < x_start:
            temp = x_start
            x_start = x_stop
            x_stop = temp
        if y_stop < y_start:
            temp = y_start
            y_start = y_stop
            y_stop = temp
    elif crop_movement.lower() == 'auto':
        [x_start, x_stop, y_start, y_stop] = find_total_motion_box(
            vid2findbox, width, height, length, motion_box_thresh, motion_box_margin)
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    out = cv2.VideoWriter(of + '_crop' + fex, fourcc, fps,
                          (int(x_stop-x_start), (int(y_stop-y_start))))
    ii = 0
    while (vid2crop.isOpened()):
        if ret:
            frame_temp = frame[y_start:y_stop, x_start:x_stop, :]
            out.write(frame_temp)
            ret, frame = vid2crop.read()
        else:
            pb.progress(length)
            # mg_progressbar(
            #     length, length, 'Rendering cropped video:', 'Complete')
            break
        pb.progress(ii)
        ii += 1
        # mg_progressbar(ii, length+1, 'Rendering cropped video:', 'Complete')

    vid2crop.release()
    out.release()
    cv2.destroyAllWindows()

    vidcap = cv2.VideoCapture(of + '_crop' + fex)
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return vidcap, width, height


def draw_rectangle(event, x, y, flags, param):
    global x_start, y_start, x_stop, y_stop, drawing, frame_mask
    if event == cv2.EVENT_LBUTTONDOWN:
        frame_mask = np.zeros(param.shape)
        drawing = True
        x_start, y_start = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing == True:
            frame_mask = np.zeros(param.shape)
            cv2.rectangle(frame_mask, (x_start, y_start),
                          (x, y), (g_val, g_val, g_val), 1)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x_stop, y_stop = x, y
        cv2.rectangle(frame_mask, (x_start, y_start),
                      (x, y), (g_val, g_val, g_val), 1)


def find_motion_box(grayimage, width, height, motion_box_margin):
    prev_Start = width
    prev_Stop = 0

    the_box = np.zeros([height, width])
    # ----Finding left and right edges
    le = int(width/2)
    re = int(width/2)
    for i in range(height):
        row = grayimage[i, :]
        inds = np.where(row > 0)[0]
        if len(inds) > 0:
            Start = inds[0]
            if Start < prev_Start:
                le = Start
                prev_Start = Start
            if len(inds) > 1:
                Stop = inds[-1]
                if Stop > prev_Stop:
                    re = Stop
                    prev_Stop = Stop

    # ---- Finding top and bottom edges
    prev_Start = height
    prev_Stop = 0
    te = int(height/2)
    be = int(height/2)
    for j in range(width):
        col = grayimage[:, j]
        inds = np.where(col > 0)[0]
        if len(inds) > 0:
            Start = inds[0]
            if Start < prev_Start:
                te = Start
                prev_Start = Start
            if len(inds) > 1:
                Stop = inds[-1]
                if Stop > prev_Stop:
                    be = Stop
                    prev_Stop = Stop

    margin = motion_box_margin

    x_start = np.clip(le-margin, 0, width-1)
    x_stop = np.clip(re+margin, 0, width-1)
    y_start = np.clip(te-margin, 0, height-1)
    y_stop = np.clip(be+margin, 0, height-1)

    the_box[np.clip(te-margin, 0, height-1), np.clip(le-margin,
                                                     0, width-1):np.clip(re+margin, 0, width-1)] = 1
    the_box[np.clip(te-margin, 0, height-1):np.clip(be+margin,
                                                    0, height-1), np.clip(le-margin, 0, width-1)] = 1
    the_box[np.clip(be+margin, 0, height-1), np.clip(le-margin,
                                                     0, width-1):np.clip(re+margin, 0, width-1)] = 1
    the_box[np.clip(te-margin, 0, height-1):np.clip(be+margin,
                                                    0, height-1), np.clip(re+margin, 0, width-1)] = 1

    return the_box, x_start, x_stop, y_start, y_stop


def find_total_motion_box(vid2findbox, width, height, length, motion_box_thresh, motion_box_margin):
    total_box = np.zeros([height, width])
    ret, frame = vid2findbox.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    pb = MgProgressbar(total=length, prefix='Finding area of motion:')
    ii = 0
    while(vid2findbox.isOpened()):
        prev_frame = frame.astype(np.int32)
        ret, frame = vid2findbox.read()
        if ret == True:
            pb.progress(ii)
            ii += 1
            # mg_progressbar(ii, length, 'Finding area of motion:', 'Complete')
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = frame.astype(np.int32)

            motion_frame = (np.abs(frame-prev_frame)).astype(np.uint8)
            motion_frame = filter_frame(
                motion_frame, 'Regular', thresh=motion_box_thresh, kernel_size=5)

            [the_box, x_start, x_stop, y_start, y_stop] = find_motion_box(
                motion_frame, width, height, motion_box_margin)
            total_box = total_box*(the_box == 0)+the_box
        else:
            [total_motion_box, x_start, x_stop, y_start, y_stop] = find_motion_box(
                total_box, width, height, motion_box_margin)
            pb.progress(length)
            # mg_progressbar(
            #     length, length, 'Finding area of motion:', 'Complete')
            break

    return x_start, x_stop, y_start, y_stop
