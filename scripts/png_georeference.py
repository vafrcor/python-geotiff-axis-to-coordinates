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
  gdal.Translate(filename + '.tif',
    path,
    outputSRS = 'EPSG:4326',
    outputBounds = bounds)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(BASE_DIR, 'data/geo-map/')
z= 18
lat_min= -7.975113876000217
lon_max= 112.63672292232515
lat_max= -7.9788751339455155
lon_min= 112.63089179992677 
georeference_file(data_dir+'malang-monumen-tugu.png', lon_min, lon_max, lat_min, lat_max, z)
