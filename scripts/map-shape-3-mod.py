import sys, os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)

import cv2, json, ntpath
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
import argparse, pprint
from copy import copy
import imutils
from geojson import Feature, Point, FeatureCollection, GeometryCollection, LineString, Polygon, dumps as geojson_dumps
from app.shape_detector import ShapeDetector
from app.geotiff import GeoTiffProcessor
from app.utils import bgr_color_to_hex, bgr_color_to_rgb_hex, json_np_default_parser

# [Step-0] Argument Parsing
ap = argparse.ArgumentParser()
ap.add_argument("-sr", "--show_result", required=False, help="whether need to show result or not", default=False, type=str)
ap.add_argument("-i", "--image", required=False, help="image source", default=None, type=str)
ap.add_argument("-dbg", "--debug", required=False, help="whether need to show debug or not", default="False", type=str)
args = vars(ap.parse_args())
show_result= True if args['show_result'] == "True" else False
show_debug= True if args['debug'] == "True" else False

img_path= args['image'] if args['image'] is not None else 'data/edge-detection/sample-04.png'
img_extension = os.path.splitext(img_path)[1]
img_name= ntpath.basename(img_path).replace(img_extension,'')
img_base_path= img_path.replace(ntpath.basename(img_path),'')
img_base_results_path= img_base_path+'results/'


# [Step-1] Get image + check color sampling
image= cv2.imread(os.path.join(BASE_DIR, img_path), 1)

# BGR code color for Building in OpenStreetMaps is (224,217,211)
# light_brown = np.uint8([[[224,217,211]]]) 
light_brown = np.uint8([[[202,208,216 ]]]) 

if show_debug:
  print('-> light_brown: ', light_brown);

# Convert BGR to HSV for masking
color_codes=[]
hsv_light_brown = cv2.cvtColor(light_brown,cv2.COLOR_BGR2HSV)

# for index in hsv_light_brown:
#   color_codes=index[0]
color_codes=hsv_light_brown[0][0]

"""

clr_building_brown= image[794,623]
clr_building_dark_brown= image[801,618]
clr_land_light_brown= image[586,967]
if show_debug:
  print('-> HSV Light Brown: ', hsv_light_brown)  
  print('-> HSV Light Brown \\ Color Codes: ', color_codes)
  print('-> Color \\ Building \\ Brown: {} (BGR Hex: {} | RGB Hex: {})'.format(clr_building_brown, bgr_color_to_hex(clr_building_brown), bgr_color_to_rgb_hex(clr_building_brown)))  
  print('-> Color \\ Building \\ Dark Brown: {} (BGR Hex: {} | RGB Hex: {})'.format(clr_building_dark_brown, bgr_color_to_hex(clr_building_dark_brown), bgr_color_to_rgb_hex(clr_building_dark_brown)))
  print('-> Color \\ Land \\ Light Brown: {} (BGR Hex: {} | RGB Hex: {})'.format(clr_land_light_brown, bgr_color_to_hex(clr_land_light_brown), bgr_color_to_rgb_hex(clr_land_light_brown)))

"""

# image_origin= cv2.imread(os.path.join(BASE_DIR, img_path), 1)
# image = imutils.resize(image_origin, width=300)
# ratio = image_origin.shape[0] / float(image.shape[0])

# [Step-2] Do masking on HSV Image 
# cream= (13, 17, 216)
# brown = (100, 100, 226)

img_rgb= cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
hsv= cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
brown = (float(color_codes[0]), float(color_codes[1]), float(color_codes[2]))
darker_brown = (float(color_codes[0])+30, float(color_codes[1])+30, float(color_codes[2])+30)

if show_debug:
  print('-> HSV Color Code \\ Brown: ', brown) 
  print('-> HSV Color Code \\ Darker Brown: ', darker_brown)  

# exit()

mask = cv2.inRange(hsv, brown, darker_brown)
final= cv2.bitwise_and(image, image, mask=mask)

# [Step-3] Find Contours
json_contour_filepath= os.path.join(BASE_DIR, img_base_results_path+img_name+'-contours-method-3.json')
json_contour_debug_filepath= os.path.join(BASE_DIR, img_base_results_path+img_name+'-contours-method-3-debug.json')
geojson_filepath= os.path.join(BASE_DIR, img_base_results_path+img_name+'-method-3-geojson.json')

