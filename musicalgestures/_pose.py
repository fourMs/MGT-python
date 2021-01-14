
import cv2
import os
import numpy as np
import pandas as pd
from musicalgestures._utils import MgProgressbar, convert_to_avi, extract_wav, embed_audio_in_video, roundup, frame2ms
import musicalgestures
import itertools

# implementation mainly inspired by: https://github.com/spmallick/learnopencv/blob/master/OpenPose/OpenPoseVideo.py


def pose(self, model='mpi', device='cpu', threshold=0.1, downsampling_factor=4, save_data=True, data_format='csv', save_video=True):
    """
    Renders a video with the pose estimation (aka. "keypoint detection" or "skeleton tracking") overlaid on it. Outputs the predictions in a text file (default format is csv). Uses models from the [openpose](https://github.com/CMU-Perceptual-Computing-Lab/openpose) project.

    Args:
        model (str, optional): 'mpi' loads the model trained on the Multi-Person Dataset (MPII), 'coco' loads one trained on the COCO dataset. The MPII model outputs 15 points, while the COCO model produces 18 points. Defaults to 'mpi'.
        device (str, optional): Sets the backend to use for the neural network ('cpu' or 'gpu'). Defaults to 'cpu'.
        threshold (float, optional): The normalized confidence threshold that decides whether we keep or discard a predicted point. Discarded points get substituted with (0, 0) in the output data. Defaults to 0.1.
        downsampling_factor (int, optional): Decides how much we downsample the video before we pass it to the neural network. For example `downsampling_factor=4` means that the input to the network is one-fourth the resolution of the source video. Heaviver downsampling reduces rendering time but produces lower quality pose estimation. Defaults to 4.
        save_data (bool, optional): Whether we save the predicted pose data to a file. Defaults to True.
        data_format (str or list, optional): Specifies format of pose-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
        save_video (bool, optional): Whether we save the video with the estimated pose overlaid on it. Defaults to True.

    Outputs:
        `filename`_pose.avi: The source video with pose overlay.
        `filename`_pose.`data_format`: A text file containing the normalized x and y coordinates of each keypoints (such as head, left shoulder, right shoulder, etc) for each frame in the source video with timecodes in milliseconds. Available formats: csv, tsv, txt.

    Returns:
        MgObject: An MgObject pointing to the output '_pose' video.
    """

    module_path = os.path.abspath(os.path.dirname(musicalgestures.__file__))

    if model.lower() == 'mpi':
        protoFile = module_path + '/pose/mpi/pose_deploy_linevec_faster_4_stages.prototxt'
        weightsFile = module_path + '/pose/mpi/pose_iter_160000.caffemodel'
        model = 'mpi'
        nPoints = 15
        POSE_PAIRS = [[0, 1], [1, 2], [2, 3], [3, 4], [1, 5], [5, 6], [6, 7], [
            1, 14], [14, 8], [8, 9], [9, 10], [14, 11], [11, 12], [12, 13]]
    elif model.lower() == 'coco':
        protoFile = module_path + '/pose/coco/pose_deploy_linevec.prototxt'
        weightsFile = module_path + '/pose/coco/pose_iter_440000.caffemodel'
        model = 'coco'
        nPoints = 18
        POSE_PAIRS = [[1, 0], [1, 2], [1, 5], [2, 3], [3, 4], [5, 6], [6, 7], [1, 8], [
            8, 9], [9, 10], [1, 11], [11, 12], [12, 13], [0, 14], [0, 15], [14, 16], [15, 17]]
    else:
        print(f'Unrecognized model "{model}", switching to default (mpi).')
        protoFile = module_path + '/pose/mpi/pose_deploy_linevec_faster_4_stages.prototxt'
        weightsFile = module_path + '/pose/mpi/pose_iter_160000.caffemodel'
        model = 'mpi'

    # Check if .caffemodel file exists, download if necessary
    if not os.path.exists(weightsFile):
        print('Could not find weights file. Do you want to download it (~200MB)? (y/n)')
        answer = input()
        if answer.lower() == 'n':
            print('Ok. Exiting...')
            return musicalgestures.MgObject(self.filename, color=self.color, returned_by_process=True)
        elif answer.lower() == 'y':
            download_model(model)
        else:
            print(f'Unrecognized answer "{answer}". Exiting...')
            return musicalgestures.MgObject(self.filename, color=self.color, returned_by_process=True)

    # Read the network into Memory
    net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)
    if device == "cpu":
        net.setPreferableBackend(cv2.dnn.DNN_TARGET_CPU)
    elif device == "gpu":
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
    else:
        print(f'Unrecognized device "{device}", switching to default (cpu).')
        net.setPreferableBackend(cv2.dnn.DNN_TARGET_CPU)

    of, fex = os.path.splitext(self.filename)

    if fex != '.avi':
        convert_to_avi(of + fex)
        fex = '.avi'
        filename = of + fex
    else:
        filename = self.filename

    vidcap = cv2.VideoCapture(filename)
    ret, frame = vidcap.read()

    fps = int(vidcap.get(cv2.CAP_PROP_FPS))
    width = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    length = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

    inWidth = int(roundup(width/downsampling_factor, 2))
    inHeight = int(roundup(height/downsampling_factor, 2))

    pb = MgProgressbar(total=length, prefix='Rendering pose estimation video:')

    if save_video:
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(of + '_pose' + fex, fourcc, fps, (width, height))

    ii = 0
    data = []

    while(vidcap.isOpened()):
        ret, frame = vidcap.read()
        if ret:

            inpBlob = cv2.dnn.blobFromImage(
                frame, 1.0 / 255, (inWidth, inHeight), (0, 0, 0), swapRB=False, crop=False)

            net.setInput(inpBlob)

            output = net.forward()

            H = output.shape[2]
            W = output.shape[3]
            points = []

            for i in range(nPoints):

                # confidence map of corresponding body's part.
                probMap = output[0, i, :, :]

                # Find global maxima of the probMap.
                minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)

                # Scale the point to fit on the original image
                x = (width * point[0]) / W
                y = (height * point[1]) / H

                if prob > threshold:
                    points.append((int(x), int(y)))

                else:
                    points.append(None)

            if save_data:
                time = frame2ms(ii, fps)
                points_list = [[list(point)[0]/width, list(point)[1]/height, ] if point != None else [
                    0, 0] for point in points]
                points_list_flat = itertools.chain.from_iterable(points_list)
                datapoint = [time]
                datapoint += points_list_flat
                data.append(datapoint)

            for pair in POSE_PAIRS:
                partA = pair[0]
                partB = pair[1]

                if points[partA] and points[partB]:
                    cv2.line(frame, points[partA], points[partB],
                             (0, 255, 255), 2, lineType=cv2.LINE_AA)
                    cv2.circle(
                        frame, points[partA], 4, (0, 0, 255), thickness=-1, lineType=cv2.FILLED)
                    cv2.circle(
                        frame, points[partB], 4, (0, 0, 255), thickness=-1, lineType=cv2.FILLED)

            if save_video:
                out.write(frame.astype(np.uint8))

        else:
            pb.progress(length)
            break

        pb.progress(ii)
        ii += 1

    if save_video:
        out.release()
        destination_video = of + '_pose' + fex
        if self.has_audio:
            source_audio = extract_wav(of + fex)
            embed_audio_in_video(source_audio, destination_video)
            os.remove(source_audio)

    def save_txt(of, width, height, model, data, data_format):
        """
        Helper function to export pose estimation data as textfile(s).
        """
        def save_single_file(of, width, height, model, data, data_format):
            """
            Helper function to export pose estimation data as a textfile using pandas.
            """

            coco_table = ['Nose', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder', 'Left Elbow', 'Left Wrist', 'Right Hip',
                          'Right Knee', 'Right Ankle', 'Left Hip', 'Left Knee', 'Left Ankle', 'Right Eye', 'Left Eye', 'Right Ear', 'Left Ear']
            mpi_table = ['Head', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder', 'Left Elbow',
                         'Left Wrist', 'Right Hip', 'Right Knee', 'Right Ankle', 'Left Hip', 'Left Knee', 'Left Ankle', 'Chest']
            headers = ['Time']

            table_to_use = []
            if model.lower() == 'mpi':
                table_to_use = mpi_table
            else:
                table_to_use = coco_table

            for i in range(len(table_to_use)):
                header_x = table_to_use[i] + ' X'
                header_y = table_to_use[i] + ' Y'
                headers.append(header_x)
                headers.append(header_y)

            data_format = data_format.lower()

            df = pd.DataFrame(data=data, columns=headers)

            if data_format == "tsv":
                with open(of+'_pose.tsv', 'wb') as f:
                    head_str = ''
                    for head in headers:
                        head_str += head + '\t'
                    head_str += '\n'
                    f.write(head_str.encode())
                    fmt_list = ['%d']
                    fmt_list += ['%.15f' for item in range(
                        len(table_to_use)*2)]
                    np.savetxt(f, df.values, delimiter='\t', fmt=fmt_list)

            elif data_format == "csv":
                df.to_csv(of+'_pose.csv', index=None)

            elif data_format == "txt":
                with open(of+'_pose.txt', 'wb') as f:
                    head_str = ''
                    for head in headers:
                        head_str += head + ' '
                    head_str += '\n'
                    f.write(head_str.encode())
                    fmt_list = ['%d']
                    fmt_list += ['%.15f' for item in range(
                        len(table_to_use)*2)]
                    np.savetxt(f, df.values, delimiter=' ', fmt=fmt_list)
            elif data_format not in ["tsv", "csv", "txt"]:
                print(
                    f"Invalid data format: '{data_format}'.\nFalling back to '.csv'.")

        if type(data_format) == str:
            save_single_file(of, width, height, model, data, data_format)

        elif type(data_format) == list:
            if all([item.lower() in ["csv", "tsv", "txt"] for item in data_format]):
                data_format = list(set(data_format))
                [save_single_file(of, width, height, model, data, item)
                 for item in data_format]
            else:
                print(
                    f"Unsupported formats in {data_format}.\nFalling back to '.csv'.")
                save_single_file(of, width, height, model, data, "csv")

    save_txt(of, width, height, model, data, data_format)

    return musicalgestures.MgObject(destination_video, color=self.color, returned_by_process=True)


