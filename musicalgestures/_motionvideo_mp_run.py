from musicalgestures._utils import ffmpeg_cmd, generate_outfilename, get_length, wrap_str, convert_to_avi, MgProgressbar, extract_wav, embed_audio_in_video, MgImage
from musicalgestures._motionvideo import save_txt, plot_motion_metrics
import subprocess
import tempfile
import shutil
import platform
import musicalgestures
import os
import numpy as np
import socket
import threading
import multiprocessing
import cv2

def mg_motion_mp(
        self,
        filtertype='Regular',
        thresh=0.05,
        blur='None',
        kernel_size=5,
        inverted_motionvideo=False,
        inverted_motiongram=False,
        unit='seconds',
        equalize_motiongram=True,
        save_plot=True,
        plot_title=None,
        save_data=True,
        data_format="csv",
        save_motiongrams=True,
        save_video=True,
        target_name_video=None,
        target_name_plot=None,
        target_name_data=None,
        target_name_mgx=None,
        target_name_mgy=None,
        overwrite=False,
        num_processes=-1):

    of, fex = self.of, self.fex

    # Convert to avi if the input is not avi - necesarry for cv2 compatibility on all platforms
    if fex != '.avi':
        # first check if there already is a converted version, if not create one and register it to the parent self
        if "as_avi" not in self.__dict__.keys():
            file_as_avi = convert_to_avi(of + fex, overwrite=overwrite)
            # register it as the avi version for the file
            self.as_avi = musicalgestures.MgObject(file_as_avi)
        # point of and fex to the avi version
        of, fex = self.as_avi.of, self.as_avi.fex

    module_path = os.path.abspath(os.path.dirname(musicalgestures.__file__)).replace('\\', '/')
    the_system = platform.system()
    pythonkw = "python"
    if the_system != "Windows":
        pythonkw += "3"
    pyfile = wrap_str(module_path + '/_motionvideo_mp_render.py')

    temp_folder = tempfile.mkdtemp().replace('\\', '/')
    if temp_folder[-1] != "/":
        temp_folder += '/'
    # print("Temp folder:", temp_folder)

    of_feed = of.replace('\\', '/')
    of_feed = os.path.basename(of_feed)

    save_data_feed = save_data or save_plot

    command = [pythonkw, pyfile, temp_folder, of_feed, fex, self.fps, self.width, self.height, self.length, self.color, filtertype, thresh, blur, kernel_size, inverted_motionvideo, inverted_motiongram, equalize_motiongram, save_data_feed, save_motiongrams, save_video, num_processes]
    command = [str(item) for item in command]
    # print()
    # print(command)
    # print()

    pgbar_text = 'Rendering motion' + ", ".join(np.array(["-video", "-grams", "-plots", "-data"])[
            np.array([save_video, save_motiongrams, save_plot, save_data])]) + ":"
    pb = MgProgressbar(total=self.length, prefix=pgbar_text)
    progress = 0

    # set up socket server thread
    HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
    PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

    process = subprocess.Popen(command)

    num_cores = multiprocessing.cpu_count()
    # print("starting thread")
    t = threading.Thread(target=run_socket_server(HOST, PORT, pb, num_cores))
    t.start()

    try:
        # print("will wait")
        process.wait()

    except KeyboardInterrupt:
        try:
            process.terminate()
        except OSError:
            pass
        process.wait()
        # print("will join")
        t.join()
        # print("joined")
        raise KeyboardInterrupt

    # print("will join")
    t.join()
    # print("joined")

    # print("organizing results...")
    results = os.listdir(temp_folder)
    time_files  = [temp_folder + file for file in results if file.startswith("time")]
    time_files.sort()
    com_files   = [temp_folder + file for file in results if file.startswith("com")]
    com_files.sort()
    qom_files   = [temp_folder + file for file in results if file.startswith("qom")]
    qom_files.sort()
    gramx_files = [temp_folder + file for file in results if file.startswith("gramx")]
    gramx_files.sort()
    gramy_files = [temp_folder + file for file in results if file.startswith("gramy")]
    gramy_files.sort()
    video_files = [temp_folder + file for file in results if file.endswith("avi")]
    video_files.sort()

    gramx, gramy, time, com, qom = None, None, None, None, None

    if save_motiongrams:
        # load gramx
        # if we only used a single chunk, load everything
        if len(gramx_files) == 1:
            gramx = np.load(gramx_files[0])
        # or in case there were multiple chunks...
        else:
            for idx, item in enumerate(gramx_files):
                if idx == 0:
                    # do not drop first row in first chunk
                    gramx = np.load(item)[:-1]
                elif idx == len(gramy_files) - 1:
                    # do not drop the last row in last chunk
                    gramx = np.append(gramx, np.load(item)[1:], axis=0)
                else:
                    # else drop first and last rows from chunk
                    gramx = np.append(gramx, np.load(item)[1:-1], axis=0)

        # load gramy
        # if we only used a single chunk, load everything
        if len(gramy_files) == 1:
            gramy = np.load(gramy_files[0])
        # or in case there were multiple chunks...
        else:
            for idx, item in enumerate(gramy_files):
                if idx == 0:
                    # do not drop first column in first chunk
                    gramy = np.load(item)[:, :-1]
                elif idx == len(gramy_files) - 1:
                    # do not drop the last column in last chunk
                    gramy = np.append(gramy, np.load(item)[:, 1:], axis=1)
                else:
                    # else drop first and last columns from chunk
                    gramy = np.append(gramy, np.load(item)[:, 1:-1], axis=1)

        if self.color == False:
            # Normalize before converting to uint8 to keep precision
            gramx = gramx/gramx.max()*255
            gramy = gramy/gramy.max()*255
            gramx = cv2.cvtColor(gramx.astype(
                np.uint8), cv2.COLOR_GRAY2BGR)
            gramy = cv2.cvtColor(gramy.astype(
                np.uint8), cv2.COLOR_GRAY2BGR)

        gramx = (gramx-gramx.min())/(gramx.max()-gramx.min())*255.0
        gramy = (gramy-gramy.min())/(gramy.max()-gramy.min())*255.0

        if equalize_motiongram:
            gramx = gramx.astype(np.uint8)
            gramx_hsv = cv2.cvtColor(gramx, cv2.COLOR_BGR2HSV)
            gramx_hsv[:, :, 2] = cv2.equalizeHist(gramx_hsv[:, :, 2])
            gramx = cv2.cvtColor(gramx_hsv, cv2.COLOR_HSV2BGR)

            gramy = gramy.astype(np.uint8)
            gramy_hsv = cv2.cvtColor(gramy, cv2.COLOR_BGR2HSV)
            gramy_hsv[:, :, 2] = cv2.equalizeHist(gramy_hsv[:, :, 2])
            gramy = cv2.cvtColor(gramy_hsv, cv2.COLOR_HSV2BGR)

        if target_name_mgx == None:
            target_name_mgx = of+'_mgx.png'
        if target_name_mgy == None:
            target_name_mgy = of+'_mgy.png'
        if not overwrite:
            target_name_mgx = generate_outfilename(target_name_mgx)
            target_name_mgy = generate_outfilename(target_name_mgy)

        if inverted_motiongram:
            cv2.imwrite(target_name_mgx, cv2.bitwise_not(gramx.astype(np.uint8)))
            cv2.imwrite(target_name_mgy, cv2.bitwise_not(gramy.astype(np.uint8)))
        else:
            cv2.imwrite(target_name_mgx, gramx.astype(np.uint8))
            cv2.imwrite(target_name_mgy, gramy.astype(np.uint8))

        # save rendered motiongrams as MgImages into parent MgObject
        self.motiongram_x = MgImage(target_name_mgx)
        self.motiongram_y = MgImage(target_name_mgy)

    if save_data:
        # load time
        for idx, item in enumerate(time_files):
            if idx == 0:
                time = np.load(item)
            else:
                last_time = time[-1]
                time = np.append(time, np.load(item)[1:] + last_time)

        # load qom
        for idx, item in enumerate(qom_files):
            if idx == 0:
                qom = np.load(item)
            else:
                qom = np.append(qom, np.load(item)[1:])

        # load com
        for idx, item in enumerate(com_files):
            if idx == 0:
                com = np.load(item)
            else:
                com = np.append(com, np.load(item)[1:], axis=0)

        save_txt(of, time, com, qom, self.width, self.height, data_format, target_name_data=target_name_data, overwrite=overwrite)

    if save_plot:
        if not save_data:
            # load qom
            for idx, item in enumerate(qom_files):
                if idx == 0:
                    qom = np.load(item)
                else:
                    qom = np.append(qom, np.load(item)[1:])

            # load com
            for idx, item in enumerate(com_files):
                if idx == 0:
                    com = np.load(item)
                else:
                    com = np.append(com, np.load(item)[1:], axis=0)

        if plot_title == None:
            plot_title = os.path.basename(of + fex)
        # save plot as an MgImage at motion_plot for parent MgObject
        self.motion_plot = MgImage(plot_motion_metrics(of, self.fps, com, qom, self.width, self.height, unit, plot_title, target_name_plot=target_name_plot, overwrite=overwrite))

    if save_video:
        if target_name_video == None:
            target_name_video = of + '_motion' + fex
        # enforce avi
        else:
            target_name_video = os.path.splitext(target_name_video)[0] + fex
        if not overwrite:
            target_name_video = generate_outfilename(target_name_video)

        # print("stitching video...")
        concatenated = concat_videos(video_files, pb_prefix='Cleanup')
        # print("moving...")
        os.replace(concatenated, target_name_video)
        # print("checking audio...")
        destination_video = target_name_video
        if self.has_audio:
            source_audio = extract_wav(of + fex)
            embed_audio_in_video(source_audio, destination_video)
            os.remove(source_audio)
        # save rendered motion video as the motion_video of the parent MgObject
        self.motion_video = musicalgestures.MgObject(destination_video, color=self.color, returned_by_process=True)

    # print("Cleanup...")
    shutil.rmtree(temp_folder)
    # print("Removed temp folder.")

    if save_video:
        return self.motion_video
    else:
        return self


