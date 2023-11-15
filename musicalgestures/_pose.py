
import cv2
import os
import numpy as np
import pandas as pd
from musicalgestures._utils import MgProgressbar, convert_to_avi, extract_wav, embed_audio_in_video, roundup, frame2ms, generate_outfilename, in_colab
import musicalgestures
import itertools

# implementation mainly inspired by: https://github.com/spmallick/learnopencv/blob/master/OpenPose/OpenPoseVideo.py


def pose(
        self,
        model='body_25',
        device='gpu',
        threshold=0.1,
        downsampling_factor=2,
        save_data=True,
        data_format='csv',
        save_video=True,
        target_name_video=None,
        target_name_data=None,
        overwrite=False):
    """
    Renders a video with the pose estimation (aka. "keypoint detection" or "skeleton tracking") overlaid on it. 
    Outputs the predictions in a text file containing the normalized x and y coordinates of each keypoints 
    (default format is csv). Uses models from the [openpose](https://github.com/CMU-Perceptual-Computing-Lab/openpose) project.

    Args:
        model (str, optional): 'body_25' loads the model trained on the BODY_25 dataset, 'mpi' loads the model trained on the Multi-Person Dataset (MPII), 'coco' loads one trained on the COCO dataset. The BODY_25 model outputs 25 points, the MPII model outputs 15 points, while the COCO model produces 18 points. Defaults to 'body_25'.
        device (str, optional): Sets the backend to use for the neural network ('cpu' or 'gpu'). Defaults to 'gpu'.
        threshold (float, optional): The normalized confidence threshold that decides whether we keep or discard a predicted point. Discarded points get substituted with (0, 0) in the output data. Defaults to 0.1.
        downsampling_factor (int, optional): Decides how much we downsample the video before we pass it to the neural network. For example `downsampling_factor=4` means that the input to the network is one-fourth the resolution of the source video. Heaviver downsampling reduces rendering time but produces lower quality pose estimation. Defaults to 2.
        save_data (bool, optional): Whether we save the predicted pose data to a file. Defaults to True.
        data_format (str, optional): Specifies format of pose-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, eg. ['csv', 'txt']. Defaults to 'csv'.
        save_video (bool, optional): Whether we save the video with the estimated pose overlaid on it. Defaults to True.
        target_name_video (str, optional): Target output name for the video. Defaults to None (which assumes that the input filename with the suffix "_pose" should be used).
        target_name_data (str, optional): Target output name for the data. Defaults to None (which assumes that the input filename with the suffix "_pose" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgVideo: An MgVideo pointing to the output video.
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
    elif model.lower() == 'body_25':
        protoFile = module_path + '/pose/body_25/pose_deploy.prototxt'
        weightsFile = module_path + '/pose/body_25/pose_iter_584000.caffemodel'
        model = 'body_25'
        nPoints = 25
        POSE_PAIRS = [[1, 8], [1, 2], [1, 5], [2, 3], [3, 4], [5, 6], [6, 7], [8, 9], [9, 10], [10, 11], [8, 12], [12, 13], [
            13, 14], [1, 0], [0, 15], [15, 17], [0, 16], [16, 18], [14, 19], [19, 20], [14, 21], [11, 22], [22, 23], [11, 24]]
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
            return musicalgestures.MgVideo(self.filename, color=self.color, returned_by_process=True)
        elif answer.lower() == 'y':
            download_model(model)
        else:
            print(f'Unrecognized answer "{answer}". Exiting...')
            return musicalgestures.MgVideo(self.filename, color=self.color, returned_by_process=True)

    # Read the network into Memory
    net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)
    device = device.lower()
    # enforce CPU device in Colab
    if in_colab() and device == 'gpu':
        print('Sorry, OpenCV GPU acceleration is not supported in Colab. Switching to CPU.')
        device = 'cpu'

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
        # first check if there already is a converted version, if not create one and register it to the parent self
        if "as_avi" not in self.__dict__.keys():
            file_as_avi = convert_to_avi(of + fex, overwrite=overwrite)
            # register it as the avi version for the file
            self.as_avi = musicalgestures.MgVideo(file_as_avi)
        # point of and fex to the avi version
        of, fex = self.as_avi.of, self.as_avi.fex
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
        if target_name_video == None:
            target_name_video = of + '_pose' + fex
        # if a target name was given we still enforce the .avi container anyway
        else:
            target_name_video = os.path.splitext(target_name_video) + fex
        if not overwrite:
            target_name_video = generate_outfilename(target_name_video)
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(target_name_video, fourcc, fps, (width, height))

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
        destination_video = target_name_video
        if self.has_audio:
            source_audio = extract_wav(of + fex)
            embed_audio_in_video(source_audio, destination_video)
            os.remove(source_audio)

    def save_txt(of, width, height, model, data, data_format, target_name_data, overwrite):
        """
        Helper function to export pose estimation data as textfile(s).
        """
        def save_single_file(of, width, height, model, data, data_format, target_name_data, overwrite):
            """
            Helper function to export pose estimation data as a textfile using pandas.
            """

            coco_table = ['Nose', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder', 'Left Elbow', 'Left Wrist', 'Right Hip',
                          'Right Knee', 'Right Ankle', 'Left Hip', 'Left Knee', 'Left Ankle', 'Right Eye', 'Left Eye', 'Right Ear', 'Left Ear']
            mpi_table = ['Head', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder', 'Left Elbow',
                         'Left Wrist', 'Right Hip', 'Right Knee', 'Right Ankle', 'Left Hip', 'Left Knee', 'Left Ankle', 'Chest']
            body_25_table = ['Nose', 'Neck', 'Right Shoulder', 'Right Elbow', 'Right Wrist', 'Left Shoulder', 'Left Elbow', 'Left Wrist', 'Mid Hip', 'Right Hip', 'Right Knee', 'Right Ankle', 'Left Hip',
                             'Left Knee', 'Left Ankle', 'Right Eye', 'Left Eye', 'Right Ear', 'Left Ear', "Left Big Toe", "Left Small Toe", "Left Heel", "Right Big Toe", "Right Small Toe", "Right Heel"]
            headers = ['Time']

            table_to_use = []
            if model.lower() == 'mpi':
                table_to_use = mpi_table
            elif model.lower() == 'coco':
                table_to_use = coco_table
            elif model.lower() == 'body_25':
                table_to_use = body_25_table

            for i in range(len(table_to_use)):
                header_x = table_to_use[i] + ' X'
                header_y = table_to_use[i] + ' Y'
                headers.append(header_x)
                headers.append(header_y)

            data_format = data_format.lower()

            df = pd.DataFrame(data=data, columns=headers)

            if data_format == "tsv":

                if target_name_data == None:
                    target_name_data = of+'_pose.tsv'
                else:
                    # take name, but enforce tsv
                    target_name_data = os.path.splitext(
                        target_name_data)[0] + '.tsv'
                if not overwrite:
                    target_name_data = generate_outfilename(target_name_data)

                with open(target_name_data, 'wb') as f:
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

                if target_name_data == None:
                    target_name_data = of+'_pose.csv'
                else:
                    # take name, but enforce csv
                    target_name_data = os.path.splitext(
                        target_name_data)[0] + '.csv'
                if not overwrite:
                    target_name_data = generate_outfilename(target_name_data)

                df.to_csv(target_name_data, index=None)

            elif data_format == "txt":

                if target_name_data == None:
                    target_name_data = of+'_pose.txt'
                else:
                    # take name, but enforce txt
                    target_name_data = os.path.splitext(
                        target_name_data)[0] + '.txt'
                if not overwrite:
                    target_name_data = generate_outfilename(target_name_data)

                with open(target_name_data, 'wb') as f:
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
                save_single_file(of, width, height, model, data, "csv",
                                 target_name_data=target_name_data, overwrite=overwrite)

        if type(data_format) == str:
            save_single_file(of, width, height, model, data, data_format,
                             target_name_data=target_name_data, overwrite=overwrite)

        elif type(data_format) == list:
            if all([item.lower() in ["csv", "tsv", "txt"] for item in data_format]):
                data_format = list(set(data_format))
                [save_single_file(of, width, height, model, data, item, target_name_data=target_name_data, overwrite=overwrite)
                 for item in data_format]
            else:
                print(
                    f"Unsupported formats in {data_format}.\nFalling back to '.csv'.")
                save_single_file(of, width, height, model, data, "csv",
                                 target_name_data=target_name_data, overwrite=overwrite)

    if save_data:
        save_txt(of, width, height, model, data, data_format,
                 target_name_data=target_name_data, overwrite=overwrite)

    if save_video:
        # save result as pose_video for parent MgVideo
        self.pose_video = musicalgestures.MgVideo(
            destination_video, color=self.color, returned_by_process=True)
        return self.pose_video
    else:
        # otherwise just return the parent MgVideo
        return self


def download_model(modeltype):
    """
    Helper function to automatically download model (.caffemodel) files.
    """
    import platform
    import subprocess
    import os
    import musicalgestures

    module_path = os.path.abspath(os.path.dirname(musicalgestures.__file__))

    batch, shell, shell_colab = '_remote.bat', '_remote.sh', '_remote_colab.sh'

    the_system = platform.system()

    pb_prefix = ''
    mpi_script = module_path + '/pose/getMPI'
    coco_script = module_path + '/pose/getCOCO'
    body_25_script = module_path + '/pose/getBODY_25'
    wget_win = musicalgestures._utils.wrap_str(
        module_path + '/3rdparty/windows/wget/wget.exe')
    target_folder_mpi = musicalgestures._utils.wrap_str(
        module_path + '/pose/mpi')
    target_folder_coco = musicalgestures._utils.wrap_str(
        module_path + '/pose/coco')
    target_folder_body_25 = musicalgestures._utils.wrap_str(
        module_path + '/pose/body_25')

    if the_system == 'Windows':
        mpi_script += batch
        coco_script += batch
        body_25_script += batch
    elif in_colab():
        mpi_script += shell_colab
        coco_script += shell_colab
        body_25_script += shell_colab
    else:
        mpi_script += shell
        coco_script += shell
        body_25_script += shell

    if modeltype.lower() == 'mpi':
        command = musicalgestures._utils.wrap_str(mpi_script)
        if the_system == 'Windows':
            command += f' {wget_win} {target_folder_mpi}'
        else:
            command = 'sudo -S bash ' + command
            command += f' {target_folder_mpi}'
        pb_prefix = 'Downloading MPI model:'
    elif modeltype.lower() == 'coco':
        command = coco_script
        if the_system == 'Windows':
            command += f' {wget_win} {target_folder_coco}'
        else:
            command = 'sudo -S bash ' + command
            command += f' {target_folder_coco}'
        pb_prefix = 'Downloading COCO model:'
    elif modeltype.lower() == 'body_25':
        command = body_25_script
        if the_system == 'Windows':
            command += f' {wget_win} {target_folder_body_25}'
        else:
            command = 'sudo -S bash ' + command
            command += f' {target_folder_body_25}'
        pb_prefix = 'Downloading BODY_25 model:'

    pb = MgProgressbar(total=100, prefix=pb_prefix)

    if the_system == 'Windows' or in_colab():
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
        i = 0
        while True:
            out = process.stdout.readline()
            if out == '':
                process.wait()
                break
            elif out.find('%') != -1:
                percentage_place = out.find('%')
                percent = out[percentage_place-2:percentage_place]
                pb.progress(float(percent))
            # else:
            #     print(out)

    except KeyboardInterrupt:
        try:
            process.terminate()
        except OSError:
            pass
        process.wait()
        raise KeyboardInterrupt
