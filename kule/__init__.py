from functools import partial
from bson import ObjectId
from pymongo import Connection

from helpers import int_or_default, jsonify

from bottle import Bottle, route, run, request, response, abort, error


connection = Connection().dbpatterns


class Kule(object):
    def __init__(self):
        pass

    def get_document(self, collection, pk):
        cursor = connection[collection]
        return jsonify(cursor.find_one({
            "_id": ObjectId(pk)
        }) or abort(404))

    def replace_document(self, collection, pk):
        connection[collection].update({"_id": ObjectId(pk)},
                                      request.json)
        return jsonify(request.json)

    def update_document(self, collection, pk):
        connection[collection].update({"_id": ObjectId(pk)},
                                      {"$set": request.json})
        response.status = 202
        return get_document(collection, pk)

    def remove_document(self, collection, pk):
        connection[collection].remove({"_id": ObjectId(pk)})
        response.status = 204

    def post_collection(self, collection):
        inserted = connection[collection].insert(request.json)
        response.status = 201
        return jsonify({"_id": inserted})

    def get_collection(self, collection):
        limit = int_or_default(request.query.limit, 20)
        offset = int_or_default(request.query.offset, 0)
        cursor = connection[collection].find()

        meta = {
            "limit": limit,
            "offset": offset,
            "total_count": cursor.count(),
        }

        objects = cursor.skip(offset).limit(limit)

        return jsonify({"meta": meta,
                        "objects": list(objects)})

    def error(self, code, message, *args):
        return jsonify({"error": code, "message": message})

    def get_error_handler(self):
        return {
            500: partial(self.error, 500, "Internal Server Error"),
            404: partial(self.error, 404, "Not Found"),
        }

    def get_app(self):
        app = Bottle()
        app.route('/:collection/:pk', method='GET')(self.get_document)
        app.route('/:collection/:pk', method='PUT')(self.replace_document)
        app.route('/:collection/:pk', method='PATCH')(self.update_document)
        app.route('/:collection/:pk', method='DELETE')(self.remove_document)
        app.route('/:collection', method='GET')(self.get_collection)
        app.route('/:collection', method='POST')(self.post_collection)
        app.error_handler = self.get_error_handler()
        return app


if __name__ == "__main__":
    kule = Kule()
    run(app=kule.get_app(), host='localhost', port=8000,
        debug=True, reloader=True)
