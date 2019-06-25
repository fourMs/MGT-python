import cv2
import numpy as np
 
# Create a VideoCapture object and read from input file
# If the input is the camera, pass 0 instead of the video file name
def show(self, input):
  cap = cv2.VideoCapture(input)
  # Check if camera opened successfully
  if (cap.isOpened()== False): 
    print("Error opening video stream or file")
  i = int(np.round((1/self.fps)*1000))
  print(i)
   
  # Read until video is completed
  while(cap.isOpened()):
    # Capture frame-by-frame
    ret, frame = cap.read()
    if ret == True:
   
      # Display the resulting frame
      cv2.imshow('Frame',frame)
   
      # Press Q on keyboard to  exit
      if cv2.waitKey(int(i)) & 0xFF == ord('q'):
        break
      
    # Break the loop
    else: 
      break
   
  # When everything done, release the video capture object
  cap.release()
   
  # Closes all the frames
  cv2.destroyAllWindows()
