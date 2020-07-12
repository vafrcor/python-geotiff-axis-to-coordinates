import logging, json, configparser, os, sys
import logging.handlers

# from pythonjsonlogger import jsonlogger
from logstash_formatter import LogstashFormatterV1

# from .geotiff import *
# from .interactive_menu import *
# from .shape_detector import *

# Init root app path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.insert(0,BASE_DIR)

# Config 
config_filepath= os.path.join(BASE_DIR, 'config.ini')
config_strings= None
with open(config_filepath, 'r') as cfg_file:
  config_strings = cfg_file.read()

config = configparser.ConfigParser()
config.read_string(config_strings)

# Logger
logger = logging.getLogger()
log_handlers = [
  logging.handlers.RotatingFileHandler(
    "%s/%s" % (BASE_DIR, config['path']['logs']+config['application']['name']+'-log.json'),
    encoding= 'utf8',
    maxBytes= 500000,
    backupCount= 5
  ),
  logging.StreamHandler()
]
fmt = {
  'extra': {
    'type': 'spartech-geodata'
  }
}
jfmt = json.dumps(fmt)
logsts_formatter = LogstashFormatterV1(
  fmt=jfmt,
  datefmt="%Y-%m-%d %H:%M:%S"
)

if config['logging']['debug'] == 'true':
  logger.setLevel(logging.DEBUG)

for h in log_handlers:
  h.setFormatter(logsts_formatter)
  logger.addHandler(h)

# logger.info('Config: ', {'config': config['test']['foo']})
# logger.warning('Config: ', {'config': config['test']['foo']})
# logger.error('Config: ', {'config': config['test']['foo']})
# logger.debug('Config: ', {'config': config['test']['foo']})

# __all__ = ["config","logger","InteractiveMenu","BASE_DIR"]