def download_model(modeltype):
    """
    Helper function to automatically download model (.caffemodel) files.
    """
    import platform
    import subprocess
    import os
    import musicalgestures

    module_path = os.path.abspath(os.path.dirname(musicalgestures.__file__))

    batch, shell = '_remote.bat', '_remote.sh'

    the_system = platform.system()

    pb_prefix = ''
    mpi_script = module_path + '/pose/getMPI'
    coco_script = module_path + '/pose/getCOCO'
    wget_win = module_path + '/3rdparty/windows/wget/wget.exe'
    target_folder_mpi = module_path + '/pose/mpi'
    target_folder_coco = module_path + '/pose/coco'

    if the_system == 'Windows':
        mpi_script += batch
        coco_script += batch
    else:
        mpi_script += shell
        coco_script += shell

    if modeltype.lower() == 'mpi':
        command = mpi_script
        if the_system == 'Windows':
            command += f' {wget_win} {target_folder_mpi}'
        else:
            command = 'sudo -S bash ' + command
            command += f' {target_folder_mpi}'
        pb_prefix = 'Downloading MPI model:'
    else:
        command = coco_script
        if the_system == 'Windows':
            command += f' {wget_win} {target_folder_coco}'
        else:
            command = 'sudo -S bash ' + command
            command += f' {target_folder_coco}'
        pb_prefix = 'Downloading COCO model:'

    pb = MgProgressbar(total=100, prefix=pb_prefix)

    if the_system == 'Windows':
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
    else:
        try:
            import getpass
            username = getpass.getuser()
            print(f'[sudo] password for {username}:')
            p = getpass.getpass() 
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, universal_newlines=True, shell=True)
            process.stdin.write(p+'\n')
            process.stdin.flush()
        except Exception as error: 
            print('ERROR', error)

    try:
        while True:
            out = process.stdout.readline()
            if out == '':
                process.wait()
                break
            elif out.find('%') != -1:
                percentage_place = out.find('%')
                percent = out[percentage_place-2:percentage_place]
                pb.progress(float(percent))
            else:
                print(out)

        # pb.progress(100)

    except KeyboardInterrupt:
        try:
            process.terminate()
        except OSError:
            pass
        process.wait()
        raise KeyboardInterrupt
