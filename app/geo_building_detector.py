import os, cv2, json, ntpath
import numpy as np
# import matplotlib.pyplot as plt
# from matplotlib.colors import hsv_to_rgb
from copy import copy
# import imutils
from geojson import Feature, Point, FeatureCollection, GeometryCollection, LineString, Polygon, dumps as geojson_dumps
from app.geotiff import GeoTiffProcessor
from app.utils import bgr_color_to_hex, bgr_color_to_rgb_hex, json_np_default_parser, get_file_size, SIZE_UNIT, bgr_color_to_hsv, bgr_color_to_rgb_hex
from app import config, logger, BASE_DIR

class GeoBuildingDetector():
  logger_base_text = 'GeoBuildingDetector \\ '
  options = {
    'show_result': False,
    'save_result': True,
    'color_preset': 'osm'
  }
  data = {
    #Color Preset using BGR Format 
    'color_presets': {
      'osm': {
        'building': {
          'fill': (202, 208, 216),
          'border': {
            'type': 'relative',
            # 'value': (30, 30, 30)
            'value': ('+30', '+30', '+30')
          },
          'contour': (36, 255, 12),
          # 'masking_color_mode': cv2.COLOR_BGR2HSV
        }
      },
      'carto': {
        'building': {
          # 'fill': (227, 239, 246),
          # 'fill': (168, 179, 186),
          'fill': (128, 139, 146),
          'border': {
            'type': 'exact',
            # 'value': (157, 172, 182),
            # 'value': (148, 160, 168),
            'value': (100, 119, 132),
            # 'value': (205, 220, 230),
            # 'value': ('+30', '+30', '+30')
          },
          'contour': (36, 255, 12),
          # 'masking_color_mode': cv2.COLOR_BGR2HSV,
          'adjust_contrast': {
            'alpha': 1.0,
            'beta': -80
          },
          'sharp_image': {
            'kernel_size': (5, 5), 
            'sigma': 0, 
            'amount': 1.0, 
            'threshold': 0
          }
          # 'masking_color_mode': cv2.COLOR_BGR2LUV
        }
      },
      'carto_gs': {
        'building': {
          'fill': (237, 237, 237),
          'border': {
            'type': 'exact',
            'value': (222, 222, 222)
          },
          'contour': (36, 255, 12),
          # 'masking_color_mode': cv2.COLOR_BGR2HSV
        }
      },
      'google': {
        'building': {
          'fill': {
            'yellow': (241,250,255),
            'gray': (244,243,241)
          },
          'border': {
            'type': 'relative',
            'value': {
              'yellow': ('+35', '+35', '+35'),
              'gray': ('+30', '+30', '+30')
            }
          },
          'contour': (36, 255, 12)
        }
      }
    },
    'path': {
      'data': os.path.join(BASE_DIR, config['path']['data_edge_detection']),
      'result': os.path.join(BASE_DIR, config['path']['data_edge_detection']) + 'results/'
    },
    'file': {
      'json_contour': '<result_path><img_name>-<preset>-contours.json',
      'json_contour_debug': '<result_path><img_name>-<preset>-contours-debug.json',
      'geojson': '<result_path><img_name>-<preset>-geo.json'
    }
  }

  def __init__(self, opts):
    self.options.update(opts)
    if not os.path.exists(self.data['path']['result']):
      os.makedirs(self.data['path']['result'])

    if not self.options['color_preset'].lower() in self.data['color_presets']:
      raise Exception("Invalid color preset: "+self.options['color_preset'])

    self.options['color_preset']= self.options['color_preset'].lower()

  def __del__(self):
    self.options = {
      'show_result': False,
      'save_result': True,
      'color_preset': 'osm'
    }

  def unsharp_mask(self, image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
    """
    Return a sharpened version of the image, using an unsharp mask.
    ref: https://stackoverflow.com/a/55590133/12836447
    """
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = float(amount + 1) * image - float(amount) * blurred
    sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
    sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
    sharpened = sharpened.round().astype(np.uint8)
    if threshold > 0:
        low_contrast_mask = np.absolute(image - blurred) < threshold
        np.copyto(sharpened, image, where=low_contrast_mask)
    return sharpened

  def transform_relative_color(self, base_color: tuple=(), color: tuple=()) -> tuple:
    temp=[]
    for idx, bbv in enumerate(color, 0):
      if bbv[0] == '+':
        temp.append(float(base_color[idx]) + float(bbv[1:]))
      elif bbv[0] == '-':
        temp.append(float(base_color[idx]) - float(bbv[1:]))
      else:
        temp.append(float(bbv))
    return tuple(temp)

  def transform_color_string_to_float(self, color: tuple=()) -> tuple :
    return (
      float(color[0]),
      float(color[1]), 
      float(color[2])
    )

  def write_image_results(self, fn_template: str, plchldr: str='<fnm>', pns: list=[]) -> None:
    for ef in pns:
      cv2.imwrite(fn_template.replace(plchldr, ef[0]), ef[1])

  def show_image_results(self, pns: list=[], opt: dict={}) -> None:
    for epn in pns:
      cv2.imshow(epn[0], epn[1])

    do_wait= bool(opt['do_wait']) if 'do_wait' in opt else True
    if do_wait:
      cv2.waitKey(0)
      cv2.destroyAllWindows()

  def get_geojson(self, filepath: tuple = (), opts: dict = {}) -> dict:
    method= 'get_geojson_'+self.options['color_preset'].lower()
    func= getattr(self, method, None)
    return func(filepath, opts)

  def get_geojson_osm(self, filepath: tuple = (), opts: dict = {}) -> dict:
    # [Step - 1] Get image + check color sampling
    img_path = os.path.join(BASE_DIR, filepath[0])
    img_tiff_path = os.path.join(BASE_DIR, filepath[1])
    img_extension = os.path.splitext(img_path)[1]
    img_name = ntpath.basename(img_path).replace(img_extension, '')
    img_base_path = img_path.replace(ntpath.basename(img_path), '')

    color_preset = self.data['color_presets'][self.options['color_preset']]
    logger.info('Color Preset (OSM): ', {'color_preset': color_preset})

    image_origin = cv2.imread(img_path, 1)
    if 'sharp_image' in color_preset['building']:
      sharp_img= self.unsharp_mask(image_origin, **color_preset['building']['sharp_image'])
      image_origin= copy(image_origin)

    image_new_contrast=[]
    if 'adjust_contrast' in color_preset['building']:
      image = cv2.convertScaleAbs(image_origin, alpha=color_preset['building']['adjust_contrast']['alpha'], beta=color_preset['building']['adjust_contrast']['beta'])
      image_new_contrast=[
        cv2.convertScaleAbs(image_origin, alpha=1.0, beta=-10),
        cv2.convertScaleAbs(image_origin, alpha=1.0, beta=-20),
        cv2.convertScaleAbs(image_origin, alpha=1.0, beta=-30),
        cv2.convertScaleAbs(image_origin, alpha=1.0, beta=-50),
        cv2.convertScaleAbs(image_origin, alpha=1.0, beta=-60)
      ]
    else:
      image = copy(image_origin)
    
    light_brown = np.uint8([[color_preset['building']['fill']]])

    # Enhance image (ref: https://chrisalbon.com/machine_learning/preprocessing_images/enhance_contrast_of_greyscale_image/)
    # image = cv2.imread('images/plane_256x256.jpg', cv2.IMREAD_GRAYSCALE)
    # image_enhanced = cv2.equalizeHist(image)
    
    # Convert BGR to HSV for masking
    color_codes = []
    hsv_fill_color = cv2.cvtColor(light_brown, cv2.COLOR_BGR2HSV)
    # hsv_fill_color = cv2.cvtColor(light_brown, color_preset['building']['masking_color_mode'])

    # for index in hsv_fill_color: 
    # color_codes = index[0]
    color_codes = hsv_fill_color[0][0]

    # [Step - 2] Do masking on HSV Image
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # img_rgb =copy(image)

    hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    # hsv = cv2.cvtColor(img_rgb, color_preset['building']['masking_color_mode'])

    fill_color = (float(color_codes[0]), float(color_codes[1]), float(color_codes[2]))

    find_border_color=[]
    if color_preset['building']['border']['type'] == 'relative':
      temp=[]
      for idx, bbv in enumerate(color_preset['building']['border']['value'], 0):
        if bbv[0] == '+':
          temp.append(float(color_codes[idx]) + float(bbv[1:]))
        elif bbv[0] == '-':
          temp.append(float(color_codes[idx]) - float(bbv[1:]))
        else:
          temp.append(float(bbv))
      border_color= tuple(temp)

      # border_color = (float(color_codes[0]) + color_preset['building']['border']['value'][0], float(color_codes[1]) + color_preset['building']['border']['value'][1], float(color_codes[2]) + color_preset['building']['border']['value'][2])
    else :
      find_border_color = cv2.cvtColor(np.uint8([[color_preset['building']['border']['value']]]), cv2.COLOR_BGR2HSV)
      # find_border_color = cv2.cvtColor(np.uint8([[color_preset['building']['border']['value']]]), color_preset['building']['masking_color_mode'])
      border_color= (float(find_border_color[0][0][0]), float(find_border_color[0][0][1]), float(find_border_color[0][0][2]))

    logger.debug(self.logger_base_text + 'Color Info', {
      'fill_color': fill_color,
      'border_color': border_color,
      'float_border_color': find_border_color,
      'hsv_fill_color_codes': color_codes,
      'hsv_fill_color': hsv_fill_color
    })

    mask = cv2.inRange(hsv, fill_color, border_color)
    final = cv2.bitwise_and(image, image, mask = mask)

    # self.data['path']['result']
    # self.data['file']['json_contour']

    json_contour_filepath = self.data['file']['json_contour'].replace('<result_path>', self.data['path']['result']).replace('<img_name>', img_name).replace('<preset>','osm')
    json_contour_debug_filepath = self.data['file']['json_contour_debug'].replace('<result_path>', self.data['path']['result']).replace('<img_name>', img_name).replace('<preset>','osm')
    geojson_filepath = self.data['file']['geojson'].replace('<result_path>', self.data['path']['result']).replace('<img_name>', img_name).replace('<preset>','osm')

    final_gray = cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
    final_blurred = cv2.GaussianBlur(final_gray, (5, 5), 0)
    ret, final_thresh = cv2.threshold(final_blurred, 127, 255, 0)
    contours, hierarchy = cv2.findContours(final_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ctr_json_str = json.dumps({
        'contours': contours,
        'hierarchy': hierarchy
      },
      default = json_np_default_parser)
    ctr_json = json.loads(ctr_json_str)

    ctr_points = []
    for cidx in range(len(ctr_json['contours'])):
      ctr_points.append(list(map(lambda x: x[0], ctr_json['contours'][cidx])))

    # [Step - 4] Find Contours Geographic Coordinates
    geotiff_image = img_tiff_path
    translate_coords = GeoTiffProcessor.get_multi_polygon_axis_point_coordinates(geotiff_image, ctr_points, {
      'debug': False
    })

    final_coords = []
    geo_features = []
    for poly in translate_coords['coords']:
      poly_coords = []
      poly_geo_coords = []
      for cr in poly:
        poly_coords.append({
          'x': cr['x'],
          'y': cr['y'],
          'latitude': cr['lat'],
          'longitude': cr['long']
        })
        poly_geo_coords.append((cr['long'], cr['lat']))

      # add final closing point
      poly_geo_coords.append((poly[0]['long'], poly[0]['lat']))
      final_coords.append(poly_coords)
      geo_feature = Feature(geometry = Polygon([poly_geo_coords], precision = 15))
      geo_features.append(geo_feature)

    geo_feature_collection = FeatureCollection(geo_features)
    geo_feature_collection_dump = geojson_dumps(geo_feature_collection, sort_keys = True)

    with open(json_contour_filepath, 'w') as outfile:
      json.dump(final_coords, outfile)

    with open(geojson_filepath, 'w') as outfile:
      outfile.write(geo_feature_collection_dump)

    # [Step - 5] Draw contours to original image clone
    final_wctrs = copy(image)# final_wctrs = copy(image_origin)# final_wctrs = copy(final)
    for c in contours:
      cv2.drawContours(final_wctrs, [c], 0, color_preset['building']['contour'], 2)

    # Build result
    polygon_len = len(ctr_points)
    r = {
      'file_path': geojson_filepath,
      'file_size': str(get_file_size(geojson_filepath, SIZE_UNIT.KB))+' KB',
      'polygon_total': polygon_len
    }
    if 'return_polygon_data' in opts and bool(opts['return_polygon_data']):
      r['geojson'] = json.loads(geo_feature_collection_dump)

    if self.options['save_result']:
      result_ftemplate = self.data['path']['result'] + img_name + '-<fnm>' + img_extension
      if 'sharp_image' in color_preset['building']:
        cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-0-sharpen-1'), sharp_img)
      if 'adjust_contrast' in color_preset['building']:
        cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-0-contrast-1'), image_new_contrast[0])
        cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-0-contrast-2'), image_new_contrast[1])
        cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-0-contrast-3'), image_new_contrast[2])
        cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-0-contrast-4'), image_new_contrast[3])
        cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-0-contrast-5'), image_new_contrast[4])
      cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-1-hsv-light-color'), hsv_fill_color)
      cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-2-image-bgr'), image)
      cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-3-image-rgb'), img_rgb)
      cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-4-hsv'), hsv)
      cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-5-final'), final)
      cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-6-image-gray'), final_gray)
      cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-7-final-blurred'), final_blurred)
      cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-8-final-thresh'), final_thresh)
      cv2.imwrite(result_ftemplate.replace('<fnm>', 'step-9-image-final-with-contours'), final_wctrs)

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

      # [Step - ending] Clean - up
      del contours, hierarchy, image, hsv_fill_color, img_rgb, hsv, final, final_gray, final_wctrs, final_blurred, final_thresh, ctr_json, ctr_json_str, final_coords, geo_features, ctr_points
      return r
    else:
      # [Step - ending] Clean - up
      del contours, hierarchy, image, hsv_fill_color, img_rgb, hsv, final, final_gray, final_wctrs, final_blurred, final_thresh, ctr_json, ctr_json_str, final_coords, geo_features, ctr_points
      return r

  def get_geojson_google(self, filepath: tuple = (), opts: dict = {}) -> dict:
    # [Step - 1] Get image + check color sampling
    img_path = os.path.join(BASE_DIR, filepath[0])
    img_tiff_path = os.path.join(BASE_DIR, filepath[1])
    img_extension = os.path.splitext(img_path)[1]
    img_name = ntpath.basename(img_path).replace(img_extension, '')
    img_base_path = img_path.replace(ntpath.basename(img_path), '')

    color_preset = self.data['color_presets'][self.options['color_preset']]
    logger.info('Color Preset (GMAP): ', {'color_preset': color_preset})

    image = cv2.imread(img_path, 1)
      
    fc_bgr_building_yellow= color_preset['building']['fill']['yellow']
    fc_bgr_building_gray= color_preset['building']['fill']['gray']

    fc_hsv_building_yellow = bgr_color_to_hsv(fc_bgr_building_yellow)
    fc_hsv_building_gray = bgr_color_to_hsv(fc_bgr_building_gray)

    if color_preset['building']['border']['type'] == 'relative':
      fc_hsv_building_yellow_darker= self.transform_relative_color(fc_hsv_building_yellow, color_preset['building']['border']['value']['yellow'])
      fc_hsv_building_gray_darker= self.transform_relative_color(fc_hsv_building_gray, color_preset['building']['border']['value']['gray'])
    else :
      find_border_color = cv2.cvtColor(np.uint8([[color_preset['building']['border']['value']]]), cv2.COLOR_BGR2HSV)
      fc_hsv_building_yellow_darker= self.transform_color_string_to_float(color_preset['building']['border']['value']['yellow'])
      fc_hsv_building_gray_darker= self.transform_color_string_to_float(color_preset['building']['border']['value']['gray'])

    logger.debug(self.logger_base_text + 'Color Info', {
      'fill_color_bgr': {
        'yellow': fc_bgr_building_yellow,
        'gray': fc_bgr_building_gray
      },
      'fill_color_hsv': {
        'yellow': fc_hsv_building_yellow,
        'gray': fc_hsv_building_gray
      },
      'border_color_hsv': {
        'yellow': fc_hsv_building_yellow_darker,
        'gray': fc_hsv_building_gray_darker
      }
    })

    # [Step-2] Do masking on HSV Image 
    img_rgb= cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    hsv= cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)

    mask_yellow = cv2.inRange(hsv, fc_hsv_building_yellow, fc_hsv_building_yellow_darker)
    mask_gray = cv2.inRange(hsv, fc_hsv_building_gray, fc_hsv_building_gray_darker)
    final= cv2.bitwise_or(image, image, mask=mask_yellow + mask_gray)

    # [Step-3] Find Contours
    json_contour_filepath = self.data['file']['json_contour'].replace('<result_path>', self.data['path']['result']).replace('<img_name>', img_name).replace('<preset>','google')
    json_contour_debug_filepath = self.data['file']['json_contour_debug'].replace('<result_path>', self.data['path']['result']).replace('<img_name>', img_name).replace('<preset>','google')
    geojson_filepath = self.data['file']['geojson'].replace('<result_path>', self.data['path']['result']).replace('<img_name>', img_name).replace('<preset>','google')

    final_gray = cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
    final_blurred = cv2.GaussianBlur(final_gray, (3, 3), 0)
    ret, final_thresh = cv2.threshold(final_blurred, 127, 255, 0)

    contours, hierarchy = cv2.findContours(final_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    ctr_json_str= json.dumps({'contours': contours, 'hierarchy': hierarchy}, default=json_np_default_parser)
    ctr_json= json.loads(ctr_json_str)

    ctr_points=[]
    for cidx in range(len(ctr_json['contours'])):
      ctr_points.append(list(map(lambda x: x[0], ctr_json['contours'][cidx])))

    # [Step - 4] Find Contours Geographic Coordinates
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

    with open(json_contour_filepath, 'w') as outfile:
      json.dump(final_coords, outfile)

    with open(geojson_filepath, 'w') as outfile:
      outfile.write(geo_feature_collection_dump)

    # [Step-5] Draw contours to original image clone
    final_wctrs= copy(image)
    for c in contours:
      cv2.drawContours(final_wctrs, [c], 0, (36, 255, 12), 2)

    # Build result
    polygon_len = len(ctr_points)
    r = {
      'file_path': geojson_filepath,
      'file_size': str(get_file_size(geojson_filepath, SIZE_UNIT.KB))+' KB',
      'polygon_total': polygon_len
    }
    if 'return_polygon_data' in opts and bool(opts['return_polygon_data']):
      r['geojson'] = json.loads(geo_feature_collection_dump)

    if self.options['save_result']:
      result_ftemplate = self.data['path']['result'] + img_name + '-gmap-<fnm>' + img_extension

      self.write_image_results(result_ftemplate, '<fnm>', [
        ('step-1-1-hsv-building-yellow', fc_hsv_building_yellow),
        ('step-1-2-hsv-building-gray', fc_hsv_building_gray),
        ('step-2-image-bgr', image),
        ('step-3-image-rgb', img_rgb),
        ('step-4-0-hsv', hsv),
        ('step-4-1-hsv-mask-yellow', mask_yellow),
        ('step-4-1-hsv-mask-gray', mask_gray),
        ('step-5-final', final),
        ('step-6-image-gray', final_gray),
        ('step-7-final-blurred', final_blurred),
        ('step-8-final-thresh', final_thresh),
        ('step-9-image-final-with-contours', final_wctrs)
      ])

    if self.options['show_result']:
      show_image_results([
        ("Step - 1-1 (HSV Yellow Color)", np.uint8([[fc_hsv_building_yellow]])),
        ("Step - 1-2 (HSV Gray Color)", np.uint8([[fc_hsv_building_gray]])),
        ("Step - 2 (Image - BGR)", image),
        ("Step - 3 ( Image - RGB)", img_rgb),
        ("Step - 4-0 (HSV)", hsv),
        ("Step - 5 (Final)", final),
        ("Step - 6 (Final - Gray)", final_gray),
        ("Step - 7 (Final - Gray Blurred)", final_blurred),
        ("Step - 8 (Final - Gray Thresh)", final_thresh),
        ("Step - 9 (Final - with contours)", final_wctrs)
      ])

      # [Step - ending] Clean - up
      del contours, hierarchy, image, fc_hsv_building_yellow, img_rgb, hsv, final, final_gray, final_wctrs, final_blurred, final_thresh, mask_yellow, mask_gray, fc_hsv_building_gray
      return r
    else:
      # [Step - ending] Clean - up
      del contours, hierarchy, image, fc_hsv_building_yellow, img_rgb, hsv, final, final_gray, final_wctrs, final_blurred, final_thresh, mask_yellow, mask_gray, fc_hsv_building_gray
      return r

  def get_geojson_carto(self, filepath: tuple = (), opts: dict = {}) -> dict:
    r = {
      'file_path': None,
      'file_size': '0 KB',
      'polygon_total': 0
    }
    return r

  def get_geojson_carto_gs(self, filepath: tuple = (), opts: dict = {}) -> dict:
    r = {
      'file_path': None,
      'file_size': '0 KB',
      'polygon_total': 0
    }
    return r
