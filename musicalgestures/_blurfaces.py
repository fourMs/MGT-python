import os
import cv2
import numpy as np
import skimage.draw
import pandas as pd
import subprocess

from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib as mpl

import musicalgestures
from musicalgestures._centerface import CenterFace
from musicalgestures._utils import MgProgressbar, MgImage, embed_audio_in_video, extract_wav, transform_frame, generate_outfilename, frame2ms

def scaling_mask(x1, y1, x2, y2, mask_scale=1.0):
    """
    Scale factor for face masks, to make sure that the masks cover the complete face.

    Args:
        x1 (int): X start coordinate value
        y1 (int): Y start coordinate value
        x2 (int): X end coordinate value
        y2 (int): Y end coordinate value
        mask_scale (float, optional): Scale factor for adjusting the size of the face masks. Defaults to 1.0.

    Returns:
        [x1, y1, x2, y2]: A list of intergers corresponding to the scaled coordinates of the face masks.
    """
    scale = mask_scale - 1.0
    h, w = y2 - y1, x2 - x1
    y1 -= h * scale
    y2 += h * scale
    x1 -= w * scale
    x2 += w * scale
    return np.round([x1, y1, x2, y2]).astype(int)

def centroid_mask(data):
    centroid = np.zeros((data.shape[0], 2))
    for i, coordinates in enumerate(data):
        # Compute the centroid of the mask using the mask's coordinates (x1,y1,x2,y2)
        centroid[i][0] = (coordinates[1] + coordinates[3]) / 2 
        centroid[i][1] = (coordinates[2] + coordinates[4]) / 2

    center_x = centroid[:,0] 
    center_y = centroid[:,1]        
    return center_x, center_y
    
def heatmap_data(data, resolution, data_min, data_max):
    diff = data_max - data_min
    heatmap_data = (data - data_min) / diff * resolution
    return heatmap_data

def nearest_neighbours(x, y, width, height, resolution, n_neighbours):
    image = np.zeros([resolution, resolution])

    extent = [0, width, 0, height]
    heatmap_x = heatmap_data(x, resolution, extent[0], extent[1])
    heatmap_y = heatmap_data(y, resolution, extent[2], extent[3]) 
    
    for x in range(resolution):
        for y in range(resolution):
            xp = (heatmap_x - x)
            yp = (heatmap_y - y)
            d = np.sqrt(xp**2 + yp**2)
            image[y][x] = 1 / np.sum(d[np.argpartition(d.ravel(), n_neighbours)[:n_neighbours]])
    return image, extent

