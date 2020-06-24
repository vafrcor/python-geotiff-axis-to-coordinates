import os, math, json
# import cv2
import gdal
from osgeo import osr 
from .utils import *

class GeoTiffProcessor():

  @staticmethod
  def get_axis_point_coordinate(filepath=None, x=0, y=0, opt={}):
    # References: https://stackoverflow.com/questions/50191648/gis-geotiff-gdal-python-how-to-get-coordinates-from-pixel

    debug= True if ('debug' in opt and opt['debug'] == True) else False

    # set base base path
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # open the dataset and get the geo transform matrix
    file_fullpath= os.path.join(BASE_DIR, filepath)
    file_size= get_file_size(file_fullpath, SIZE_UNIT.MB)
    ds = gdal.Open(file_fullpath) 
    xoffset, px_w, rot1, yoffset, px_h, rot2 = ds.GetGeoTransform()

    # is how to get the coordinate in space.
    posX = px_w * x + rot1 * y + xoffset
    posY = rot2 * x + px_h * y + yoffset

    # shift to the center of the pixel
    posX += px_w / 2.0
    posY += px_h / 2.0

    # get CRS from dataset 
    crs = osr.SpatialReference()
    crs.ImportFromWkt(ds.GetProjectionRef())
    # create lat/long crs with WGS84 datum
    crsGeo = osr.SpatialReference()
    crsGeo.ImportFromEPSG(4326) # 4326 is the EPSG id of lat/long crs 
    t = osr.CoordinateTransformation(crs, crsGeo)
    (lat, long, z) = t.TransformPoint(posX, posY)

    ret={
      'filepath': file_fullpath,
      'filesize': str(file_size)+' MB',
      'x': x,
      'y': y,
      'posX': posX,
      'posY': posY,
      'lat': lat,
      'long': long,
      'z': z,
      'xoffset': xoffset,
      'px_w': px_w,
      'rot1': rot1,
      'yoffset': yoffset,
      'px_h': px_h,
      'rot2': rot2
    }

    if debug:
      print('DEBUG: ')
      print(json.dumps(ret, indent=4))

    del ds, crs
    return ret
