import musicalgestures

# CREATE MODULE OBJECT: Here is an example call to create an MgVideo, using loads of parameters
mg = musicalgestures.MgVideo("./musicalgestures/examples/dancer.avi", starttime=2,
                             endtime=20, contrast=100, brightness=50)

# USE MODULE METHOD: To run the motionvideo analysis, run the function using your video object
mg.motion(inverted_motionvideo=False, inverted_motiongram=False,
          thresh=0.05, unit='seconds')

# History video
mg.history(history_length=25)
# Motion history video
mg.history(filename=mg.of + '_motion.avi', history_length=25)

# Average image of original video
# mg.blend(filename="./musicalgestures/examples/dancer.avi", component_mode='average')

# Average image of pre-processed video
mg.blend(component_mode='average')

# Average image of motion video
mg.blend(filename=mg.of + '_motion.avi', component_mode='average')
