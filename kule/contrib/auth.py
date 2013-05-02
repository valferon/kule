import hashlib
import uuid

from kule import Kule, jsonify, request, response, abort


class KuleWithAuth(Kule):
    """
    Adds authentication endpoints to kule
    """
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
        access_token = str(uuid.uuid4())
        self.connection['access_tokens'].insert({
            'access_token': access_token,
            'user_id': user.get('id')})
        user.pop('password')
        user.update({'access_token': access_token})
        return jsonify(user)

    def register(self):
        collection = self.connection['users']
        password = request.json.get('password')
        username = request.json.get('username')
        email = request.json.get('email')
        if not username or not password:
            abort(400, 'Please give an username and password')
        if collection.find_one({'username': username}):
            abort(400, 'A user with that username already exists')
        if collection.find_one({'email': email}):
            abort(400, 'A user with that email already exists')
        hasher = hashlib.md5()
        hasher.update(password)
        response.status = 201
        return jsonify({"_id": collection.insert({
            'username': request.json.get('username'),
            'email': request.json.get('email'),
            'password': hasher.hexdigest()
        })})

    def dispatch_views(self):
        super(KuleWithAuth, self).dispatch_views()
        self.app.route('/sessions', method='post')(self.authenticate)
        self.app.route('/sessions', method='options')(self.empty_response)
        self.app.route('/users', method='post')(self.register)
        self.app.route('/users', method='options')(self.empty_response)

kule = KuleWithAuth
