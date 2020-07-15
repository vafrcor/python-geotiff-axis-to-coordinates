import argparse, pprint
import os
from osgeo import gdal
from math import log, tan, radians, cos, pi, floor, degrees, atan, sinh

"""
References:
- OSM Bounding Box: https://wiki.openstreetmap.org/wiki/Bounding_Box
- GDAL Translate: https://gdal.org/programs/gdal_translate.html
"""

def sec(x):
  return (1 / cos(x))

def latlon_to_xyz(lat, lon, z):
  tile_count = pow(2, z)
  x = (lon + 180) / 360
  y = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
  return (tile_count * x, tile_count * y)

def tile_edges(x, y, z):
  lat1, lat2 = y_to_lat_edges(y, z)
  lon1, lon2 = x_to_lon_edges(x, z)
  return [lon1, lat1, lon2, lat2]

def bbox_to_xyz(lon_min, lon_max, lat_min, lat_max, z):
  x_min, y_max = latlon_to_xyz(lat_min, lon_min, z)
  x_max, y_min = latlon_to_xyz(lat_max, lon_max, z)
  return (floor(x_min), floor(x_max), floor(y_min), floor(y_max))

def georeference_file(path, lon_min, lon_max, lat_min, lat_max, z):
  bounds= (lon_min, lat_min, lon_max, lat_max)
  filename, extension = os.path.splitext(path)
  filepath= filename + '.tif'
  if os.path.exists(filepath):
    print('deleting existing file: '+filepath);
    os.remove(filepath)
  gdal.Translate(filepath,
    path,
    outputSRS = 'EPSG:4326',
    outputBounds = bounds)

# how to use
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# data_dir = os.path.join(BASE_DIR, 'data/geo-map/')
# zoom= 18
# lat_min= -7.975113876000217
# lon_max= 112.63672292232515
# lat_max= -7.9788751339455155
# lon_min= 112.63089179992677 
# georeference_file(data_dir+'malang-monumen-tugu.png', lon_min, lon_max, lat_min, lat_max, z)


if __name__ == "__main__":
  # Argument Parsing
  # example: python scripts/png_georeference.py -i='data/geo-map/malang-monumen-tugu.png' -z=5 -latmn=-7.975113876000217 -latmx=-7.9788751339455155 -lonmn=112.63089179992677 -lonmx=112.63672292232515

  # python scripts/png_georeference.py -i='data/geo-map/map-monumen-tugu-carto-colorfull.png' -z=18 -latmn=-7.974875248648185 -latmx=-7.979311194447356 -lonmn=112.63118147850038 -lonmx=112.63701260089876
  # python scripts/png_georeference.py -i='data/geo-map/map-monumen-tugu-carto-grayscale.png' -z=18 -latmn=-7.975013368667483 -latmx=-7.979183688915689 -lonmn=112.63118147850038 -lonmx=112.63701260089876
  
  ap = argparse.ArgumentParser()
  ap.add_argument("-i", "--image", required=True, help="Image Source", default=None, type=str)
  ap.add_argument("-z", "--zoom", required=True, help="Zoom Level", default=None, type=int)
  ap.add_argument("-latmn", "--latitude_min", required=True, help="Latitude min.", default=None, type=float)
  ap.add_argument("-latmx", "--latitude_max", required=True, help="Latitude min.", default=None, type=float)
  ap.add_argument("-lonmn", "--longitude_min", required=True, help="Longitude min.", default=None, type=float)
  ap.add_argument("-lonmx", "--longitude_max", required=True, help="Longitude max.", default=None, type=float)
  ap.add_argument("-dbg", "--debug", required=False, help="Whether need to show debug or not", default="False", type=str)
  args = vars(ap.parse_args())
  img_path= args['image'] if args['image'] is not None else False
  zoom= int(args['zoom']) if args['zoom'] is not None else False
  lat_min= float(args['latitude_min']) if args['latitude_min'] is not None else False
  lat_max= float(args['latitude_max']) if args['latitude_max'] is not None else False
  lon_min= float(args['longitude_min']) if args['longitude_min'] is not None else False
  lon_max= float(args['longitude_max']) if args['longitude_max'] is not None else False

  show_debug= True if args['debug'] == "True" else False
  print('>> Geo refrencing...')
  georeference_file(img_path, lon_min, lon_max, lat_min, lat_max, zoom)
  print('>> Done!')
