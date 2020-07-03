import os
from osgeo import gdal 
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

options_list = [
    '-ot Byte',
    '-of JPEG',
    '-b 1', #remove "-b 2" and "-b 3" for grey image
    '-b 2',
    '-b 3',
    '-b mask',
    '-scale',
    '-co "QUALITY=70"'

] 
options_string = " ".join(options_list)

gdal.Translate(os.path.join(BASE_DIR, 'data/medium-new.jpg'), #file output
               os.path.join(BASE_DIR, 'data/medium.tif'), #file input in tif
               options=options_string)
