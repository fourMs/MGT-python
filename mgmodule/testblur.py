import cv2
from matplotlib import pyplot as plt
import numpy as np
img = cv2.imread('orange.jpg')
blur = cv2.blur(img,(20,20)) #how much you wanna blur
#plt.imshow(frame)
plt.subplot(121),plt.imshow(img),plt.title('Original')
plt.xticks([]), plt.yticks([])
plt.subplot(122),plt.imshow(blur),plt.title('Blurred')
plt.xticks([]), plt.yticks([])
plt.show()

#this plots a blue orange......