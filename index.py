from app import *

if __name__ == "__main__":
  menu= InteractiveMenu('GeoTIFF Processor', {
    'translate_axis_to_coordinate_small': 'Translate AXIS to Coordinate \\ Small size Image',
    'translate_axis_to_coordinate_medium': 'Translate AXIS to Coordinate \\ Medium size Image',
    'translate_axis_to_coordinate_large': 'Translate AXIS to Coordinate \\ Large size Image',
    'translate_axis_to_coordinate_extra_large': 'Translate AXIS to Coordinate \\ Extra Large size Image',
  })
  InteractiveMenu.show_menu()

