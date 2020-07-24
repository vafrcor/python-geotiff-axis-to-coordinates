"""
References: https://stackoverflow.com/a/56743344/12836447 
"""
import sys, os, json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)

import cv2
import os, ntpath
import argparse
from copy import copy 
import imutils
from app.utils import bgr_color_to_hex, bgr_color_to_rgb_hex, json_np_default_parser
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

# Main Logic
img_path= args['image'] if args['image'] is not None else 'data/edge-detection/sample-10.png'
img_extension = os.path.splitext(img_path)[1]
img_name= ntpath.basename(img_path).replace(img_extension,'')
img_base_path= img_path.replace(ntpath.basename(img_path),'')
img_base_results_path= img_base_path+'results/'

image = cv2.imread(os.path.join(BASE_DIR, img_path))
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (3, 3), 0)
thresh = cv2.threshold(blurred, 240, 255, cv2.THRESH_BINARY_INV)[1]
canny = cv2.Canny(thresh, 50, 255, 1)

# cnts, hierarchy = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
# cnts = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# cnts, hierarchy = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# cnts, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


# cnts = cnts[0] if len(cnts) == 2 else cnts[1]

cnts = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
# print('contours', cnts)

final= copy(image)
"""
for c in cnts:
  cv2.drawContours(final, [c], 0, (36, 255, 12), 2)
  # cv2.drawContours(final, [c], 0, (0, 0, 255), 2)
"""
contours, hier = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
for x in range(len(contours)): #if a contour has not contours inside of it, draw the shape filled
  c = hier[0][x][2]
  if c == -1:
    cv2.drawContours(final, [contours[x]], 0, (0, 0, 255), -1)

ddata={
  'contours': cnts, 
  # 'hierarchy': hierarchy
}
ctr_json_str= json.dumps(ddata, default=json_np_default_parser)
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

json_contour_filepath= os.path.join(BASE_DIR, img_base_results_path+img_name+'-contours-method-2.json')
geojson_filepath= os.path.join(BASE_DIR, img_base_results_path+img_name+'-method-2-geojson.json')
with open(json_contour_filepath, 'w') as outfile:
  # json.dump(contours, outfile, default=json_np_default_parser)
  # json.dump({'contours': ctr_points, 'contours_coords': translate_coords.coords}, outfile)
  json.dump(final_coords, outfile)
  # json.dump(new_ctrs, outfile, default=json_np_default_parser)

with open(geojson_filepath, 'w') as outfile:
  # json.dump(contours, outfile, default=json_np_default_parser)
  # json.dump({'contours': ctr_points, 'contours_coords': translate_coords.coords}, outfile)
  outfile.write(geo_feature_collection_dump)


# Saving results 
result_ftemplate= img_base_results_path+img_name+'-<fnm>'+img_extension;
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-2-step-1-gray')), gray)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-2-step-2-blurred')), blurred)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-2-step-3-thresh')), thresh)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-2-step-4-canny')), canny)
cv2.imwrite(os.path.join(BASE_DIR, result_ftemplate.replace('<fnm>','method-2-step-5-final')), final)


# Showing results
if show_result:
  cv2.imshow('Step - 1 (Gray)', gray)
  cv2.imshow('Step - 2 (Blurred)', blurred)
  cv2.imshow('Step - 3 (Thresh)', thresh)
  cv2.imshow('Step - 4 (Canny)', canny)
  cv2.imshow('Step - 5 (Final)', final)
  # Exit 
  cv2.waitKey(0)
  cv2.destroyAllWindows()
