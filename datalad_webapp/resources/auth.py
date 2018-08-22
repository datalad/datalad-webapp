from flask import session
from flask import jsonify
from datalad_webapp import (
    webapp_props,
    verify_authentication,
)
from datalad_webapp.resource import WebAppResource


class AuthenticationResource(WebAppResource):
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
