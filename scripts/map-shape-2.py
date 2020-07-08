"""
References: https://stackoverflow.com/a/56743344/12836447 
"""

import cv2
import os
import argparse

# Argument Parsing
ap = argparse.ArgumentParser()
ap.add_argument("-sr", "--show_result", required=False, help="whether need to show result or not", default=False, type=str)
ap.add_argument("-i", "--image", required=False, help="image source", default=None, type=str)
ap.add_argument("-dbg", "--debug", required=False, help="whether need to show debug or not", default="False", type=str)
args = vars(ap.parse_args())
show_result= True if args['show_result'] == "True" else False
show_debug= True if args['debug'] == "True" else False

# Main Logic
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
img_path= args['image'] if args['image'] is not None else 'data/edge-detection/sample-03.jpg'
img_extension = os.path.splitext(img_path)[1]

image = cv2.imread(os.path.join(BASE_DIR, img_path))
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (3, 3), 0)
thresh = cv2.threshold(blurred, 240, 255, cv2.THRESH_BINARY_INV)[1]
canny = cv2.Canny(thresh, 50, 255, 1)

cnts = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if len(cnts) == 2 else cnts[1]

for c in cnts:
  cv2.drawContours(image, [c], 0, (36, 255, 12), 2)

# Showing results
if show_result:
  cv2.imshow('Result - Gray', gray)
  cv2.imshow('Result - Thresh', thresh)
  cv2.imshow('Result - Canny', canny)
  cv2.imshow('Result - Final', image)

# Saving results 
cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-2-thresh'+img_extension)), thresh)
cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-2-gray'+img_extension)), gray)
cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-2-canny'+img_extension)), canny)
cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-2-image'+img_extension)), image)

# Exit 
cv2.waitKey(0)
cv2.destroyAllWindows()
