import multiprocessing
import numpy as np
import os
import argparse
import cv2
import sys
try:
    import musicalgestures
except:
    # local dev mode
    sys.path.append('../')
    import musicalgestures
from musicalgestures._utils import frame2ms
from musicalgestures._centroid import centroid
from musicalgestures._filter import filter_frame
import socket


def mg_motion_mp(args):

    target_folder, of, fex, fps, width, height, length, color, filtertype, thresh, blur, kernel_size, inverted_motionvideo, inverted_motiongram, equalize_motiongram, save_data, save_motiongrams, save_video, start_frame, num_frames, process_id, client = args

    # init
    target_name_video = None
    gramx = None
    gramy = None
    time = None
    qom = None
    com = None
    out = None
    fourcc = None
    process_id_str = '{:02d}'.format(process_id)

    # ignore runtime warnings when dividing by 0
    np.seterr(divide='ignore', invalid='ignore')

    # load video
    vidcap = cv2.VideoCapture(of+fex)

    # set start frame
    vidcap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    ret, frame = vidcap.read()

    if save_video:
        target_name_video = target_folder + of + '_motion_' + process_id_str + fex
        # print(target_name_video)
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(target_name_video, fourcc, fps, (width, height))

    if save_motiongrams:
        gramx = np.zeros([1, width, 3])
        gramy = np.zeros([height, 1, 3])
    if save_data:
        time = np.array([])  # time in ms
        qom = np.array([])  # quantity of motion
        com = np.array([])  # centroid of motion

    ii = 0

    if color == False:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if save_motiongrams:
            gramx = np.zeros([1, width])
            gramy = np.zeros([height, 1])

    try:
        while(ii < num_frames):
            # report progress
            client.sendall(bytes("progress:" + str(process_id) + " " + str(ii), 'utf-8'))

            if blur.lower() == 'average':
                prev_frame = cv2.blur(frame, (10, 10))
            elif blur.lower() == 'none':
                prev_frame = frame

            ret, frame = vidcap.read()

            if not ret:
                break

            if blur.lower() == 'average':
                # The higher these numbers the more blur you get
                frame = cv2.blur(frame, (10, 10))

            if color == False:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            frame = np.array(frame)
            frame = frame.astype(np.int32)

            if color == True:
                motion_frame_rgb = np.zeros(
                    [height, width, 3])

                for i in range(frame.shape[2]):
                    motion_frame = (
                        np.abs(frame[:, :, i]-prev_frame[:, :, i])).astype(np.uint8)
                    motion_frame = filter_frame(
                        motion_frame, filtertype, thresh, kernel_size)
                    motion_frame_rgb[:, :, i] = motion_frame

                if save_motiongrams:
                    movement_y = np.mean(motion_frame_rgb, axis=1).reshape(height, 1, 3)
                    movement_x = np.mean(motion_frame_rgb, axis=0).reshape(1, width, 3)
                    gramy = np.append(gramy, movement_y, axis=1)
                    gramx = np.append(gramx, movement_x, axis=0)

            else:
                motion_frame = (
                    np.abs(frame-prev_frame)).astype(np.uint8)
                motion_frame = filter_frame(
                    motion_frame, filtertype, thresh, kernel_size)

                if save_motiongrams:
                    movement_y = np.mean(
                        motion_frame, axis=1).reshape(height, 1)
                    movement_x = np.mean(
                        motion_frame, axis=0).reshape(1, width)
                    gramy = np.append(gramy, movement_y, axis=1)
                    gramx = np.append(gramx, movement_x, axis=0)

            if color == False:
                motion_frame = cv2.cvtColor(
                    motion_frame, cv2.COLOR_GRAY2BGR)
                motion_frame_rgb = motion_frame

            if save_video:
                # if this is not the first process (rendering the start of the video) then don't save the first frame of the output (it'll always be black).
                if process_id != 0 and ii > 0:
                    if inverted_motionvideo:
                        out.write(cv2.bitwise_not(
                            motion_frame_rgb.astype(np.uint8)))
                    else:
                        out.write(motion_frame_rgb.astype(np.uint8))
                elif process_id == 0:
                    if inverted_motionvideo:
                        out.write(cv2.bitwise_not(
                            motion_frame_rgb.astype(np.uint8)))
                    else:
                        out.write(motion_frame_rgb.astype(np.uint8))


            if save_data:
                combite, qombite = centroid(motion_frame_rgb.astype(
                    np.uint8), width, height)
                if ii == 0:
                    time = frame2ms(ii, fps)
                    com = combite.reshape(1, 2)
                    qom = qombite
                else:
                    time = np.append(time, frame2ms(ii, fps))
                    com = np.append(com, combite.reshape(1, 2), axis=0)
                    qom = np.append(qom, qombite)

            ii += 1

    except:
        vidcap.release()
        if save_video:
            out.release()

    if save_motiongrams:
        # save grams to npy files
        with open(target_folder + f'gramx_{process_id_str}.npy', 'wb') as f:
            np.save(f, gramx)
        with open(target_folder + f'gramy_{process_id_str}.npy', 'wb') as f:
            np.save(f, gramy)

    if save_data:
        # save data to npy files
        with open(target_folder + f'time_{process_id_str}.npy', 'wb') as f:
            np.save(f, time)
        with open(target_folder + f'com_{process_id_str}.npy', 'wb') as f:
            np.save(f, com)
        with open(target_folder + f'qom_{process_id_str}.npy', 'wb') as f:
            np.save(f, qom)

    # resetting numpy warnings for dividing by 0
    np.seterr(divide='warn', invalid='warn')

    vidcap.release()
    if save_video:
        out.release()


