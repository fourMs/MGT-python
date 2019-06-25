import cv2
import numpy as np

def constrNum(n, minn, maxn):
    return max(min(maxn, n), minn)

img=cv2.imread('circle.png')

h = img.shape[0]
w = img.shape[1]

m = 50
prev_Start = w
prev_Stop = 0 

img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
the_box = np.zeros([h,w])
#----Finding left and right edges
for i in range(h):
	row=img[i,:]
	inds = np.where(row>0)[0]
	if len(inds)>0:
		Start = inds[0]
		if Start<prev_Start:
			le = Start
			prev_Start = Start
		if len(inds)>1:
			Stop = inds[-1]
			if Stop>prev_Stop:
				re = Stop
				prev_Stop = Stop

# ---- Finding top and bottom edges
prev_Start = h
prev_Stop = 0 
for j in range(w):
	col=img[:,j]
	inds = np.where(col>0)[0]
	if len(inds)>0:
		Start = inds[0]
		if Start<prev_Start:
			te = Start
			prev_Start = Start
		if len(inds)>1:
			Stop = inds[-1]
			if Stop>prev_Stop:
				be = Stop
				prev_Stop = Stop


the_box[constrNum(te-m,0,h-1),constrNum(le-m,0,w-1):constrNum(re+m,0,w-1)]=1
the_box[constrNum(te-m,0,h-1):constrNum(be+m,0,h-1),constrNum(le-m,0,w-1)]=1
the_box[constrNum(be+m,0,h-1),constrNum(le-m,0,w-1):constrNum(re+m,0,w-1)]=1
the_box[constrNum(te-m,0,h-1):constrNum(be+m,0,h-1),constrNum(re+m,0,w-1)]=1




cv2.imshow('',the_box)
cv2.waitKey(0)