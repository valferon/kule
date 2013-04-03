import json
from functools import partial

from bson import ObjectId
from pymongo import Connection

from helpers import int_or_default, jsonify, loads

from bottle import Bottle, route, run, request, response, abort, error


class Kule(object):
    def __init__(self, database=None, host=None, port=None,
                 collections=None):
        self.connection = self.connect(database, host, port)
        self.collections = collections

    def connect(self, database, host=None, port=None):
        return Connection(host=host, port=port)[database]

    def get_collection(self, collection):
        if self.collections and collection not in self.collections:
            abort(403)
        return self.connection[collection]

    def get_detail(self, collection, pk):
        cursor = self.get_collection(collection)
        data = cursor.find_one({"_id": ObjectId(pk)}) or abort(404)
        return jsonify(self.get_bundler(collection)(data))

    def put_detail(self, collection, pk):
        collection = self.get_collection(collection)
        collection.update({"_id": ObjectId(pk)},
                          request.json)
        return jsonify(request.json)

    def patch_detail(self, collection, pk):
        collection = self.get_collection(collection)
        collection.update({"_id": ObjectId(pk)},
                          {"$set": request.json})
        response.status = 202
        return get_document(collection, pk)

    def delete_detail(self, collection, pk):
        collection = self.get_collection(collection)
        collection.remove({"_id": ObjectId(pk)})
        response.status = 204

    def post_list(self, collection):
        collection = self.get_collection(collection)
        collection.insert(request.json)
        response.status = 201
        return jsonify({"_id": inserted})

    def get_query(self):
        query = request.GET.get("query")
        return json.loads(query) if query else {}

    def get_list(self, collection):
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

    def get_bundler(self, collection):
        return getattr(self, "build_%s_bundle" % collection.name,
                       self.build_bundle)

    def build_bundle(self, data):
        return data

    def get_error_handler(self):
        return {
            500: partial(self.error, "Internal Server Error."),
            404: partial(self.error, "Document Not Found."),
            501: partial(self.error, "Not Implemented."),
            405: partial(self.error, "Method Not Allowed."),
            403: partial(self.error, "Forbidden."),
            400: partial(self.error, "Bad request."),
        }

    def dispatch_views(self):
        for method in ("get", "post", "put", "patch", "delete"):
            self.app.route('/:collection', method=method)(
                getattr(self, "%s_list" % method, self.not_implemented))
            self.app.route('/:collection/:pk', method=method)(
                getattr(self, "%s_detail" % method, self.not_implemented))

            # magical views
            for collection in self.collections or []:
                detail_view = getattr(self, "%s_%s_detail" % (
                    method, collection), None)
                list_view = getattr(self, "%s_%s_list" % (
                    method, collection), None)
                if list_view:
                    self.app.route('/%s' % collection, method=method)(
                        list_view)
                if detail_view:
                    self.app.route('/%s/:id' % collection, method=method)(
                        detail_view)

    def get_bottle_app(self):
        self.app = Bottle()
        self.dispatch_views()
        self.app.error_handler = self.get_error_handler()
        return self.app

    def not_implemented(self, *args, **kwargs):
        abort(501)

    def error(self, message, error):
        return jsonify({"error": error.status_code,
                        "message": message})


if __name__ == "__main__":
    kule = Kule(database="selam", collections=["documents"])
    run(app=kule.get_bottle_app(), host='localhost', port=8003,
        debug=True, reloader=True)
