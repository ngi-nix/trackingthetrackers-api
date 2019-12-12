
"""
Config file
"""

import sys
import logging

config = dict()
config.update(dict(
    version=0.1,
    debug=True,
    DATABASE='bincache',
    USERNAME='bincache',           # replace by the username
    PASSWORD='',
    DBHOST='localhost',
    DBPORT=5432,
    SECRET_KEY="Please generate a really long random string here",
    UPLOAD_PATH="/tmp",            # Change to the upload path where files should be stored
))


LOG_FORMAT_SYSLOG = '%(name)s: %(levelname)s %(message)s'
logger = logging.getLogger(sys.argv[0])
