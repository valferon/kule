import hashlib
import uuid

from kule import Kule, jsonify, request, abort


class KuleWithAuth(Kule):

    def authenticate(self):
        collection = self.connection['users']
        username = request.json.get('username')
        password = request.json.get('password')
        hasher = hashlib.md5()
        hasher.update(password)
        user = collection.find_one({
            'username': username,
            'password': hasher.hexdigest(),
        }) or abort(400, 'Wrong username or password')
        access_token = uuid.uuid4()
        self.connection['access_tokens'].insert({
            'access_token': access_token,
            'user_id': user.get('id')})
        return jsonify({
            'access_token': access_token
        })

    def register(self):
        collection = self.connection['users']
        password = request.json.get('password')
        username = request.json.get('username')
        email = request.json.get('email')
        if not username or not password:
            abort(400, 'Please give an username and password')
        if self.collection.find_one({'username': username}):
            abort(400, 'A user with that username already exists')
        if self.collection.find_one({'email': email}):
            abort(400, 'A user with that email already exists')
        hasher = hashlib.md5()
        hasher.update(password)
        created = collection.insert({
            'username': request.json.get('username'),
            'email': request.json.get('email'),
            'password': hasher.hexdigest()
        })
        return jsonify({"_id": created})

    def dispatch_views(self):
        super(KuleWithAuth, self).dispatch_views()
        self.app.route('/authenticate', method='post')(self.authenticate)
        self.app.route('/users', method='post')(self.register)


kule = KuleWithAuth