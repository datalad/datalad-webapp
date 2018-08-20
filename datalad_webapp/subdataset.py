from flask_restful import (
    Resource,
    fields,
    marshal_with,
)
import os.path as op

# ensure bound dataset method
import datalad.distribution.subdatasets

from datalad_webapp import verify_authentication


class RelPath(fields.String):
    def format(self, value):
        return op.relpath(value[0], value[1])


resource_fields = {
    'name': fields.String(attribute="gitmodule_name"),
    'path': RelPath(
        attribute=lambda x: (x['path'], x['refds'] if 'refds' in x else None)),
    'parentds': RelPath(
        attribute=lambda x: (x['parentds'], x['refds'] if 'refds' in x else None)),
    'revision': fields.String,
    'url': fields.String(attribute="gitmodule_url"),
}


class Subdataset(Resource):
    def __init__(self, dataset):
        self.ds = dataset

    @verify_authentication
    @marshal_with(resource_fields, envelope='results')
    def get(self, fulfilled=None):
        return self.ds.subdatasets(
            fulfilled=fulfilled)
