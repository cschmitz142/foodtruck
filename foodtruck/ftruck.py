import os
from flask import Flask, Response, request, current_app, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp
from datetime import datetime
import logging
import logging.config
import json
from foodtruck.database import Session
import functions

LOG_FILE = os.environ['FOODTRUCK_API_LOG_INI']
logging.config.fileConfig(LOG_FILE, disable_existing_loggers=False)
logger = logging.getLogger()


def authenticate(uid, pw):
    logger.debug('checking uid: %s, pw: %s' % (uid, pw))
    user = functions.auth(uid, pw)
    logger.debug(user)
    if user != -1:
        return user
    return -1


def identity(payload):
    uid = payload['identity']
    logger.debug('payload: %s' % (uid))
    return {'user_id': functions.get_user(uid).uid}


app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret'
app.config['JWT_AUTH_USERNAME_KEY'] = 'uid'
app.config['JWT_AUTH_PASSWORD_KEY'] = 'pw'
jwt = JWT(app, authenticate, identity)


@jwt.jwt_payload_handler
def make_payload(identity):
    iat = datetime.utcnow()
    exp = iat + current_app.config.get('JWT_EXPIRATION_DELTA')
    nbf = iat + current_app.config.get('JWT_NOT_BEFORE_DELTA')
    identity = getattr(identity, 'uid') or identity['uid']
    return {'exp': exp, 'iat': iat, 'nbf': nbf, 'identity': identity}


@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()


@app.route('/protected')
@jwt_required()
def index():
    logger.info("[%s] - %s" % (request.method, request.path))
    return Response(json.dumps(dict(current_identity)))


@app.route('/trucks', methods=['GET'])
def all_trucks():
    logger.info("[%s] - %s" % (request.method, request.path))
    return Response(functions.all_trucks())


@app.route('/locations', methods=['GET'])
def all_locations():
    logger.info("[%s] - %s" % (request.method, request.path))
    return Response(functions.all_locations())


@app.route('/users', methods=['GET'])
def all_users():
    logger.info("[%s] - %s" % (request.method, request.path))
    return Response(functions.all_users())


@app.after_request
def after_request(response):
    response.headers['Content-Type'] = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


if __name__ == '__main__':
    app.run(debug=False)