def mg_blurfaces(self, mask='blur', mask_image=None, mask_scale=1.0, ellipse=True, draw_heatmap=False, neighbours=32, resolution=250, draw_scores=False, save_data=True, data_format='csv', color=(0, 0, 0), target_name=None, overwrite=False):
    """
    Automatic anonymization of faces in videos. 
    This function works by first detecting all human faces in each video frame and then applying an anonymization filter 
    (blurring, black rectangles or images) on each detected face region.

    Credits: `centerface.onnx` (original) and `centerface.py` are based on https://github.com/Star-Clouds/centerface (revision 8c39a49), released under [MIT license](https://github.com/Star-Clouds/CenterFace/blob/36afed/LICENSE).

    Args:
        mask (str, optional): Mask filter mode for face regions. 'blur' applies a strong gaussian blurring, 'rectangle' draws a solid black box, 'image' replaces the face with a custom image and 'none' does leaves the input unchanged. Defaults to 'blur'.
        mask_image (str, optional): Anonymization image path which can be used for masking face regions. This can be activated by specifying 'image' in the mask parameter. Defaults to None.
        mask_scale (float, optional): Scale factor for face masks, to make sure that the masks cover the complete face. Defaults to 1.0.
        ellipse (bool, optional): Mask faces with blurred ellipses. Defaults to True.
        draw_heatmap (bool, optional): Draw heatmap of the detected faces using the centroid of the face mask. Defaults to False.
        neighbours (int, optional): Number of neighbours for smoothing the heatmap image. Defaults to 32.
        resolution (int, optional): Number of pixel resolution for the heatmap visualization. Defaults to 250.
        draw_scores (bool, optional): Draw detection faceness scores onto outputs (a score between 0 and 1 that roughly corresponds to the detector's confidence that something is a face). Defaults to False.
        save_data (bool, optional): Whether to save the scaled coordinates of the face mask (time (ms), x1, y1, x2, y2) for each frame to a file. Defaults to True.
        data_format (str, optional): Specifies format of blur_faces-data. Accepted values are 'csv', 'tsv' and 'txt'. For multiple output formats, use list, e.g. ['csv', 'txt']. Defaults to 'csv'.
        color (tuple, optional): Customized color of the rectangle boxes. Defaults to black (0, 0, 0).
        target_name (str, optional): Target output name. Defaults to None (which assumes that the input filename with the suffix "_blurred" should be used).
        overwrite (bool, optional): Whether to allow overwriting existing files or to automatically increment target filenames to avoid overwriting. Defaults to False.

    Returns:
        MgVideo: A MgVideo as blur_faces for parent MgVideo
    """

    of, fex = os.path.splitext(self.filename)
    # Define ffmpeg command start and end
    cmd = ['ffmpeg', '-y', '-i', self.filename, '-f', 'image2pipe', '-pix_fmt', 'rgb24', '-vcodec', 'rawvideo', '-']
    
    if target_name == None:
        target_name = of + '_blurred.avi'
    else:
        # Enforce .avi
        target_name = os.path.splitext(target_name)[0] + '.avi'
    if not overwrite:
        target_name = generate_outfilename(target_name)
    if os.path.isfile(target_name):
        os.remove(target_name)       

    pb = MgProgressbar(total=self.length, prefix='Blurring faces:')
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=-1)

    # Create an instance of the CenterFace class
    centerface = CenterFace()
    output_stream = cv2.VideoWriter(target_name, cv2.VideoWriter_fourcc('M','J','P','G'), self.fps, (self.width, self.height))

    # Create an empty list to append the mask coordinates
    data = []

    i = 0

    while True:
        # Read frame-by-frame
        if self.color:
            out = process.stdout.read(self.width*self.height*3)
        else:
            out = process.stdout.read(self.width*self.height)
        if out == b'':
            pb.progress(self.length)
            break

        # Transform the bytes read into a numpy array and convert to RGB
        frame = transform_frame(out, self.height, self.width, self.color)
        frame = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2RGB) # copy frame for writing it
        
        h, w = frame.shape[:2]
        dets, lms = centerface(frame, h, w, threshold=0.2)

        for x, det in enumerate(dets):
            boxes, score = det[:4], det[4]
            x1, y1, x2, y2 = boxes.astype(int)
            x1, y1, x2, y2 = scaling_mask(x1, y1, x2, y2, mask_scale)
            # Clip bounding boxes coordinates to valid frame region
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
                    # Get y and x coordinate lists of the bounding ellipse
                    ey, ex = skimage.draw.ellipse((y2 - y1) // 2, (x2 - x1) // 2, (y2 - y1) // 2, (x2 - x1) // 2)
                    roibox[ey, ex] = blurred_box[ey, ex]
                    frame[y1:y2, x1:x2] = roibox
                else:
                    frame[y1:y2, x1:x2] = blurred_box

            # Mask faces with an image
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
            
            # Draw heatmap of the detected faces using the centroid of the face mask.
            if draw_heatmap or save_data:
                time = frame2ms(i, self.fps)
                data.append([time, x1, y1, x2, y2])

            # Draw the faceness score (between 0 and 1) that roughly corresponds to the detector's confidence that something is a face.
            if draw_scores:
                cv2.putText(frame, f'{score:.2f}', (x1 + 0, y1 - 20), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 255, 0))

        output_stream.write(frame)
    
        # Flush the buffer
        process.stdout.flush()
        pb.progress(i)
        i += 1

    # Terminate the process
    process.terminate()
    output_stream.release()

    if self.has_audio:
        # Embed audio in the video file
        source_audio = extract_wav(of + fex)
        embed_audio_in_video(source_audio, target_name)
        os.remove(source_audio)

    # Save warped video as blur_faces for parent MgVideo
    # we have to do this here since we are not using mg_blurfaces (that would normally save the result itself)
    self.blur_faces = musicalgestures.MgVideo(target_name, color=self.color, returned_by_process=True)

    def save_txt(of, data, data_format, target_name=target_name, overwrite=overwrite):
        """
        Helper function to export pose estimation data as textfile(s).
        """
        def save_single_file(of, data, data_format, target_name=target_name, overwrite=overwrite):
            """
            Helper function to export pose estimation data as a textfile using pandas.
            """

            headers = ['time (ms)', 'x1', 'y1', 'x2', 'y2']
            data_format = data_format.lower()

            df = pd.DataFrame(data=data, columns=headers)

            if data_format == "tsv":
                if target_name == None:
                    target_name = of + '.tsv'
                else:
                    # take name, but enforce tsv
                    target_name = os.path.splitext(target_name)[0] + '.tsv'
                if not overwrite:
                    target_name = generate_outfilename(target_name)

                with open(target_name, 'wb') as f:
                    head_str = ''
                    for head in headers:
                        head_str += head + '\t'
                    head_str += '\n'
                    f.write(head_str.encode())
                    fmt_list = ['%.0f' for item in range(len(headers))]
                    np.savetxt(f, df.values, delimiter='\t', fmt=fmt_list)

            elif data_format == "csv":
                if target_name == None:
                    target_name = of + '.csv'
                else:
                    # take name, but enforce csv
                    target_name = os.path.splitext(target_name)[0] + '.csv'
                if not overwrite:
                    target_name = generate_outfilename(target_name)
                df.to_csv(target_name, index=None)

            elif data_format == "txt":
                if target_name == None:
                    target_name = of + '.txt'
                else:
                    # take name, but enforce txt
                    target_name = os.path.splitext(target_name)[0] + '.txt'
                if not overwrite:
                    target_name = generate_outfilename(target_name)

                with open(target_name, 'wb') as f:
                    head_str = ''
                    for head in headers:
                        head_str += head + ' '
                    head_str += '\n'
                    f.write(head_str.encode())
                    fmt_list = ['%.0f' for item in range(len(headers))]
                    np.savetxt(f, df.values, delimiter=' ', fmt=fmt_list)

            elif data_format not in ["tsv", "csv", "txt"]:
                print(f"Invalid data format: '{data_format}'.\nFalling back to '.csv'.")
                save_single_file(of, data, "csv", target_name=target_name, overwrite=overwrite)

        if type(data_format) == str:
            save_single_file(of, data, data_format, target_name=target_name, overwrite=overwrite)

        elif type(data_format) == list:
            if all([item.lower() in ["csv", "tsv", "txt"] for item in data_format]):
                data_format = list(set(data_format))
                [save_single_file(of, data, item, target_name=target_name, overwrite=overwrite)
                 for item in data_format]
            else:
                print(f"Unsupported formats in {data_format}.\nFalling back to '.csv'.")
                save_single_file(of, data, "csv", target_name=target_name, overwrite=overwrite)

    if save_data:  
        save_txt(of, data, data_format, target_name=target_name, overwrite=overwrite)  
        return self.blur_faces

    if draw_heatmap:
        target_name = os.path.splitext(target_name)[0] + '.png'
        if not overwrite:
            target_name = generate_outfilename(target_name)

        # Approximately update font and plot size with frame size
        plt.rcParams.update({'font.size': int((self.height/self.fps))})  
        fig, ax = plt.subplots(figsize=(int(self.width/self.fps), int(self.height/self.fps))) 
        # make sure background is white
        fig.patch.set_facecolor('white')
        fig.patch.set_alpha(1)  

        center_x, center_y = centroid_mask(np.asarray(data))
        im, extent = nearest_neighbours(center_x, center_y, self.width, self.height, resolution, neighbours)

        ax.imshow(im, extent=extent, cmap=cm.jet)
        ax.set_title(f"Heatmap of face detection (neighbours={neighbours})")
        ax.set_xlabel("Video width (pixels)")
        ax.set_ylabel("Video height (pixels)")
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])

        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad="3%")
        normalizer = mpl.colors.Normalize(vmin=0, vmax=1)
        fig.colorbar(mpl.cm.ScalarMappable(norm=normalizer, cmap=cm.jet), cax=cax)

        plt.tight_layout()
        plt.savefig(target_name, format='png', transparent=False)
        plt.close()

        return MgImage(target_name)

    else:
        return self.blur_faces
    
