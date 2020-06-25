import os, math, json
# import cv2
import gdal
from osgeo import osr 
from .utils import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

"""
References: 
- https://stackoverflow.com/questions/50191648/gis-geotiff-gdal-python-how-to-get-coordinates-from-pixel
"""

class GeoTiffProcessor():

  @staticmethod
  def read_coordinate(ds=None, transformPoint=None, x=0, y=0):
    # xoffset, px_w, rot1, yoffset, px_h, rot2 = ds.GetGeoTransform()
    xoffset, px_w, rot1, yoffset, rot2, px_h = ds.GetGeoTransform()
    
    # This is how to get the coordinate in space.
    posX = px_w * x + rot1 * y + xoffset
    posY = rot2 * x + px_h * y + yoffset

    # Shift to the center of the pixel
    posX += px_w / 2.0
    posY += px_h / 2.0
      
    # Get lat-long coordinates
    # (lat, long, z) = transformPoint.TransformPoint(posX, posY)
    (long, lat, z) = transformPoint.TransformPoint(posX, posY)

    r={
      'lat': lat,
      'long': long,
      'z': z,
      'posX': posX,
      'posY': posY,
      'xoffset': xoffset,
      'px_w': px_w,
      'rot1': rot1,
      'yoffset': yoffset,
      'px_h': px_h,
      'rot2': rot2
    }
    lat=long=z=posX=posY=xoffset=px_w=rot1=yoffset=px_h=rot2= None
    return r

  @staticmethod
  def get_axis_point_coordinate(filepath=None, x=0, y=0, opt={}):
    debug= True if ('debug' in opt and opt['debug'] == True) else False

    # open the dataset and get the geo transform matrix
    file_fullpath= os.path.join(BASE_DIR, filepath)
    file_size= get_file_size(file_fullpath, SIZE_UNIT.MB)
    ds = gdal.Open(file_fullpath) 
    crs = osr.SpatialReference()
    # get CRS from dataset 
    crs.ImportFromWkt(ds.GetProjectionRef())
    # create lat/long crs with WGS84 datum
    crsGeo = osr.SpatialReference()
    crsGeo.ImportFromEPSG(4326) # 4326 is the EPSG id of lat/long crs 
    tp = osr.CoordinateTransformation(crs, crsGeo)
    coords= GeoTiffProcessor.read_coordinate(ds, tp, x, y)

    info={
      'filepath': file_fullpath,
      'filesize': str(file_size)+' MB',
      'x': x,
      'y': y
    }

    ret = {**info, **coords}
    
    if debug:
      print('DEBUG: ')
      print(json.dumps(ret, indent=2))

    del ds, crs
    return ret

  @staticmethod
  def get_polygon_axis_point_coordinates(filepath=None, points= (), opt={}):
    debug= True if ('debug' in opt and opt['debug'] == True) else False

    # open the dataset and get the geo transform matrix
    file_fullpath= os.path.join(BASE_DIR, filepath)
    file_size= get_file_size(file_fullpath, SIZE_UNIT.MB)
    ds = gdal.Open(file_fullpath) 
    crs = osr.SpatialReference()
    # get CRS from dataset 
    crs.ImportFromWkt(ds.GetProjectionRef())
    # create lat/long crs with WGS84 datum
    crsGeo = osr.SpatialReference()
    crsGeo.ImportFromEPSG(4326) # 4326 is the EPSG id of lat/long crs 
    tp = osr.CoordinateTransformation(crs, crsGeo)
    
    ret={
      'filepath': file_fullpath,
      'filesize': str(file_size)+' MB',
      'points': points,
      'coords': []
    }

    for point in points:
      x,y= point
      eret={
        'x':x,
        'y':y
      }
      translate=GeoTiffProcessor.read_coordinate(ds, tp, x, y)
      e={**eret, **translate}
      ret['coords'].append(e)
    
    if debug:
      print('DEBUG: ')
      print(json.dumps(ret, indent=2))

    del ds, crs
    return ret

  @staticmethod
  def get_multi_polygon_axis_point_coordinates(filepath=None, polygons= (), opt={}):
    debug= True if ('debug' in opt and opt['debug'] == True) else False

    # open the dataset and get the geo transform matrix
    file_fullpath= os.path.join(BASE_DIR, filepath)
    file_size= get_file_size(file_fullpath, SIZE_UNIT.MB)
    ds = gdal.Open(file_fullpath) 
    crs = osr.SpatialReference()
    # get CRS from dataset 
    crs.ImportFromWkt(ds.GetProjectionRef())
    # create lat/long crs with WGS84 datum
    crsGeo = osr.SpatialReference()
    crsGeo.ImportFromEPSG(4326) # 4326 is the EPSG id of lat/long crs 
    tp = osr.CoordinateTransformation(crs, crsGeo)
    
    ret={
      'filepath': file_fullpath,
      'filesize': str(file_size)+' MB',
      'polygons': polygons,
      'coords': []
    }

    for polygon in polygons:
      epoly=[]
      for point in polygon:
        x,y= point
        eret={
          'x':x,
          'y':y
        }
        translate=GeoTiffProcessor.read_coordinate(ds, tp, x, y)
        e={**eret, **translate}
        epoly.append(e)
        e = x = y = None
        
      ret['coords'].append(epoly)
      epoly=None
    
    if debug:
      print('DEBUG: ')
      print(json.dumps(ret, indent=2))

    s = crs = None
    del ds, crs
    return ret

  
