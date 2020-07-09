import enum, os

def write_separator(total=32):
  print (''.join('-' * total))

def read_exception_data(e):
  import pprint, sys, traceback
  r={
    'message': None,
    'traceback': None
  }

  if isinstance(e, Exception):
    pprint.pprint(e)
    exc_type, exc_obj, tb = sys.exc_info()
    r['message'] = [str(x) for x in e.args]
    r['traceback'] = traceback.format_tb(tb)
  return  r

def pretty_print(data):
  import pprint
  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(data)


# Enum for size units
class SIZE_UNIT(enum.Enum):
  BYTES = 1
  KB = 2
  MB = 3
  GB = 4

def convert_unit(size_in_bytes, unit):
  """ Convert the size from bytes to other units like KB, MB or GB"""
  if unit == SIZE_UNIT.KB:
    return size_in_bytes/1024
  elif unit == SIZE_UNIT.MB:
    return size_in_bytes/(1024*1024)
  elif unit == SIZE_UNIT.GB:
    return size_in_bytes/(1024*1024*1024)
  else:
    return size_in_bytes

def get_file_size(file_name, size_type = SIZE_UNIT.BYTES ):
  """ Get file in size in given unit like KB, MB or GB"""
  size = os.path.getsize(file_name)
  return convert_unit(size, size_type)

# Additional Parser for Numpy Array
def json_np_default_parser(obj):
  if type(obj).__module__ == np.__name__:
    if isinstance(obj, np.ndarray):
      return obj.tolist()
    else:
      return obj.item()
  raise TypeError('Unknown type:', type(obj))
