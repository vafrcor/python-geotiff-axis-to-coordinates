from math import log, tan, radians, cos, pi, floor, degrees, atan, sinh

def sec(x):
  return (1 / cos(x))

def latlon_to_xyz(lat, lon, z):
  tile_count = pow(2, z)
  x = (lon + 180) / 360
  y = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
  return (tile_count * x, tile_count * y)

def bbox_to_xyz(lon_min, lon_max, lat_min, lat_max, z):
  x_min, y_max = latlon_to_xyz(lat_min, lon_min, z)
  x_max, y_min = latlon_to_xyz(lat_max, lon_max, z)
  return (floor(x_min), floor(x_max), floor(y_min), floor(y_max))

def mercatorToLat(mercatorY):
  return (degrees(atan(sinh(mercatorY))))

def y_to_lat_edges(y, z):
  tile_count = pow(2, z)
  unit = 1 / tile_count
  relative_y1 = y * unit
  relative_y2 = relative_y1 + unit
  lat1 = mercatorToLat(pi * (1 - 2 * relative_y1))
  lat2 = mercatorToLat(pi * (1 - 2 * relative_y2))
  return (lat1, lat2)

def x_to_lon_edges(x, z):
  tile_count = pow(2, z)
  unit = 360 / tile_count
  lon1 = -180 + x * unit
  lon2 = lon1 + unit
  return (lon1, lon2)

def tile_edges(x, y, z):
  lat1, lat2 = y_to_lat_edges(y, z)
  lon1, lon2 = x_to_lon_edges(x, z)
  return [lon1, lat1, lon2, lat2]

def get_bounding_box_from_center_coords(latitude, longitude):
  # Source Articles:
  # - main: https://stackoverflow.com/a/25063452/12836447
  # - another approach: https://stackoverflow.com/a/238558/12836447
  
  # 111 kilometers / 1000 = 111 meters.
  # 1 degree of latitude = ~111 kilometers.
  # 1 / 1000 means an offset of coordinate by 111 meters.

  offset = 1.0 / 1000.0;
  latMax = latitude + offset;
  latMin = latitude - offset;

  # With longitude, things are a bit more complex.
  # 1 degree of longitude = 111km only at equator (gradually shrinks to zero at the poles)
  # So need to take into account latitude too, using cos(lat).

  lngOffset = offset * cos(latitude * pi / 180.0);
  lngMax = longitude + lngOffset;
  lngMin = longitude - lngOffset;
  return (lngMin, lngMax, latMin, latMax)

def gdal_reference_from_png(path: str, lon_min: float, lon_max: float, lat_min: float, lat_max: float, z: int): None
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

def gdal_convert_image(path: str, output_format: str, opt: dict): None
  from osgeo import gdal 

  BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  filename, extension = os.path.splitext(path)

  # Notes:
  # remove "-b 2" and "-b 3" for grey image
  options_list = [
    '-ot Byte',
    '-of '+output_format
  ] 

  if 'output_type' in output_format:
    options_list.append(f'-ot {opt['output_type']}')

  if 'quality' in output_format:
    options_list.append(f'-co "QUALITY={opt['quality']}"')

  if 'scale' in output_format:
    options_list.append('-scale')

  if 'remove_mask' in output_format:
    options_list.append('-b mask')

  if 'remove_band_1' in output_format:
    options_list.append('-b 1')

  if 'remove_band_2' in output_format:
    options_list.append('-b 2')

  if 'remove_band_3' in output_format:
    options_list.append('-b 3')

  if 'remove_band_4' in output_format:
    options_list.append('-b 4')

  # reference: https://svn.osgeo.org/gdal/tags/gdal_1_1_8/html/formats_list.html
  output_extension= {
    'JPG': '.jpg',
    'JPEG200': '.jp2'
    'PNG': '.png',
    'GTiff': '.tif',
    'ECW': '.ecw',
    'GIF': '.gif'
  }
  options_string = " ".join(options_list)

  gdal.Translate(os.path.join(BASE_DIR, path), os.path.join(BASE_DIR, filename.replace(extension, output_extension[output_format])), options=options_string)
