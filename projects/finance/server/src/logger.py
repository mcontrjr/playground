import logging
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(os.path.join(current_dir, '..', 'logs')):
    os.makedirs(os.path.join(current_dir, '..', 'logs'))

logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to ensure file handler can capture debug logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(current_dir, '..', 'logs', 'parser.log')),
        logging.StreamHandler()
    ]
)

log = logging.getLogger()

for handler in log.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.setLevel(logging.INFO)
    if isinstance(handler, logging.FileHandler):
        handler.setLevel(logging.DEBUG)