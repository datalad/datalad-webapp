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
from datalad.support import json_py
from datalad.support.constraints import (
    EnsureBool,
    EnsureChoice,
)
import logging
lgr = logging.getLogger('datalad.webapp.resources.file')


class FileResource(WebAppResource):
    # any arg is treated as a relative path
    _urlarg_spec = '<path:path>'

    def __init__(self, *args, **kwargs):
        super(FileResource, self).__init__(*args, **kwargs)
        # setup parser
        bool_type = EnsureBool()
        json_type = EnsureChoice('yes', 'no', 'stream')
        self.rp = reqparse.RequestParser()
        self.rp.add_argument(
            'path', type=str,
            help='path to file',
            location=['args', 'json', 'form'])
        self.rp.add_argument(
            'json', type=json_type,
            default='no',
            help='%s. {error_msg}' % repr(json_type),
            location=['args', 'json', 'form'])
        self.rp.add_argument(
            'verify_availability', type=bool_type,
            default='yes',
            help='%s. {error_msg}' % repr(bool_type),
            location=['args', 'json', 'form'])

    def _validate_file_path(self, path):
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
        return file_abspath

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

        file_abspath = self._validate_file_path(path)
        if not self.read_only:
            # in read only mode we cannot do this, as it might cause
            # more datasets to be install etc...
            self.ds.get(file_abspath)
        # TODO proper error reporting when loading/decoding fails
        if args.json == 'stream':
            content = list(json_py.load_stream(file_abspath))
        elif args.json == 'yes':
            content = json_py.load(file_abspath)
        else:
            content = open(file_abspath, 'r').read()

        return jsonify({
            'path': path,
            'content': content,
        })

    def put(self):
        if self.read_only:
            abort(403)

    @verify_authentication
    def delete(self, path=None):
        if self.read_only:
            abort(403)
        args = self.rp.parse_args()
        # either use value from routing, or from request
        path = path or args.path
        if path is None:
            # BadRequest
            abort(400)
        file_abspath = self._validate_file_path(path)

        return self.ds.remove(
            file_abspath,
            check=args.verify_availability,
        )
