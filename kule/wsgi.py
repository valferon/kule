import pymongo.errors

from .kule import Kule
import logging
import os

def make_app(*args, **kwargs):
    """create a wsgi app and loads settings from environment"""

    logging.info("%s %s", args, kwargs)
    klass = Kule
    kule = klass(
        host=os.environ.get('mongodb_host', 'localhost'),
        port=int(os.environ.get('mongodb_port', '27017')),
        database=os.environ.get('mongodb_database', 'test'),
        collections=os.environ.get('mongodb_collections', "").split(",")
    )
    app = kule.get_bottle_app()
    return app

try:
    app = make_app()
except pymongo.errors.ConnectionFailure:
    logging.exception("Can't connect to environment connections")
