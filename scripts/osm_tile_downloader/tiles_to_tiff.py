import math, time
import urllib.request
import os
import glob
import subprocess
import shutil
from tile_convert import bbox_to_xyz, tile_edges, get_bounding_box_from_center_coords
from osgeo import gdal
from urllib.parse import urlsplit
"""
References: 
- Article: 
  - https://jimmyutterstrom.com/blog/2019/06/05/map-tiles-to-geotiff/
  - https://gdal.org/programs/gdal_merge.html
- Source Code: https://github.com/jimutt/tiles-to-tiff
- Problem: https://github.com/OSGeo/gdal/issues/1827 (GDAL Merge street map strang pixel)
- Possible Problem Solver: 
  - https://gis.stackexchange.com/questions/48034/how-to-add-color-interpretation-for-raster-bands-using-gdal

- Script
  - `gdalbuildvrt -separate data/map-download/output/output.vrt data/map-download/temp/*.tif`
  - `gdal_translate data/map-download/output/output.vrt data/map-download/output/output.tif`
"""

#-- -- -- -- --CONFIGURATION-- -- -- -- -- - #
# tile_server = "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.png?access_token=" + os.environ.get(
#   'MAPBOX_ACCESS_TOKEN')

# tile_server = "https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoidmFmcmNvciIsImEiOiJja2NicW1nYzIwOHU3Mnp0MGZuaTgwNHJqIn0.JMY9F1fIDAgaebgxXIDXTg"
# tile_type='satellite'

# tile_server= "http://a.tiles.mapbox.com/v4/mapbox.mapbox-streets-v7/{z}/{x}/{y}@2x.png?access_token=pk.eyJ1IjoidmFmcmNvciIsImEiOiJja2NicW1nYzIwOHU3Mnp0MGZuaTgwNHJqIn0.JMY9F1fIDAgaebgxXIDXTg"
# tile_type='street_vector'

# tile_server= "https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/256/{z}/{x}/{y}?access_token=pk.eyJ1IjoidmFmcmNvciIsImEiOiJja2NicW1nYzIwOHU3Mnp0MGZuaTgwNHJqIn0.JMY9F1fIDAgaebgxXIDXTg"
# tile_type='street'

tile_server= "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
tile_type='street'

tile_host= urlsplit(tile_server).netloc
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
temp_dir = os.path.join(BASE_DIR, 'data/map-download/temp')
output_dir = os.path.join(BASE_DIR, 'data/map-download/output')

# print('dirs: ', {
#   'base_dir': BASE_DIR,
#   'temp_dir': temp_dir,
#   'output_dir': output_dir
#   })

zoom = 18
center_lat=-7.97699
center_lon=112.63409
# lon_min = 21.49147
# lon_max = 21.5
# lat_min = 65.31016
# lat_max = 65.31688

lon_min, lon_max, lat_min, lat_max = get_bounding_box_from_center_coords(center_lat,center_lon)
# print('Bounding Box: ', {
#   'lon_min': lon_min,
#   'lon_max': lon_max,
#   'lat_min': lat_min,
#   'lat_max': lat_max
# })
# exit()

#-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- - #

def download_tile(x, y, z, tile_server):
  url = tile_server.replace(
    "{x}", str(x)).replace(
    "{y}", str(y)).replace(
    "{z}", str(z)
  )
  path = f'{temp_dir}/{x}_{y}_{z}.png'

  opener = urllib.request.build_opener()
  opener.addheaders = [('User-agent', '[Map Free 4 All] [0.0.1] contact [vafrcor2009@gmail.com]')]
  urllib.request.install_opener(opener)

  urllib.request.urlretrieve(url, path)
  return (path)

def merge_tiles(input_pattern, output_path):
  # ,'-ot', 'uint16',  '-init', '255 255 255','-pct', '-separate', "-co","PHOTOMETRIC=rgb", '-of', 'GTiff'
  merge_command = ['gdal_merge.py', '-init', '255 255 255', '-of', 'GTiff' ,'-o', output_path]

  for name in glob.glob(input_pattern):
    merge_command.append(name)

  subprocess.call(merge_command)

def georeference_raster_tile(x, y, z, path):
  bounds = tile_edges(x, y, z)
  filename, extension = os.path.splitext(path)
  gdal.Translate(filename + '.tif',
    path,
    outputSRS = 'EPSG:4326',
    outputBounds = bounds)

x_min, x_max, y_min, y_max = bbox_to_xyz(lon_min, lon_max, lat_min, lat_max, zoom)

print(f"Downloading {(x_max - x_min + 1) * (y_max - y_min + 1)} tiles")

for x in range(x_min, x_max + 1):
  for y in range(y_min, y_max + 1):
    print(f"{x},{y}")
    png_path = download_tile(x, y, zoom, tile_server)
    georeference_raster_tile(x, y, zoom, png_path)
    # time.sleep(1)

time.sleep(2)
print("Download complete")

print("Merging tiles")
output_file=f'/merged-lonmn-{lon_min}_lonmx-{lon_max}_latmn-{lat_min}_latmx-{lat_max}_z-{zoom}_{tile_host}-{tile_type}.tif'
output_filename= output_dir + output_file
if os.path.exists(output_filename):
  print('deleting existing file: '+output_filename);
  os.remove(output_filename)
merge_tiles(temp_dir + '/*.tif', output_filename)
print("Merge complete")
shutil.rmtree(temp_dir)
os.makedirs(temp_dir)
