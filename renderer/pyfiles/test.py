import numpy as np 
import cv2 

filename = '/home/os17592/dev/datasets/Locations/gsv/31H_eJ2pNG05muMtNId6yw.jpg'
a = cv2.imread(filename)
cv2.imshow('a', a)
cv2.waitKey(0)