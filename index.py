import sys, os

from app import *

if __name__ == "__main__":
  menu= InteractiveMenu('GeoTIFF Processor', {
    'translate_axis_point_to_coordinate_small': 'Translate AXIS Point to Coordinate (Small Image)',
    'translate_axis_point_to_coordinate_medium': 'Translate AXIS Point to Coordinate (Medium Image)',
    'translate_axis_point_to_coordinate_large': 'Translate AXIS Point to Coordinate (Large Image)',
    'translate_axis_point_to_coordinate_extra_large': 'Translate AXIS Point to Coordinate (Extra Large Image)',
    'translate_polygon_axis_points_to_coordinates': 'Translate Polygon Axis Points to Coordinates (Medium Image)',
    'translate_multi_poliygon_axis_points_to_coordinates': 'Translate Multi Polygon Axis Points to Coordinates (Medium Image)'  
  })
  InteractiveMenu.show_menu()
