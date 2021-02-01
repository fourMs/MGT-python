import cv2
import numpy as np
import argparse

global frame_mask, drawing, g_val, x_start, x_stop, y_start, y_stop
x_start, y_start = -1, -1
x_stop, y_stop = -1, -1
drawing = False


def draw_rectangle(event, x, y, flags, param):
    """
    Helper function to render a cropping window to the user in case of manual cropping, using cv2.
    """
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


parser = argparse.ArgumentParser(
    description='Create (memory-safe) user interface for manual cropping.')

parser.add_argument('Path', metavar='path', type=str, help='path to file')
parser.add_argument('Ratio', metavar='ratio', type=float, help='scale ratio')
parser.add_argument('Width', metavar='width', type=int, help='scaled width')
parser.add_argument('Height', metavar='height', type=int, help='scaled height')

args = parser.parse_args()

imgpath = args.Path
scale_ratio = args.Ratio
scaled_width, scaled_height = args.Width, args.Height

frame = cv2.imread(imgpath)
frame_scaled = cv2.resize(frame, (scaled_width, scaled_height))
frame_mask = np.zeros(frame_scaled.shape)
name_str = 'Draw rectangle and press "C" to crop'
cv2.namedWindow(name_str, cv2.WINDOW_AUTOSIZE)
cv2.setMouseCallback(name_str, draw_rectangle, param=frame_scaled)
g_val = 220
while(1):
    cv2.imshow(name_str, frame_scaled*(frame_mask != g_val) +
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

w, h, x, y = x_stop - x_start, y_stop - y_start, x_start, y_start

if scale_ratio < 1:
    w, h, x, y = [int(elem / scale_ratio) for elem in [w, h, x, y]]

print(w, h, x, y)
