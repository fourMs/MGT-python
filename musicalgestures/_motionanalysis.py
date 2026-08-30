import cv2
import numpy as np


def motiongram_data(frames, orientation="y", frame_diff=True, normalize=True):
    """
    Compute a motiongram as a plain numpy array from a stack of grayscale
    frames, with a selectable orientation.

    The orientation names the position axis the gram keeps, as everywhere in
    the toolbox. With `orientation="y"` each (motion) frame is collapsed to
    its per-row mean (the mean across image columns), and the resulting
    column vectors are stacked over time into an (height, n) array -- image
    row vs time. This y-gram renders vertical trajectories (e.g. a mallet's
    approach-and-rebound path toward an instrument) directly. With
    `orientation="x"` each frame is collapsed to its per-column mean, giving
    a (width, n) array -- image column vs time -- which renders sideways
    travel. The old values "vertical" and "horizontal" (which named the
    motion shown, y and x respectively) are deprecated and will be removed
    in 2.0.

    This is the numpy-level counterpart of the image-producing motiongram
    pipelines (`MgVideo.motiongrams`): use this function when you want the
    motiongram as data for further analysis rather than as a rendered image.

    Source: cymbal-comparison study (Jensenius) -- the y-motiongram of
    the mallet trajectory; building on the classic fourMs motiongram.

    Args:
        frames (np.ndarray): Grayscale frames of shape (T, H, W).
        orientation (str, optional): "y" (per-row mean; image row vs time;
            shows vertical motion) or "x" (per-column mean; image column vs
            time; shows sideways travel). "vertical" and "horizontal" are
            deprecated aliases for "y" and "x", removed in 2.0. Defaults
            to "y".
        frame_diff (bool, optional): If True, collapse the absolute inter-frame
            differences (a motiongram, T-1 time steps); if False, collapse the
            frames themselves (a videogram, T time steps). Defaults to True.
        normalize (bool, optional): If True, scale the result to [0, 1] by its
            maximum. Defaults to True.

    Returns:
        np.ndarray: The motiongram, of shape (H, T-1) for "y" or (W, T-1)
            for "x" (T instead of T-1 when `frame_diff` is False). Time runs
            along the second axis.
    """
    if orientation in ("vertical", "horizontal"):
        import warnings
        new = {"vertical": "y", "horizontal": "x"}[orientation]
        warnings.warn(f"orientation={orientation!r} is deprecated and will be "
                      f"removed in 2.0; use orientation={new!r}.",
                      DeprecationWarning, stacklevel=2)
        orientation = new

    frames = np.asarray(frames, dtype=np.float32)
    if frames.ndim != 3:
        raise ValueError("motiongram_data expects frames of shape (T, H, W)")
    data = np.abs(np.diff(frames, axis=0)) if frame_diff else frames
    if orientation == "y":
        gram = data.mean(axis=2).T      # (H, T-1): image row vs time
    elif orientation == "x":
        gram = data.mean(axis=1).T      # (W, T-1): image column vs time
    else:
        raise ValueError("orientation must be 'x' or 'y'")
    if normalize:
        gram = gram / (gram.max() + 1e-12)
    return gram


def centroid(image, width, height):
    """
    Computes the centroid and quantity of motion in an image or frame.

    Args:
        image (np.array(uint8)): The input image matrix for the centroid estimation function.
        width (int): The pixel width of the input video capture.
        height (int): The pixel height of the input video capture.

    Returns:
        np.array(2): X and Y coordinates of the centroid of motion.
        int: Quantity of motion: How large the change was in pixels.
    """

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    x = np.arange(width)
    y = np.arange(height)
    # Calculates the sum of the pixels in the input image
    qom = cv2.sumElems(image)[0]
    mx = np.mean(image, axis=0)
    my = np.mean(image, axis=1)

    if np.sum(mx) != 0 and np.sum(my) != 0:
        comx = np.dot(x, mx) / np.sum(mx)
        comy = np.dot(y, my) / np.sum(my)
    else:
        comx = 0
        comy = 0

    com = np.zeros(2)
    com[0] = comx
    # The y-axis is flipped to fit a "normal" coordinate system
    com[1] = height-comy

    return com, int(qom)

def area(motion_frame, height, width):
    # Area of Motion (AoM)
    aombite = []
    # Convert to gray scale
    gray = cv2.cvtColor(motion_frame, cv2.COLOR_BGR2GRAY)
    # Apply adaptative threshold on the video frame to make differences more visible for contour detection
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 51, 2)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  
    # Get the largest contour to average the area of motion
    if len(contours) != 0:
        largest = contours[0]
        for contour in contours:
            if cv2.contourArea(contour) > cv2.contourArea(largest):
                largest = contour  
        (x, y, w, h) = cv2.boundingRect(largest) 
        # Append and normalize coordinates of the area of motion
        aombite.append([x/width, y/height, (x+w)/width,(y+h)/height])
    else:
        aombite.append([0,0,0,0])

    return aombite