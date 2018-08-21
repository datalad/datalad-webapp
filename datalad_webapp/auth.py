from flask_restful import Resource
from flask import session
from flask import jsonify
from datalad_webapp import (
    webapp_props,
    verify_authentication,
)


class Authentication(Resource):
    def __init__(self, dataset):
        self.ds = dataset

    # TODO protect with httpauth
    def get(self):
        if 'config' not in webapp_props:
            raise ValueError('No running webapp')
        session['api_key'] = webapp_props['config']['api_key']
        return jsonify({'api_key': session['api_key']})

    @verify_authentication
    def delete(self):
        session.pop('api_key', None)
        return jsonify({
            'message': 'authentication revoked',
        })
