import json
import datetime

import bson


def int_or_default(value, default=None):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class MongoEncoder(json.JSONEncoder):
    """
    Custom encoder for dumping MongoDB documents
    """
    def default(self, obj):

        if isinstance(obj, bson.ObjectId):
            return str(obj)

        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()

        return super(MongoEncoder, self).default(obj)


jsonify = MongoEncoder().encode
