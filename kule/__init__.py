from functools import partial
from bson import ObjectId
from pymongo import Connection

from helpers import int_or_default, jsonify

from bottle import Bottle, route, run, request, response, abort, error


connection = Connection().dbpatterns

kule = Bottle()


@kule.route('/:collection/:pk', method='GET')
def get_document(collection, pk):
    cursor = connection[collection]
    return jsonify(cursor.find_one({
        "_id": ObjectId(pk)
    }) or abort(404))


@kule.route('/:collection/:pk', method='PUT')
def replace_document(collection, pk):
    connection[collection].update({"_id": ObjectId(pk)},
                                  request.json)
    return jsonify(request.json)


@kule.route('/:collection/:pk', method='PATCH')
def update_document(collection, pk):
    connection[collection].update({"_id": ObjectId(pk)},
                                  {"$set": request.json})
    response.status = 202
    return get_document(collection, pk)


@kule.route('/:collection/:pk', method='DELETE')
def get_document(collection, pk):
    connection[collection].remove({"_id": ObjectId(pk)})
    response.status = 204


@kule.route('/:collection', method='GET')
def get_collection(collection):
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


@kule.route('/:collection', method='POST')
def post_collection(collection):
    inserted = connection[collection].insert(request.json)
    response.status = 201
    return jsonify({"_id": inserted})


def error(code, message, *args):
    return jsonify({"error": code, "message": message})


kule.error_handler = {
    500: partial(error, 500, "Internal Server Error"),
    404: partial(error, 404, "Not Found"),
}

if __name__ == "__main__":
    run(app=kule, host='localhost', port=8000, debug=True, reloader=True)
