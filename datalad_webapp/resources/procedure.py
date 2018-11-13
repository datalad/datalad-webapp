from flask_restful import (
    fields,
    marshal_with,
    reqparse,
)
import os.path as op

# ensure bound dataset method
import datalad.interface.run_procedure

from datalad_webapp import verify_authentication
from datalad_webapp.resource import WebAppResource

import logging
lgr = logging.getLogger('datalad.webapp.resources.procedure')


class RelPath(fields.String):
    def format(self, value):
        return op.relpath(value[0], value[1])


# TODO global mapping for how to deal with datalad's result fields
resource_fields = {
    'name': fields.String(attribute=lambda x: x['procedure_name']
                          if 'procedure_name' in x else None),
    'path': RelPath(
        attribute=lambda x: (x['path'], x['refds'] if 'refds' in x else None)),
    'format': fields.String(attribute=lambda x: x['procedure_callfmt']
                            if 'procedure_callfmt' in x else None),
    'help': fields.String(attribute=lambda x: x['procedure_help']
                          if 'procedure_help' in x else None)
}


class ProcedureResource(WebAppResource):
    @verify_authentication
    @marshal_with(resource_fields, envelope='results')
    def get(self):
        return self.ds.run_procedure(discover=True)
