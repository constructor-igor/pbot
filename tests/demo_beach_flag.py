import os, sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from IsraelMetrologyService import IsraelMetrologyService

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    ims = IsraelMetrologyService()
    ims.dwoanload_data()
    ims.parse_data()
    ims.to_log()