def run_socket_server(host, port, pb, numprocesses):
    # print("will start server")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        conn, addr = s.accept()
        with conn:
            # print('Connected by', addr)
            tracker = TrackMultiProgress(numprocesses)
            while True:
                data = conn.recv(1024)
                # print(data.decode())
                data_str = data.decode()
                if data_str.startswith("progress:"):
                    progress_message = data_str[len("progress:"):]
                    progress_message_list = progress_message.split('progress:')
                    progress = None
                    for progress_bit in progress_message_list:
                        node, iteration = progress_bit.split(' ')
                        node, iteration = int(node), int(iteration)
                        progress = tracker.progress(node, iteration)
                    pb.progress(progress)
                else:
                    print()
                    print("got something else...")
                    print(data_str)
                    # pass

                if not data:
                    print("shutting down server")
                    break


class TrackMultiProgress():
    def __init__(self, numprocesses):
        self.numprocesses = numprocesses
        self.processmap = np.zeros(self.numprocesses)

    def progress(self, node, iteration):
        self.processmap[node] = iteration
        return np.sum(self.processmap)

    def reset(self):
        self.processmap = np.zeros(self.numprocesses)


def concat_videos(list_of_videos, target_name=None, overwrite=False, pb_prefix='Concatenating videos:', stream=True):
    import os
    of, fex = os.path.splitext(list_of_videos[0])
    if not target_name:
        target_name = of + '_concat' + fex
    if not overwrite:
        target_name = generate_outfilename(target_name)
    cmds = ['ffmpeg', '-y']

    for video in list_of_videos:
        cmds.append('-i')
        cmds.append(video)

    cmd_filter = ["-filter_complex", f'concat=n={len(list_of_videos)}:v=1:a=0']
    for cmdlet in cmd_filter:
        cmds.append(cmdlet)

    cmd_end = ["-c:v", "mjpeg", "-q:v", "3", target_name]
    for cmdlet in cmd_end:
        cmds.append(cmdlet)

    ffmpeg_cmd(cmds, get_length(list_of_videos[0]) * len(list_of_videos), pb_prefix=pb_prefix, stream=stream)

    return target_name

