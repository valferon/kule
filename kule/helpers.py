import json
import datetime
import io
import csv

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


def flatten(rows):
    """
    Flatten a json structure with nested dictionaries to a flat structure

    >>> rows = [{'a': 2}, {'b': 3, 'c': {'a':1}}]
    >>> list(flatten(rows))
    [{'a': 2}, {'b': 3, 'c.a': 1}]
    """
    for item in rows:
        row = {}
        for key, value in key_values(item):
            row[key] = value
        yield row

def key_values(row):
    """
    convert a row with a nested format to key_values

    >>> dict(key_values({'a': 2, 'b': {'a': 1, 'b': 3}}))
    {'a': 2, 'b.b': 3, 'b.a': 1}
    """
    if isinstance(row, dict):
        for key, value in row.items():
            if isinstance(value, dict):
                for key_, value_ in key_values(value):
                    yield key + "." + key_, value_
            else:
                yield key, value


def csvify(rows):
    r"""
    Custom encoder for dumping MongoDB to csv

    >>> rows = [{'a': 2}, {'b': 3, 'c': {'a':1}}]
    >>> csvify(rows)
    'a,b,c.a\r\n2,,\r\n,3,1\r\n'

    >>> rows = {'meta': 'blah', 'objects': [{'a': 1}, {'b': 2}]}
    >>> csvify(rows)
    'a,b\r\n1,\r\n,2\r\n'

    """
    # csv module in python does not support unicode input so we're using bytes.
    # https://docs.python.org/2.7/library/csv.html#module-csv
    stream = io.BytesIO()
    if 'objects' in rows:
        rows = rows['objects']
    rows = list(flatten(rows))

    # lookup unique keys
    keys = set()
    for row in rows:
        keys.update(row.keys())

    writer = csv.DictWriter(stream, fieldnames=list(keys))
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return stream.getvalue()

jsonify = MongoEncoder().encode


if __name__ == '__main__':
    import doctest
    doctest.testmod()
