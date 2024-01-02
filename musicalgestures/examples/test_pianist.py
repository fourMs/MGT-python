import musicalgestures

# CREATE MODULE OBJECT: Here is an example call to create an MgVideo, using loads of parameters
mg = musicalgestures.MgVideo("../pianist.avi", color=False, crop='auto', skip=3)
# USE MODULE METHOD: To run the motionvideo analysis, run the function using your video object,
# then create the motion history by chaining the history() function onto the result of the previous (motion) function
mg.motion(inverted_motionvideo=True, inverted_motiongram=True,
          thresh=0.1, blur='Average').history(history_length=25)

# Average image of original video
# mg.blend(filename="../pianist.avi", component_mode='average')

# Average image of pre-processed video
mg.blend(component_mode='average')

# Average image of motion video
mg.blend(filename=mg.of + '_motion.avi', component_mode='average')
