class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """
    Exception raised for errors in the input.

    Args:
        Error (str): Explanation of the error.
    """

    def __init__(self, message):
        self.message = message


def mg_input_test(filename, array, fps, filtertype, thresh, starttime, endtime, blur, skip, frames):
    """
    Gives feedback to user if initialization from input went wrong.

    Args:
        filename (str): Path to the input video file.
        array (np.ndarray, optional): Generates an MgVideo object from a video array. Defauts to None.
        fps (float, optional): The frequency at which consecutive images from the video array are captured or displayed. Defauts to None.
        filtertype (str): 'Regular' turns all values below `thresh` to 0. 'Binary' turns all values below `thresh` to 0, above `thresh` to 1. 'Blob' removes individual pixels with erosion method.
        thresh (float): A number in the range of 0 to 1. Eliminates pixel values less than given threshold.
        starttime (int/float): Trims the video from this start time (s).
        endtime (int/float): Trims the video until this end time (s).
        blur (str): 'Average' to apply a 10px * 10px blurring filter, 'None' otherwise.
        skip (int): Every n frames to discard. `skip=0` keeps all frames, `skip=1` skips every other frame.
        frames (int): Specify a fixed target number of frames to extract from the video. 

    Raises:
        InputError: If the types or options are wrong in the input.
    """

    filenametest = type(filename) == str

    if filenametest:
        if array is not None:
            if fps is None:
                msg = 'Please specify frame per second (fps) parameter for generating video from array.'
                raise InputError(msg)

        if filtertype.lower() not in ['regular', 'binary', 'blob']:
            msg = 'Please specify a filter type as str: "Regular", "Binary" or "Blob"'
            raise InputError(msg)

        if blur.lower() not in ['average', 'none']:
            msg = 'Please specify a blur type as str: "Average" or "None"'
            raise InputError(msg)

        if not isinstance(thresh, (float, int)):
            msg = 'Please specify a threshold as a float between 0 and 1.'
            raise InputError(msg)

        if not isinstance(starttime, (float, int)):
            msg = 'Please specify a starttime as a float.'
            raise InputError(msg)

        if not isinstance(endtime, (float, int)):
            msg = 'Please specify a endtime as a float.'
            raise InputError(msg)

        if not isinstance(skip, int):
            msg = 'Please specify a skip as an integer of frames you wish to skip (Max = N frames).'
            raise InputError(msg)
        
        if not isinstance(frames, int):
            msg = 'Please specify a frames as an integer of fixed frames you wish to keep.'
            raise InputError(msg)

    else:
        msg = 'Minimum input for this function: filename as a str.'
        raise InputError(msg)
