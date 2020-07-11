import os, cv2, json, ntpath
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
from copy import copy
import imutils
from geojson import Feature, Point, FeatureCollection, GeometryCollection, LineString, Polygon, dumps as geojson_dumps
from app.geotiff import GeoTiffProcessor
from app.utils import bgr_color_to_hex, bgr_color_to_rgb_hex, json_np_default_parser
from app import config, logger, BASE_DIR


class GeoBuildingDetector():
  logger_base_text= 'GeoBuildingDetector \\ '
  options={
    'show_result': False,
    'save_result': True,
    'color_preset': 'osm'
  }
  data={
    # Color Preset using BGR Format
    'color_presets': {
      'osm': {
        'building': {
          'fill': (202,208,216)
          'border': {
            'type': 'addition',
            'value': (30, 30, 30)
          },
          'contour': (36, 255, 12)
        }
      },
      'google': {}
    },
    'path': {
      'data': os.path.join(BASE_DIR, config['path']['data_edge_detection'])
      'result': os.path.join(BASE_DIR, config['path']['data_edge_detection'])+'results/'
    },
    'file': {
      'json_contour': '<result_path><img_name>-contours.json',
      'json_contour_debug': '<result_path><img_name>-contours-debug.json',
      'geojson': '<result_path><img_name>-geo.json'
    }
  }

  def __init__(self, opts):
    self.options.update(opts)
    if not os.path.exists(self.options['path']['result']):
      os.makedirs(self.options['path']['result'])

  def get_geojson(self, filepath: tuple=()): dict
    # [Step-1] Get image + check color sampling
    img_path= os.path.join(BASE_DIR, filepath[0])
    img_tiff_path= os.path.join(BASE_DIR, filepath[1])
    img_extension = os.path.splitext(img_path)[1]
    img_name= ntpath.basename(img_path).replace(img_extension,'')
    img_base_path= img_path.replace(ntpath.basename(img_path),'')
    image= cv2.imread(source_filepath, 1)

    color_preset= self.data['color_presets'][self.options['color_preset']]
    light_brown = np.uint8([[color_preset['building']['fill']]]) 

    # Convert BGR to HSV for masking
    color_codes=[]
    hsv_fill_color = cv2.cvtColor(light_brown,cv2.COLOR_BGR2HSV)

    # for index in hsv_fill_color:
    #   color_codes=index[0]
    color_codes=hsv_fill_color[0][0]

    # [Step-2] Do masking on HSV Image 
    img_rgb= cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    hsv= cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    fill_color = (float(color_codes[0]), float(color_codes[1]), float(color_codes[2]))

    if color_preset['building']['border']['type'] == 'addition': 
      border_color = (float(color_codes[0])+color_preset['building']['border']['value'][0], float(color_codes[1])+color_preset['building']['border']['value'][1], float(color_codes[2])+color_preset['building']['border']['value'][2])
    else:
      border_color= color_preset['building']['border']['value']

    logger.debug(self.logger_base_text+'Color Info', {
      'fill_color': fill_color,
      'border_color': border_color,
      'color_codes': color_codes,
      'hsv_fill_color': hsv_fill_color
      })

    mask = cv2.inRange(hsv, fill_color, darkborder_colorer_brown)
    final= cv2.bitwise_and(image, image, mask=mask)

    self.data['path']['result']
    self.data['file']['json_contour']

    json_contour_filepath= self.data['file']['json_contour'].replace('<result_path>', self.data['path']['result']).replace('<img_name>',img_name)
    json_contour_debug_filepath= self.data['file']['json_contour_debug'].replace('<result_path>', self.data['path']['result']).replace('<img_name>',img_name)
    geojson_filepath= self.data['file']['geojson'].replace('<result_path>', self.data['path']['result']).replace('<img_name>',img_name)

    final_gray = cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
    final_blurred = cv2.GaussianBlur(final_gray, (5, 5), 0)
    ret, final_thresh = cv2.threshold(final_blurred, 127, 255, 0)
    contours, hierarchy = cv2.findContours(final_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ctr_json_str= json.dumps({'contours': contours, 'hierarchy': hierarchy}, default=json_np_default_parser)
    ctr_json= json.loads(ctr_json_str)

    ctr_points=[]
    for cidx in range(len(ctr_json['contours'])):
      ctr_points.append(list(map(lambda x: x[0], ctr_json['contours'][cidx])))

    # [Step-4] Find Contours Geographic Coordinates 
    geotiff_image= img_tiff_path
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

    with open(json_contour_filepath, 'w') as outfile:
      json.dump(final_coords, outfile)

    with open(geojson_filepath, 'w') as outfile:
      outfile.write(geo_feature_collection_dump)

    # [Step-5] Draw contours to original image clone
    final_wctrs= copy(image)
    # final_wctrs= copy(image_origin)
    # final_wctrs= copy(final)
    for c in contours:
      cv2.drawContours(final_wctrs, [c], 0, color_preset['building']['contour'], 2)

    if self.options['save_result']:
      result_ftemplate= self.data['path']['result']+img_name+'-<fnm>'+img_extension;
      cv2.imwrite(result_ftemplate.replace('<fnm>','step-1-hsv-light-color'), hsv_fill_color)
      cv2.imwrite(result_ftemplate.replace('<fnm>','step-2-image-bgr'), image)
      cv2.imwrite(result_ftemplate.replace('<fnm>','step-3-image-rgb') , img_rgb)
      cv2.imwrite(result_ftemplate.replace('<fnm>','step-4-hsv'), hsv)
      cv2.imwrite(result_ftemplate.replace('<fnm>','step-5-final'), final)
      cv2.imwrite(result_ftemplate.replace('<fnm>','step-6-image-gray'), final_gray)
      cv2.imwrite(result_ftemplate.replace('<fnm>','step-7-final-blurred'), final_blurred)
      cv2.imwrite(result_ftemplate.replace('<fnm>','step-8-final-thresh'), final_thresh)
      cv2.imwrite(result_ftemplate.replace('<fnm>','step-9-image-final-with-contours'), final_wctrs)

    if self.options['show_result']:
      cv2.imshow("Step - 1 (HSV Light Color)", hsv_fill_color)
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

    # [Step-ending] Clean-up
    del contours, hierarchy, image, hsv_fill_color, img_rgb, hsv, final, final_gray, final_wctrs, final_blurred, final_thresh, ctr_json, ctr_json_str, final_coords, geo_features

    return geo_feature_collection_dump
