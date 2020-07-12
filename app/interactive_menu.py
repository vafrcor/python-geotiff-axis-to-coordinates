import time
from app.utils import *
from app.geotiff import GeoTiffProcessor
from app.geo_building_detector import GeoBuildingDetector

class InteractiveMenu():
  name='Example Menu'
  menus={}
  image_types={
    'small': 'data/small.tif',
    'medium': 'data/medium.tif',
    'large': 'data/large.tif',
    'extra_large': 'data/extra_large.tif',
  }

  def __init__(self, name, menus={}, opt={}):
    InteractiveMenu.name= name if not name is None else self.name
    InteractiveMenu.menus= menus

  @classmethod 
  def show_menu(self):
    print(self.name)
    write_separator()

    mkeys= list(self.menus.keys())
    x=0
    for mk,mv in self.menus.items():
      x+=1
      print (str(x)+' - '+mv)

    try:
      imode = int(input("Please enter a mode: "))
      imx= imode - 1

      if imx < len(mkeys):
        if mkeys[imx] == 'exit':
          exit()
        else:
          write_separator()
          getattr(self, mkeys[imx])()
      else:
        print ("unknown mode")

      time.sleep(2)
      write_separator()
      next_menu = str(input("Do you wanted to choose another menu? [y/n]: "))
      if next_menu.lower() == 'y':
        self.show_menu()
      else:
        print ("Thank you for tried this menu. Bye...")
        exit()
    except Exception as e:
      pretty_print("unknown mode (an error occured)", {'error': read_exception_data(e)})
      # print ("unknown mode (an error occured)", {'error': read_exception_data(e)})
      write_separator()
      self.show_menu()

  @classmethod
  def translate_axis_to_coordinate(self, size):
    try:
      x= int(input('Set X-Axis: '))
      y= int(input('Set Y-Axis: '))
      GeoTiffProcessor.get_axis_point_coordinate(self.image_types[size], x, y, {'debug': True})
    except Exception as e:
      err= read_exception_data(e)
      pretty_print(err)

  @classmethod
  def translate_axis_point_to_coordinate_small(self):
    self.translate_axis_to_coordinate('small')

  @classmethod
  def translate_axis_point_to_coordinate_medium(self):
    self.translate_axis_to_coordinate('medium')

  @classmethod
  def translate_axis_point_to_coordinate_large(self):
    self.translate_axis_to_coordinate('large')

  @classmethod
  def translate_axis_point_to_coordinate_extra_large(self):
    self.translate_axis_to_coordinate('extra_large')

  @classmethod
  def translate_polygon_axis_points_to_coordinates(self):
    try:
      points=[
        (100,100), (1100,100), (1100,1100), (100,1100)
      ]
      GeoTiffProcessor.get_polygon_axis_point_coordinates(self.image_types['medium'], points, {'debug': True})
    except Exception as e:
      err= read_exception_data(e)
      pretty_print(err)

  @classmethod
  def translate_multi_poliygon_axis_points_to_coordinates(self):
    try:
      points=[
        [(100,100), (1100,100), (1100,1100), (100,1100)],
        [(100,2000), (1100,2000), (1100,3000), (100,3000)]
      ]
      GeoTiffProcessor.get_multi_polygon_axis_point_coordinates(self.image_types['medium'], points, {'debug': True})
    except Exception as e:
      err= read_exception_data(e)
      pretty_print(err)

  @classmethod
  def get_building_geojson_from_street_map(self):
    gbd= GeoBuildingDetector({
      'show_result': False
    })
    r= gbd.get_geojson(('data/edge-detection/sample-07.png','data/edge-detection/sample-07.tif', {}))
    pretty_print('Result: ', r)
