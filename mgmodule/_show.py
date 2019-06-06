import cv2
import numpy as np
 
# Create a VideoCapture object and read from input file
# If the input is the camera, pass 0 instead of the video file name
def show(self, input):
  cap = cv2.VideoCapture(input)
  # Check if camera opened successfully
  if (cap.isOpened()== False): 
    print("Error opening video stream or file")
   
  # Read until video is completed
  while(cap.isOpened()):
    # Capture frame-by-frame
    ret, frame = cap.read()
    if ret == True:
   
      # Display the resulting frame
      cv2.imshow('Frame',frame)
   
      # Press Q on keyboard to  exit
      if self.skip != 0:
        if cv2.waitKey(25*self.skip) & 0xFF == ord('q'):
            break
      else:
        if cv2.waitKey(25) & 0xFF == ord('q'):
          break
      
    # Break the loop
    else: 
      break
   
  # When everything done, release the video capture object
  cap.release()
   
  # Closes all the frames
  cv2.destroyAllWindows()
