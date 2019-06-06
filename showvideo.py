def showvideo(baseDir=None,fname=None):
    """Function to display any video in Ipython or Jupyter Notebook given a directory in which the video exist and the video file name.
    Args:
        baseDir: Directory containing the video
        fname: Filename of video.
    """
    from IPython.display import HTML
    import os
    """
    location = baseDir + fname
    if os.path.isfile(location):
        ext = '.mp4'
    else:
        print("Error: Please check the path.")
    """
    video_encoded = open(fname, "rb").read().encode("base64")
    video_tag = '<video width="320" height="240" controls alt="test" src="data:video/{0};base64,{1}">'.format(ext, video_encoded)
    return HTML(data=video_tag)
