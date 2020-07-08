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
