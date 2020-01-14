def mg_progressbar(iteration, total, prefix='', suffix='', decimals=1, length=40, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar.

    Parameters:
    -----------
    - iteration   - Required  : current iteration (Int)
    - total       - Required  : total iterations (Int)
    - prefix      - Optional  : prefix string (Str)
    - suffix      - Optional  : suffix string (Str)
    - decimals    - Optional  : positive number of decimals in percent complete (Int)
    - length      - Optional  : character length of bar (Int)
    - fill        - Optional  : bar fill character (Str)
    - printEnd    - Optional  : end character (e.g. "\\r", "\\r\\n") (Str)
    """
    import sys

    percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                     (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    sys.stdout.flush()
    sys.stdout.write('\r%s |%s| %s%% %s' %
                     (prefix, bar, percent, suffix))
    # Print New Line on Complete
    if iteration == total:
        print()


def scale_num(val, in_low, in_high, out_low, out_high):
    """Scale a number linearly."""
    return ((val - in_low) * (out_high - out_low)) / (in_high - in_low) + out_low


def scale_array(array, new_min, new_max):
    """Scale an array linearly."""
    minimum, maximum = np.min(array), np.max(array)
    m = (new_max - new_min) / (maximum - minimum)
    b = new_min - m * minimum
    return m * array + b


class MgImage():
    def __init__(self, filename):
        self.filename = filename
        import os
        self.of = os.path.splitext(self.filename)[0]
        self.fex = os.path.splitext(self.filename)[1]
    from ._show import mg_show as show


def convert_to_avi(filename):
    """Convert any video to one with .avi extension using ffmpeg"""
    import os
    of = os.path.splitext(filename)[0]
    fex = os.path.splitext(filename)[1]
    cmds = ' '.join(['ffmpeg', '-i', filename, of + '.avi'])
    os.system(cmds)
