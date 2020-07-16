import sys, os

# Init root app path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)

from app.interactive_menu import InteractiveMenu

if __name__ == "__main__":
  # GeoTIFF Processor
  menu= InteractiveMenu('Available Menu:', {
    'translate_axis_point_to_coordinate_small': 'Translate AXIS Point to Coordinate (Small Image)',
    'translate_axis_point_to_coordinate_medium': 'Translate AXIS Point to Coordinate (Medium Image)',
    'translate_axis_point_to_coordinate_large': 'Translate AXIS Point to Coordinate (Large Image)',
    'translate_axis_point_to_coordinate_extra_large': 'Translate AXIS Point to Coordinate (Extra Large Image)',
    'translate_polygon_axis_points_to_coordinates': 'Translate Polygon Axis Points to Coordinates (Medium Image)',
    'translate_multi_poliygon_axis_points_to_coordinates': 'Translate Multi Polygon Axis Points to Coordinates (Medium Image)',
    'get_building_geojson_from_street_map': 'Get Building GeoJSON From Street Map - OSM',
    'get_building_geojson_from_street_map_google': 'Get Building GeoJSON From Street Map - Google',
    'get_building_geojson_from_street_map_carto': 'Get Building GeoJSON From Street Map - Carto',
    'get_building_geojson_from_street_map_carto_gs': 'Get Building GeoJSON From Street Map - Grayscale',
    'exit':'Exit menu'
  })
  InteractiveMenu.show_menu()
