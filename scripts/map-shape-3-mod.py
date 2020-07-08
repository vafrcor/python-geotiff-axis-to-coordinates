import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)

import cv2, json, ntpath
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
import argparse, pprint
from copy import copy
from app.shape_detector import ShapeDetector

# Additional Parser
def json_np_default_parser(obj):
  if type(obj).__module__ == np.__name__:
    if isinstance(obj, np.ndarray):
      return obj.tolist()
    else:
      return obj.item()
  raise TypeError('Unknown type:', type(obj))

# Argument Parsing
ap = argparse.ArgumentParser()
ap.add_argument("-sr", "--show_result", required=False, help="whether need to show result or not", default=False, type=str)
ap.add_argument("-i", "--image", required=False, help="image source", default=None, type=str)
ap.add_argument("-dbg", "--debug", required=False, help="whether need to show debug or not", default="False", type=str)
args = vars(ap.parse_args())
show_result= True if args['show_result'] == "True" else False
show_debug= True if args['debug'] == "True" else False

# Get images
img_path= args['image'] if args['image'] is not None else 'data/edge-detection/sample-04.png'
img_extension = os.path.splitext(img_path)[1]
img_name= ntpath.basename(img_path).replace(img_extension,'')
img_base_path= img_path.replace(ntpath.basename(img_path),'')
img_base_results_path= img_base_path+'results/'
# BGR code color for Building in OpenStreetMaps is (224,217,211)
light_brown = np.uint8([[[202,208,216 ]]]) 
# light_brown = np.uint8([[[224,217,211]]]) 
if show_debug:
  print('-> light_brown: ', light_brown);

#Convert BGR to HSV for masking
color_codes=[]
hsv_light_brown = cv2.cvtColor(light_brown,cv2.COLOR_BGR2HSV)

# for index in hsv_light_brown:
#   color_codes=index[0]
color_codes=hsv_light_brown[0][0]

if show_debug:
  print('-> HSV Light Brown: ', hsv_light_brown)  
  print('-> Color Codes: ', color_codes)

# Start masking the image here
image= cv2.imread(os.path.join(BASE_DIR, img_path), 1)
img_rgb= cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
hsv= cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
brown = (float(color_codes[0]), float(color_codes[1]), float(color_codes[2]))
darker_brown = (float(color_codes[0])+30, float(color_codes[1])+30, float(color_codes[2])+30)

# cream= (13, 17, 216)
# brown = (100, 100, 226)

mask = cv2.inRange(hsv, brown, darker_brown)
final= cv2.bitwise_and(image, image, mask=mask)

# findcontours
json_contour_filepath= os.path.join(BASE_DIR, img_base_results_path+img_name+'-contours-method-3.json')

final_gray = cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
final_blurred = cv2.GaussianBlur(final_gray, (5, 5), 0)
ret, final_thresh = cv2.threshold(final_blurred, 127, 255, 0)
# contours, hierarchy = cv2.findContours(final_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
contours, hierarchy = cv2.findContours(final_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


with open(json_contour_filepath, 'w') as outfile:
    json.dump(contours, outfile, default=json_np_default_parser)

final_wctrs= copy(image)
for c in contours:
  cv2.drawContours(final_wctrs, [c], 0, (36, 255, 12), 2)

# save images
result_ftemplate= img_base_results_path+img_name+'-<fnm>'+img_extension;
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-1-hsv-light-color')), hsv_light_brown)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-2-image-bgr')), image)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-3-image-rgb')) , img_rgb)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-4-hsv')), hsv)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-5-final')), final)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-6-image-gray')), final_gray)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-7-final-blurred')), final_blurred)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-8-final-thresh')), final_thresh)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-9-image-final-with-contours')), final_wctrs)


# show the final image
if show_result:
  cv2.imshow("Step - 1 (HSV Light Color)", hsv_light_brown)
  cv2.imshow("Step - 2 (Image - BGR)", image)
  cv2.imshow("Step - 3 ( Image - RGB)", img_rgb)
  cv2.imshow("Step - 4 (HSV)", hsv)
  cv2.imshow("Step - 5 (Final)", final)
  cv2.imshow("Step - 6 (Final - Gray)", final_gray)
  cv2.imshow("Step - 7 (Final - Gray Blurred)", final_blurred)
  cv2.imshow("Step - 8 (Final - Gray Thresh)", final_thresh)
  cv2.imshow("Step - 9 (Final - with contours)", final_wctrs)
  
  cv2.waitKey(0)
  cv2.destroyAllWindows()

  # plt.subplot(1,2,1)
  # plt.imshow(final, cmap="gray")
  # plt.title('OSM Image')
  # plt.xticks([]), plt.yticks([])
  # plt.show()