final_gray = cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
final_blurred = cv2.GaussianBlur(final_gray, (5, 5), 0)
ret, final_thresh = cv2.threshold(final_blurred, 127, 255, 0)
# contours, hierarchy = cv2.findContours(final_thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
contours, hierarchy = cv2.findContours(final_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

ctr_json_str= json.dumps({'contours': contours, 'hierarchy': hierarchy}, default=json_np_default_parser)
ctr_json= json.loads(ctr_json_str)

ctr_points=[]
for cidx in range(len(ctr_json['contours'])):
  ctr_points.append(list(map(lambda x: x[0], ctr_json['contours'][cidx])))

# [Step-4] Find Contours Geographic Coordinates 
geotiff_image= img_path.replace(img_extension, '.tif')
translate_coords= GeoTiffProcessor.get_multi_polygon_axis_point_coordinates(geotiff_image, ctr_points, {'debug': False})

final_coords=[]
geo_features=[]
for poly in translate_coords['coords']:
  poly_coords=[]
  poly_geo_coords=[]
  for cr in poly:
    poly_coords.append({'x': cr['x'], 'y': cr['y'], 'latitude': cr['lat'], 'longitude': cr['long']})
    poly_geo_coords.append((cr['long'], cr['lat']))

  # add final closing point
  poly_geo_coords.append((poly[0]['long'], poly[0]['lat']))
  final_coords.append(poly_coords)
  geo_feature= Feature(geometry=Polygon([poly_geo_coords], precision=15))
  geo_features.append(geo_feature)
  

geo_feature_collection = FeatureCollection(geo_features)
geo_feature_collection_dump = geojson_dumps(geo_feature_collection, sort_keys=True)

# new_ctrs=[]
# new_ctrs_debug=[]
# for cidx in range(len(contours)):
#   contour= contours[cidx]
#   peri = cv2.arcLength(contour, True)
#   approx = cv2.approxPolyDP(contour, 0.04 * peri, True)
#   new_ctrs_debug.append({
#     'peri': peri,
#     'approx': approx,
#     'coords': json.dumps(list(map(lambda x: x[0], ctr_json['contours'][cidx])))
#   })
#   new_ctrs.append(approx)

with open(json_contour_filepath, 'w') as outfile:
  # json.dump(contours, outfile, default=json_np_default_parser)
  # json.dump({'contours': ctr_points, 'contours_coords': translate_coords.coords}, outfile)
  json.dump(final_coords, outfile)
  # json.dump(new_ctrs, outfile, default=json_np_default_parser)

with open(geojson_filepath, 'w') as outfile:
  # json.dump(contours, outfile, default=json_np_default_parser)
  # json.dump({'contours': ctr_points, 'contours_coords': translate_coords.coords}, outfile)
  outfile.write(geo_feature_collection_dump)

# if show_debug:
#   with open(json_contour_debug_filepath, 'w') as outfile2:
#     json.dump(new_ctrs_debug, outfile2, default=json_np_default_parser)

# [Step-5] Draw contours to original image clone
final_wctrs= copy(image)
# final_wctrs= copy(image_origin)
# final_wctrs= copy(final)
# for c in new_ctrs:
for c in contours:
  # c = c.astype("float")
  # c *= ratio
  # c = c.astype("int")
  cv2.drawContours(final_wctrs, [c], 0, (36, 255, 12), 2)

"""
# Analyze contours
# - load the image and resize it to a smaller factor so that
# - the shapes can be approximated better
final_shape_ctrs= copy(final_thresh)
resized = imutils.resize(final_shape_ctrs, width=300)
ratio = final_shape_ctrs.shape[0] / float(resized.shape[0])
cnts = cv2.findContours(final_shape_ctrs, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
# cnts = imutils.grab_contours((contours, hierarchy))

sd = ShapeDetector()

# loop over the contours
for c in cnts:
  # compute the center of the contour, then detect the name of the
  # shape using only the contour
  M = cv2.moments(c)
  cX = int((M["m10"] / M["m00"]) * ratio)
  cY = int((M["m01"] / M["m00"]) * ratio)
  shape = sd.detect(c)
  # multiply the contour (x, y)-coordinates by the resize ratio,
  # then draw the contours and the name of the shape on the image
  c = c.astype("float")
  c *= ratio
  c = c.astype("int")
  cv2.drawContours(final_shape_ctrs, [c], -1, (0, 255, 0), 2)
  cv2.putText(final_shape_ctrs, shape, (cX, cY), cv2.FONT_HERSHEY_SIMPLEX,
    0.5, (255, 255, 255), 2)
"""

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
# cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-9-2-image-final-resized')), resized)
# cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-3-step-10-image-final-with-shape-contours')), final_shape_ctrs)

def clean_up():
  global contours, hierarchy, new_ctrs, image, hsv_light_brown, img_rgb, hsv, final, final_gray, final_wctrs, final_blurred, final_thresh
  del contours, hierarchy, image, hsv_light_brown, img_rgb, hsv, final, final_gray, final_wctrs, final_blurred, final_thresh
  # del new_ctrs

# show the final image
if show_debug and show_result:
  cv2.imshow("Step - 1 (HSV Light Color)", hsv_light_brown)
  cv2.imshow("Step - 2 (Image - BGR)", image)
  cv2.imshow("Step - 3 ( Image - RGB)", img_rgb)
  cv2.imshow("Step - 4 (HSV)", hsv)
  cv2.imshow("Step - 5 (Final)", final)
  cv2.imshow("Step - 6 (Final - Gray)", final_gray)
  cv2.imshow("Step - 7 (Final - Gray Blurred)", final_blurred)
  cv2.imshow("Step - 8 (Final - Gray Thresh)", final_thresh)
  cv2.imshow("Step - 9 (Final - with contours)", final_wctrs)
  # cv2.imshow("Step - 10 (Final - with shape contours)", final_shape_ctrs)
  cv2.waitKey(0)
  cv2.destroyAllWindows()

  # plt.subplot(1,2,1)
  # plt.imshow(final, cmap="gray")
  # plt.title('OSM Image')
  # plt.xticks([]), plt.yticks([])
  # plt.show()

  clean_up()
else:
  clean_up()
