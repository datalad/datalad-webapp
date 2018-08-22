from flask_restful import (
    fields,
    marshal_with,
    reqparse,
)
import os.path as op

# ensure bound dataset method
import datalad.distribution.subdatasets

from datalad_webapp import verify_authentication
from datalad_webapp.resource import WebAppResource


class RelPath(fields.String):
    def format(self, value):
        return op.relpath(value[0], value[1])

# TODO global mapping for how to deal with datalad's result fields
resource_fields = {
    'name': fields.String(attribute="gitmodule_name"),
    'path': RelPath(
        attribute=lambda x: (x['path'], x['refds'] if 'refds' in x else None)),
    'parentds': RelPath(
        attribute=lambda x: (x['parentds'], x['refds'] if 'refds' in x else None)),
    'revision': fields.String,
    'url': fields.String(attribute="gitmodule_url"),
}


class SubdatasetResource(WebAppResource):
    @verify_authentication
    @marshal_with(resource_fields, envelope='results')
    def get(self, fulfilled=None, recursive=False):
        psr = reqparse.RequestParser()
        psr.add_argument('fulfilled', type=bool)
        psr.add_argument('recursive', type=bool)
        args = psr.parse_args()
        return self.ds.subdatasets(**args)

    # XXX could be added to change subdataset properties
    #def post()

    # XXX could be added to remove/uninstall subdatasets
    #def delete()