def run_pool(func, args, numprocesses):
    pool = multiprocessing.Pool(numprocesses)
    # results = pool.map(func, args)
    pool.map(func, args)
    # return results


def calc_frame_groups(framecount, num_cores):
    import math
    groups = [] # [startframe, numframes]
    frames_per_core = math.floor(framecount / num_cores)
    remaining = framecount - (num_cores * frames_per_core)

    for i in range(num_cores):
        startframe = i * frames_per_core
        numframes = frames_per_core + 1 if i < num_cores-1 else frames_per_core + remaining
        groups.append([startframe, numframes])

    return groups


def testhogfunc(process_id):
    limit = 20
    count = 0
    while count < limit:
        print(process_id, count)
        futyi = 0
        for i in range(10_000_000):
            futyi += 1
        count += 1
    return process_id, count


def bool_from_str(boolstring):
    return True if boolstring == "True" else False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Render motion video and data in a multicore process')
    parser.add_argument('target_folder', metavar='target_folder', type=str, help='path to temporary folder')
    parser.add_argument('of', metavar='of', type=str, help='filename without path or ext')
    parser.add_argument('fex', metavar='fex', type=str, help='file extension including dot')
    parser.add_argument('fps', metavar='fps', type=str, help='fps')
    parser.add_argument('width', metavar='width', type=str, help='width')
    parser.add_argument('height', metavar='height', type=str, help='height')
    parser.add_argument('length', metavar='length', type=str, help='length')
    parser.add_argument('color', metavar='color', type=str, help='color')
    parser.add_argument('filtertype', metavar='filtertype', type=str, help='filtertype')
    parser.add_argument('thresh', metavar='thresh', type=str, help='thresh')
    parser.add_argument('blur', metavar='blur', type=str, help='blur')
    parser.add_argument('kernel_size', metavar='kernel_size', type=str, help='kernel_size')
    parser.add_argument('inverted_motionvideo', metavar='inverted_motionvideo', type=str, help='inverted_motionvideo')
    parser.add_argument('inverted_motiongram', metavar='inverted_motiongram', type=str, help='inverted_motiongram')
    parser.add_argument('equalize_motiongram', metavar='equalize_motiongram', type=str, help='equalize_motiongram')
    parser.add_argument('save_data', metavar='save_data', type=str, help='save_data')
    parser.add_argument('save_motiongrams', metavar='save_motiongrams', type=str, help='save_motiongrams')
    parser.add_argument('save_video', metavar='save_video', type=str, help='save_video')

    args = parser.parse_args()

    HOST = '127.0.0.1'  # The server's hostname or IP address
    PORT = 65432        # The port used by the server

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    target_folder = os.path.abspath(args.target_folder).replace('\\', '/')
    if target_folder[-1] != "/":
        target_folder += '/'

    of, fex = args.of, args.fex
    fps, width, height, length = int(float(args.fps)), int(float(args.width)), int(float(args.height)), int(float(args.length))
    color, filtertype, thresh, blur, kernel_size = bool_from_str(args.color), args.filtertype, float(args.thresh), args.blur, int(float(args.kernel_size))
    inverted_motionvideo, inverted_motiongram, equalize_motiongram = bool_from_str(args.inverted_motionvideo), bool_from_str(args.inverted_motiongram), bool_from_str(args.equalize_motiongram)
    save_data, save_motiongrams, save_video = bool_from_str(args.save_data), bool_from_str(args.save_motiongrams), bool_from_str(args.save_video) 

    numprocessors = multiprocessing.cpu_count()
    frame_groups = calc_frame_groups(length, numprocessors)

    feed_args = []

    for i in range(numprocessors):
        start_frame, num_frames = frame_groups[i]
        initargs = [target_folder, of, fex, fps, width, height, length, color, filtertype, thresh, blur, kernel_size, inverted_motionvideo, inverted_motiongram, equalize_motiongram, save_data, save_motiongrams, save_video, start_frame, num_frames, i, client]
        # client.sendall(bytes(str(initargs), 'utf-8'))
        feed_args.append(initargs)

    # results = run_pool(mg_motion_mp, feed_args, numprocessors)
    run_pool(mg_motion_mp, feed_args, numprocessors)

    client.close()
    # print("Closed socket client.")