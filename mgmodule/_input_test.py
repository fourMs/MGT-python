class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message):
        self.message = message


def input_test(filename,method,filtertype,thresh,starttime,endtime,blur,skip):
    """ Gives feedback to user if initialization from input went wrong. """
    filenametest = 'true'

    for c in filename:
        if c.isalpha() == True or c.isnumeric() == True or c == '.' or c == '_':
            pass
        else: 
            filenametest = 'false'

    if filenametest == 'true':
        if method != 'Diff' and method != 'OpticalFlow':
            msg = 'Please specify a method for motion estimation as str: Diff or OpticalFlow.'
            raise InputError(msg) 

        if filtertype != 'Regular' and filtertype != 'Binary' and filtertype != 'Blob':
            msg = 'Please specify a filter type as str: Regular or Binary'
            raise InputError(msg)

        if blur != 'Average' and blur != 'None':
            msg = 'Please specify a blur type as str: Average or None'
            raise InputError(msg)

        if not isinstance(thresh,float) and not isinstance(thresh, int):
            msg = 'Please specify a threshold as a float between 0 and 1.'
            raise InputError(msg)

        if not isinstance(starttime,float) and not isinstance(starttime,int):
            msg = 'Please specify a starttime as a float.'
            raise InputError(msg)

        if not isinstance(endtime,float) and not isinstance(endtime,int):
            msg = 'Please specify a endtime as a float.'
            raise InputError(msg)

        if not isinstance(skip,int):
            msg = 'Please specify a skip as an integer of frames you wish to skip (Max = N frames).'
            raise InputError(msg)        

    else:
        msg = 'Minimum input for this function: filename as a str.'
        raise InputError(msg)
