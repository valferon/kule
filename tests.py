import unittest
import operator
import json
import bson

from webtest import TestApp

from kule import Kule

first = operator.itemgetter(0)


class KuleTests(unittest.TestCase):
    """
    Functionality tests for kule.
    """
    def setUp(self):
        self.kule = Kule(database="kule_test",
                         collections=["documents"])
        self.app = TestApp(self.kule.get_bottle_app())
        self.collection = self.kule.get_collection("documents")

    def tearDown(self):
        self.collection.remove()

    def test_empty_response(self):
        response = self.app.get("/documents")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json,
                         {'meta': {
                             'total_count': 0,
                             'limit': 20,
                             'offset': 0},
                          'objects': []})

    def test_get_list(self):
        self.collection.insert({"foo": "bar"})
        response = self.app.get("/documents")
        self.assertEqual(response.status_code, 200)
        objects = response.json.get("objects")
        meta = response.json.get("meta")
        self.assertEqual(1, len(objects))
        self.assertEqual(1, meta.get("total_count"))
        record = first(objects)
        self.assertEqual(record.get("foo"), "bar")

    def test_post_list(self):
        response = self.app.post("/documents", json.dumps({"foo": "bar"}),
                                 content_type="application/json")
        self.assertEqual(201, response.status_code)
        object_id = response.json.get("_id")
        query = {"_id": bson.ObjectId(object_id)}
        self.assertEqual(1, self.collection.find(query).count())
        record = self.collection.find_one(query)
        self.assertEqual(record.get("foo"), "bar")

    def test_get_detail(self):
        object_id = str(self.collection.insert({"foo": "bar"}))
        response = self.app.get("/documents/%s" % object_id)
        self.assertEqual(200, response.status_code)
        self.assertEqual(response.json, {'_id': object_id,
                                         'foo': 'bar'})

    def test_put_detail(self):
        object_id = self.collection.insert({"foo": "bar"})
        response = self.app.put("/documents/%s" % object_id,
                                json.dumps({"bar": "foo"}),
                                content_type="application/json")
        self.assertEqual(response.status_code, 202)
        record = self.collection.find_one({"_id": object_id})
        self.assertEqual(record, {'_id': object_id,
                                  'bar': 'foo'})

    def test_patch_detail(self):
        object_id = self.collection.insert({"foo": "bar"})
        response = self.app.patch("/documents/%s" % object_id,
                                  json.dumps({"bar": "foo"}),
                                  content_type="application/json")
        self.assertEqual(response.status_code, 202)
        record = self.collection.find_one({"_id": object_id})
        self.assertEqual(record, {'_id': object_id,
                                  'foo': 'bar',
                                  'bar': 'foo'})

    def test_delete_detail(self):
        object_id = self.collection.insert({"foo": "bar"})
        response = self.app.delete("/documents/%s" % object_id)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(0, self.collection.find(
            {"_id": object_id}).count())

    def test_magical_methods(self):
        class MyKule(Kule):
            def get_foo_list(self):
                return {"foo": "bar"}
        kule = MyKule(database="kule_test", collections=["foo"])
        app = TestApp(kule.get_bottle_app())
        self.assertEqual(app.get("/foo").json, {"foo": "bar"})

    def test_bundler(self):
        class MyKule(Kule):
            def build_foo_bundle(self, document):
                return {"_title": document.get("title")}
        kule = MyKule(database="kule_test", collections=["foo"])
        app = TestApp(kule.get_bottle_app())
        object_id = kule.get_collection("foo").insert({"title": "bar"})
        self.assertEqual(app.get("/foo/%s" % object_id).json, {"_title": "bar"})


unittest.main()
