
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
    USERNAME='aaron',           # replace by the username
    PASSWORD='',
    DBHOST='localhost',
    DBPORT=5432,
    SECRET_KEY="Please generate a really long random string here",
))


LOG_FORMAT_SYSLOG = '%(name)s: %(levelname)s %(message)s'
logger = logging.getLogger(sys.argv[0])
