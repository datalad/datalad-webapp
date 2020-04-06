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

__version__ = '0.3'

import logging
import functools

import os
import os.path as op
from pkg_resources import (
    iter_entry_points,
    resource_isdir,
    resource_filename,
)

from datalad.interface.base import Interface
from datalad.interface.base import build_doc
from datalad.interface.utils import eval_results
from datalad.support.param import Parameter
from datalad.distribution.dataset import datasetmethod
from datalad.distribution.dataset import EnsureDataset
from datalad.support.constraints import (
    EnsureNone,
    EnsureChoice,
    EnsureBool
)

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
        app=Parameter(
            args=('app',),
            nargs='?',
            metavar='APPNAME',
            doc="""Name of a registered webapp to start"""),
        dataset=Parameter(
            args=("-d", "--dataset"),
            doc="""specify the dataset to serve as the anchor of the webapp.
            An attempt is made to identify the dataset based on the current
            working directory. If a dataset is given, the command will be
            executed in the root directory of this dataset.""",
            constraints=EnsureDataset() | EnsureNone()),
        read_only=Parameter(
            args=("--read-only",),
            constraints=EnsureBool(),
            doc="""do not perform operations other then read-only access
            to dataset. It is up to the individual resources to interpret
            this flag and act accordingly."""),
        mode=Parameter(
            args=("--mode",),
            constraints=EnsureChoice('normal', 'daemon', 'dry-run', 'debug'),
            doc="""Execution mode: regular foreground process (normal);
            background process (daemon); no server is started, but all
            configuration is perform (dry-run); like normal, but in debug
            mode (debug)"""),
        static_root=Parameter(
            args=("--static-root",),
            doc="""path to static (HTML) files that should be served in
            root of the webapp. Defaults to the current directory."""),
        get_apps=Parameter(
            args=('--get-apps',),
            action='store_true',
            doc="""if set, yields all registered webapp."""),
    )

    @staticmethod
    @datasetmethod(name='webapp')
    @eval_results
    def __call__(app=None, dataset=None, read_only=False, mode='normal',
                 static_root=None, get_apps=False):
        if get_apps:
            for ep in iter_entry_points('datalad.webapp.apps'):
                yield dict(
                    action='webapp',
                    status='ok'
                    if resource_isdir(ep.module_name, ep.load()) else 'error',
                    path=ep.name,
                    logger=lgr,
                    message=("provided by '%s'", ep.module_name))
            return

        from datalad.distribution.dataset import require_dataset
        dataset = require_dataset(
            dataset, check_installed=True, purpose='serving')

        if static_root is None and app:
            for ep in iter_entry_points('datalad.webapp.apps'):
                if ep.name == app:
                    app_path = resource_filename(ep.module_name, ep.load())
                    if not resource_isdir(ep.module_name, ep.load()):
                        yield dict(
                            action='webapp',
                            status='error',
                            path=dataset.path,
                            message=(
                                "app entrypoint '%s' does not point to directory",
                                app, app_path)
                        )
                        return
                    static_root = app_path
                    break
            if static_root is None:
                yield dict(
                    action='webapp',
                    status='error',
                    path=dataset.path,
                    message=(
                        "no registered webapp with name '%s'",
                        app)
                )
                return
        elif static_root is None:
            static_root = op.curdir

        from flask import Flask
        app = Flask(
            __name__,
            root_path=dataset.path,
            static_url_path='',
            static_folder=op.abspath(static_root),
        )
        app.secret_key = os.urandom(64)
        # expose via arg
        app.config['api_key'] = 'dummy'

        webapp_props['config'] = app.config

        from flask_restful import Api
        api = Api(app, prefix="/api/v1")

        # TODO add default route to static index.html, if one exists
        # TODO use opt-in model for endpoints to limit exposure of
        # functionality to what is really needed
        for ep in iter_entry_points('datalad.webapp.resources'):
            lgr.warn("Available webapp resource'%s'", ep.name)
            cls = ep.load()
            urls = ['/{}'.format(ep.name)]
            if hasattr(cls, '_urlarg_spec'):
                urls.append('/{}/{}'.format(ep.name, cls._urlarg_spec))

            api.add_resource(
                cls,
                *urls,
                resource_class_kwargs=dict(
                    dataset=dataset,
                )
            )

        if op.exists(op.join(static_root, 'index.html')):
            from flask import send_from_directory

            @app.route('/')
            def serve_index():
                return send_from_directory(
                    static_root, 'index.html')

        if mode == 'dry-run':
            yield dict(
                action='webapp',
                status='ok',
                app=app,
                path=dataset.path,
            )
            return

        print("""
*************************************************
*************************************************

      THIS IS NOT A PRODUCTION-READY TOOL

      - only use in a trusted environment
      - do not expose service on public
        network interfaces

*************************************************
*************************************************
""")
        # TODO expose flags, or use FLASK config vars
        app.run(debug=mode == 'debug')
