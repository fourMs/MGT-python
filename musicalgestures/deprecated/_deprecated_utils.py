

def mg_progressbar(
        iteration,
        total,
        prefix='',
        suffix='',
        decimals=1,
        length=40,
        fill='█',
        printEnd="\r"):
    """
    Calls in a loop to create terminal progress bar.

    Parameters
    ----------
    - iteration : int

        Current iteration.
    - total : int

        Total iterations.
    - prefix : str, optional

        Prefix string.
    - suffix : str, optional

        Suffix string.
    - decimals : int, optional

        Default is 1. Positive number of decimals in percent complete.
    - length : int, optional

        Default is 40. Character length of bar.
    - fill : str, optional

        Default is '█'. Bar fill character.
    - printEnd : str, optional.

        Default is '\\r'. End of line character.
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
