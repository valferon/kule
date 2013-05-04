import json
from functools import partial

from bson import ObjectId
from pymongo import Connection

from helpers import int_or_default, jsonify

from bottle import Bottle, route, run, request, response, abort, error


class Kule(object):
    """Wraps bottle app."""

    def __init__(self, database=None, host=None, port=None,
                 collections=None):
        self.connection = self.connect(database, host, port)
        self.collections = collections

    def connect(self, database, host=None, port=None):
        """Connects to the MongoDB"""
        return Connection(host=host, port=port)[database]

    def get_collection(self, collection):
        """Returns the given collection if it permitted"""
        if self.collections and collection not in self.collections:
            abort(403)
        return self.connection[collection]

    def get_detail(self, collection, pk):
        """Returns a single document."""
        cursor = self.get_collection(collection)
        data = cursor.find_one({"_id": ObjectId(pk)}) or abort(404)
        return jsonify(self.get_bundler(cursor)(data))

    def put_detail(self, collection, pk):
        """Updates whole document."""
        collection = self.get_collection(collection)
        if '_id' in request.json:
            # we are ignoring id fields of bundle,
            # because _id field is immutable
            del request.json['_id']
        collection.update({"_id": ObjectId(pk)}, request.json)
        response.status = 202
        return jsonify(request.json)

    def patch_detail(self, collection, pk):
        """Updates specific parts of the document."""
        collection = self.get_collection(collection)
        collection.update({"_id": ObjectId(pk)},
                          {"$set": request.json})
        response.status = 202
        return self.get_detail(collection.name, str(pk))

    def delete_detail(self, collection, pk):
        """Deletes a single document"""
        collection = self.get_collection(collection)
        collection.remove({"_id": ObjectId(pk)})
        response.status = 204

    def post_list(self, collection):
        """Creates new document"""
        collection = self.get_collection(collection)
        inserted = collection.insert(request.json)
        response.status = 201
        return jsonify({"_id": inserted})

    def get_list(self, collection):
        """Returns paginated objects."""
        collection = self.get_collection(collection)
        limit = int_or_default(request.query.limit, 20)
        offset = int_or_default(request.query.offset, 0)
        query = self.get_query()
        cursor = collection.find(query)

        meta = {
            "limit": limit,
            "offset": offset,
            "total_count": cursor.count(),
        }

        objects = cursor.skip(offset).limit(limit)
        objects = map(self.get_bundler(collection), objects)

        return jsonify({"meta": meta,
                        "objects": objects})

    def get_query(self):
        """Loads the given json-encoded query."""
        query = request.GET.get("query")
        return json.loads(query) if query else {}

    def get_bundler(self, collection):
        """Returns a bundler function for collection"""
        method_name = "build_%s_bundle" % collection.name
        return getattr(self, method_name, self.build_bundle)

    def build_bundle(self, data):
        """Dummy bundler"""
        return data

    def empty_response(self, *args, **kwargs):
        """Empty response"""

    # we are returning an empty response for OPTIONS method
    # it's required for enabling CORS.
    options_list = empty_response
    options_detail = empty_response

    def get_error_handler(self):
        """Customized errors"""
        return {
            500: partial(self.error, message="Internal Server Error."),
            404: partial(self.error, message="Document Not Found."),
            501: partial(self.error, message="Not Implemented."),
            405: partial(self.error, message="Method Not Allowed."),
            403: partial(self.error, message="Forbidden."),
            400: self.error,
        }

    def dispatch_views(self):
        """Routes bottle app. Also determines the magical views."""
        for method in ("get", "post", "put", "patch", "delete", "options"):
            self.app.route('/:collection', method=method)(
                getattr(self, "%s_list" % method, self.not_implemented))
            self.app.route('/:collection/:pk', method=method)(
                getattr(self, "%s_detail" % method, self.not_implemented))

            # magical views
            for collection in self.collections or []:
                list_view = getattr(self, "%s_%s_list" % (
                    method, collection), None)
                detail_view = getattr(self, "%s_%s_detail" % (
                    method, collection), None)
                if list_view:
                    self.app.route('/%s' % collection, method=method)(
                        list_view)
                if detail_view:
                    self.app.route('/%s/:id' % collection, method=method)(
                        detail_view)

    def after_request(self):
        """A bottle hook for json responses."""
        response["content_type"] = "application/json"
        methods = 'PUT, PATCH, GET, POST, DELETE, OPTIONS'
        headers = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = methods
        response.headers['Access-Control-Allow-Headers'] = headers

    def get_bottle_app(self):
        """Returns bottle instance"""
        self.app = Bottle()
        self.dispatch_views()
        self.app.hook('after_request')(self.after_request)
        self.app.error_handler = self.get_error_handler()
        return self.app

    def not_implemented(self, *args, **kwargs):
        """Returns not implemented status."""
        abort(501)

    def error(self, error, message=None):
        """Returns the error response."""
        return jsonify({"error": error.status_code,
                        "message": error.body or message})

    def run(self, *args, **kwargs):
        """Shortcut method for running kule"""
        kwargs.setdefault("app", self.get_bottle_app())
        run(*args, **kwargs)


def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("--bind", dest="address",
                      help="Binds an address to kule")
    parser.add_option("--mongodb-host", dest="mongodb_host",
                      help="MongoDB host")
    parser.add_option("--mongodb-port", dest="mongodb_port",
                      help="MongoDB port")
    parser.add_option("-d", "--database", dest="database",
                      help="MongoDB database name")
    parser.add_option("-c", "--collections", dest="collections",
                      help="Comma-separated collections.")
    parser.add_option("-k", "--klass", dest="klass",
                      help="Kule class")
    options, args = parser.parse_args()
    collections = (options.collections or "").split(",")
    database = options.database
    if not database:
        parser.error("MongoDB database not given.")
    host, port = (options.address or 'localhost'), 8000
    if ':' in host:
        host, port = host.rsplit(':', 1)

    try:
        klass = __import__(options.klass, fromlist=['kule']).kule
    except AttributeError:
        raise ImportError('Bad kule module.')
    except TypeError:
        klass = Kule

    kule = klass(
        host=options.mongodb_host,
        port=options.mongodb_port,
        database=options.database,
        collections=collections
    )
    run(host=host, port=port, app=kule.get_bottle_app())

if __name__ == "__main__":
    main()
