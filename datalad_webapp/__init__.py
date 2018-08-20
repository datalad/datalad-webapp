# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the datalad package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""DataLad webapp support"""

__docformat__ = 'restructuredtext'

import logging
import functools

import os
from pkg_resources import iter_entry_points

from datalad.utils import assure_list
from datalad.interface.base import Interface
from datalad.interface.base import build_doc
from datalad.interface.utils import eval_results
from datalad.support.param import Parameter
from datalad.distribution.dataset import datasetmethod
from datalad.distribution.dataset import EnsureDataset
from datalad.support.constraints import EnsureNone
from datalad.support.constraints import EnsureChoice

# defines a datalad command suite
# this symbold must be indentified as a setuptools entrypoint
# to be found by datalad
command_suite = (
    # description of the command suite, displayed in cmdline help
    "Generic web app support",
    [('datalad_webapp', 'WebApp', 'webapp', 'webapp')]
)

# we want to hook into datalad's logging infrastructure, so we use a common
# prefix
lgr = logging.getLogger('datalad.extension.webapp')


# to ease config (etc.) access from other components
webapp_props = {}


def verify_authentication(view):
    from flask import session
    from flask import request
    from flask import abort

    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        api_key = webapp_props['config']['api_key']
        session_key = session.get('api_key', None)
        request_key = request.get_json()
        if request_key is not None:
            request_key = request_key.get('api_key', None)
        if session_key is None and request_key is None:
            abort(401)
        elif session_key == api_key or request_key == api_key:
            return view(*args, **kwargs)
        else:
            abort(401)

    return wrapped_view


@build_doc
class WebApp(Interface):
    """
    """
    _params_ = dict(
        dataset=Parameter(
            args=("-d", "--dataset"),
            doc="""specify the dataset to serve as the anchor of the webapp.
            An attempt is made to identify the dataset based on the current
            working directory. If a dataset is given, the command will be
            executed in the root directory of this dataset.""",
            constraints=EnsureDataset() | EnsureNone()),
        mode=Parameter(
            args=("--mode",),
            constraints=EnsureChoice('normal', 'daemon', 'dry-run'),
            doc="""Execution mode: regular foreground process (normal);
            background process (daemon); no server is started, but all
            configuration is perform (dry-run)"""),
    )

    @staticmethod
    @datasetmethod(name='webapp')
    @eval_results
    def __call__(dataset=None, mode='normal'):
        from datalad.distribution.dataset import require_dataset
        dataset = require_dataset(
            dataset, check_installed=True, purpose='serving')

        from flask import Flask
        app = Flask(__name__)
        app.secret_key = os.urandom(64)
        # expose via arg
        app.config['api_key'] = 'dummy'

        webapp_props['config'] = app.config

        from flask_restful import Api
        api = Api(app, prefix="/api/v1")

        # TODO use opt-in model for endpoints to limit exposure of
        # functionality to what is really needed
        for ep in iter_entry_points('datalad.webapp.resources'):
            lgr.warn("Available webapp resource'%s'", ep.name)
            cls = ep.load()
            api.add_resource(
                cls,
                '/{}'.format(ep.name),
                resource_class_kwargs=dict(
                    dataset=dataset,
                ),
            )

        # TODO expose flags, or use FLASK config vars
        app.run(debug=True)
