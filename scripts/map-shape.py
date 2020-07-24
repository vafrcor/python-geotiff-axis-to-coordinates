
"""
References: https://stackoverflow.com/a/56762262/12836447
"""
import sys, os, json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)

import cv2
import numpy as np
import argparse, ntpath
from copy import copy
import imutils
from app.utils import pretty_print, bgr_color_to_hex, bgr_color_to_rgb_hex, bgr_color_to_hsv, hsv_color_to_bgr, json_np_default_parser
from geojson import Feature, Point, FeatureCollection, GeometryCollection, LineString, Polygon, dumps as geojson_dumps
from app.geotiff import GeoTiffProcessor

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
img_name= ntpath.basename(img_path).replace(img_extension,'')
img_base_path= img_path.replace(ntpath.basename(img_path),'')
img_base_results_path= img_base_path+'results/'

img = cv2.imread(os.path.join(BASE_DIR, img_path))
img_original= copy(img)

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
# low_gray = (0, 0, 0)
# high_gray = (179, 255, 233)

# low_yellow = (22, 15, 255)
# high_yellow = (23, 64, 251)

low_gray = (0, 0, 0)
high_gray = (100, 3, 243)

## works color
# low_gray = (0, 0, 0)
# high_gray = (120, 4, 240)

## original color
# low_gray = (107, 59, 226)
# high_gray = (11, 142, 255)

# low_yellow = bgr_color_to_hsv((22, 15, 255))
# high_yellow = bgr_color_to_hsv((23, 64, 251))
# low_gray= bgr_color_to_hsv((244, 243, 241))
# high_gray = bgr_color_to_hsv((121, 121, 121))

# low_gray_bgr = (244, 243, 241)
# high_gray_bgr = (240, 236, 235)
# low_gray_hsv=cv2.cvtColor(np.uint8([[low_gray_bgr]]), cv2.COLOR_BGR2HSV)
# high_gray_hsv=cv2.cvtColor(np.uint8([[high_gray_bgr]]), cv2.COLOR_BGR2HSV)
# low_gray= low_gray_hsv[0][0]
# high_gray= high_gray_hsv[0][0]

if show_debug:
  pretty_print('Color Space:', {
    'hsv': {
      'low_yellow': low_yellow,
      'high_yellow': high_yellow,
      'low_gray': low_gray,
      'high_gray': high_gray
    },
    'bgr': {
      'low_yellow': hsv_color_to_bgr(low_yellow),
      'high_yellow': hsv_color_to_bgr(high_yellow),
      'low_gray': hsv_color_to_bgr(low_gray),
      'high_gray': hsv_color_to_bgr(high_gray)
    },
    'sample':{
      'hsv':{
        'low_yellow': (0, 28, 0),
        'high_yellow': (27, 255, 255),
        'low_gray': (0, 0, 0),
        'high_gray': (179, 255, 233)
      },
      'bgr':{
        'low_yellow': hsv_color_to_bgr((0, 28, 0)),
        'high_yellow': hsv_color_to_bgr((27, 255, 255)),
        'low_gray': hsv_color_to_bgr((0, 0, 0)),
        'high_gray': hsv_color_to_bgr((179, 255, 233))
      }
    }
  })

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

# Saving results 
result_ftemplate= img_base_results_path+img_name+'-<fnm>'+img_extension;
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-1-step-1-original')), img_original)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-1-step-2-hsv')), hsv)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-1-step-3-yellow_mask')), yellow_mask)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-1-step-4-gray_mask')), gray_mask)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-1-step-5-combined_mask')), combined_mask)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-1-step-6-gray')), gray)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-1-step-7-blurred')), blurred)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-1-step-8-thresh')), thresh)

cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-1-step-9-final')), img)


# cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-1-hsv'+img_extension)), hsv)
# cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-1-thresh'+img_extension)), thresh)
# cv2.imwrite(os.path.join(BASE_DIR, img_path.replace(img_extension,'-method-1-image'+img_extension)), img)


# display result
if show_result:
  cv2.imshow("Result - Step-1-Original", img_original)
  cv2.imshow("Result - Step-2-HSV", hsv)
  cv2.imshow("Result - Step-3-Yellow Mask", yellow_mask)
  cv2.imshow("Result - Step-4-Gray Mask", gray_mask)
  cv2.imshow("Result - Step-5-Combined Mask", combined_mask)
  cv2.imshow("Result - Step-6-Gray", gray)
  cv2.imshow("Result - Step-7-Blurred", blurred)
  cv2.imshow("Result - Step-8-Tresh", thresh)
  cv2.imshow("Result - Step-9-Final", img)


# Exit 
cv2.waitKey(0)
cv2.destroyAllWindows()
