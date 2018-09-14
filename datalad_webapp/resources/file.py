from flask import (
    abort,
    jsonify,
)
from flask_restful import (
    reqparse,
)
import os.path as op

from datalad_webapp import verify_authentication
from datalad_webapp.resource import WebAppResource

import logging
lgr = logging.getLogger('datalad.webapp.resources.file')


class FileResource(WebAppResource):
    # any arg is treated as a relative path
    _urlarg_spec = '<path:path>'

    def __init__(self, *args, **kwargs):
        super(FileResource, self).__init__(*args, **kwargs)
        # setup parser
        self.rp = reqparse.RequestParser()
        self.rp.add_argument(
            'path', type=str,
            help='path to file',
            location=['args', 'json', 'form'])

    @verify_authentication
    def get(self, path=None):
        args = self.rp.parse_args()
        # either use value from routing, or from request
        path = path or args.path
        if path is None:
            # no path, give list of available files
            return jsonify({
                'files': self.ds.repo.get_indexed_files(),
            })

        file_abspath = op.join(self.ds.path, path)
        if op.relpath(file_abspath, self.ds.path).startswith(op.pardir):
            # XXX not sure if this can actually happen
            # something funky is going on -> forbidden
            abort(403)
        if not op.exists(file_abspath):
            abort(404)
        if op.isdir(file_abspath):
            # -> rejected due to semantic error: dir != file
            abort(422)
        # TODO actually get the file content
        content = open(file_abspath, 'r').read()
        # TODO json_py.loads/load_stream if flag in request
        # TODO split by line if requested
        return jsonify({
            'path': path,
            'content': content,
        })

    #def post()

    #def put()

    #def delete()
