
"""
References: https://stackoverflow.com/a/56762262/12836447
"""

import cv2
import numpy as np
import os, argparse

# Argument Parsing
ap = argparse.ArgumentParser()
ap.add_argument("-sr", "--show_result", required=False, help="whether need to show result or not", default=False, type=str)
ap.add_argument("-i", "--image", required=False, help="image source", default=None, type=str)
ap.add_argument("-dbg", "--debug", required=False, help="whether need to show debug or not", default="False", type=str)
args = vars(ap.parse_args())
show_result= True if args['show_result'] == "True" else False
show_debug= True if args['debug'] == "True" else False

# Main Code
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# load image and convert to hsv
img_path= args['image'] if args['image'] is not None else 'data/edge-detection/sample-03.jpg'
img_extension = os.path.splitext(img_path)[1]

img = cv2.imread(os.path.join(BASE_DIR, img_path))

# draw gray box around image to detect edge buildings
h, w = img.shape[: 2]
cv2.rectangle(img, (0, 0), (w - 1, h - 1), (50, 50, 50), 1)

# convert image to HSV
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# image = cv2.imread(os.path.join(BASE_DIR, img_path))
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (3, 3), 0)
thresh = cv2.threshold(blurred, 240, 255, cv2.THRESH_BINARY_INV)[1]
# define color ranges
low_yellow = (0, 28, 0)
high_yellow = (27, 255, 255)

low_gray = (0, 0, 0)
high_gray = (179, 255, 233)

# create masks
yellow_mask = cv2.inRange(hsv, low_yellow, high_yellow)
gray_mask = cv2.inRange(hsv, low_gray, high_gray)

# combine masks
combined_mask = cv2.bitwise_or(yellow_mask, gray_mask)
kernel = np.ones((3, 3), dtype = np.uint8)
combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_DILATE, kernel)

# findcontours
contours, hier = cv2.findContours(combined_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# find and draw buildings
for x in range(len(contours)): #if a contour has not contours inside of it, draw the shape filled
  c = hier[0][x][2]
  if c == -1:
    cv2.drawContours(img, [contours[x]], 0, (0, 0, 255), -1)

# draw the outline of all contours
for cnt in contours:
  cv2.drawContours(img, [cnt], 0, (0, 255, 0), 2)

# display result
if show_result:
  cv2.imshow("Result - HSV", hsv)
  cv2.imshow("Result - Tresh", thresh)
  cv2.imshow("Result - Final", img)

# Saving results 
cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-1-hsv'+img_extension)), hsv)
cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-1-thresh'+img_extension)), thresh)
cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-1-image'+img_extension)), img)

# Exit 
cv2.waitKey(0)
cv2.destroyAllWindows()
