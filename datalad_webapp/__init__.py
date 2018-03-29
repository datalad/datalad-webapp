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

from os.path import dirname
from os.path import basename
from os.path import isdir
from os.path import join as opj

from glob import glob

from datalad import cfg
from pkg_resources import iter_entry_points

from datalad.dochelpers import exc_str
from datalad.utils import assure_list
from datalad.interface.base import Interface
from datalad.interface.base import build_doc
from datalad.support.param import Parameter
from datalad.distribution.dataset import datasetmethod
from datalad.interface.utils import eval_results
from datalad.support.constraints import EnsureNone
from datalad.distribution.dataset import EnsureDataset

# defines a datalad command suite
# this symbold must be indentified as a setuptools entrypoint
# to be found by datalad
module_suite = (
    # description of the command suite, displayed in cmdline help
    "Generic web app support",
    [('datalad_webapp', 'WebApp', 'webapp', 'webapp')]
)

# we want to hook into datalad's logging infrastructure, so we use a common
# prefix
lgr = logging.getLogger('datalad.module.webapp')


@build_doc
class WebApp(Interface):
    """
    """
    _params_ = dict(
        app=Parameter(
            args=('--app',),
            doc="yeah!",
            nargs='+',
            action='append'),
        dataset=Parameter(
            args=("-d", "--dataset"),
            doc="""specify the dataset to serve as the anchor of the webapp.
            An attempt is made to identify the dataset based on the current
            working directory. If a dataset is given, the command will be
            executed in the root directory of this dataset.""",
            constraints=EnsureDataset() | EnsureNone()),
        daemonize=Parameter(
            args=("--daemonize",),
            action='store_true',
            doc="yeah!"),
    )

    @staticmethod
    @datasetmethod(name='webapp')
    @eval_results
    def __call__(app, dataset=None, daemonize=False):
        apps = assure_list(app)
        if not apps:
            raise ValueError('no app specification given')
        if not isinstance(apps[0], (list, tuple)):
            apps = [apps]
        apps = {a[0] if isinstance(a, (list, tuple)) else a:
                a[1] if isinstance(a, (list, tuple)) and len(a) > 1 else None
                for a in apps}

        import cherrypy

        # global config
        cherrypy.config.update({
            # prevent visible tracebacks, etc:
            # http://docs.cherrypy.org/en/latest/config.html#id14
            #'environment': 'production',
            #'log.error_file': 'site.log',
        })

        # set the priority according to your needs if you are hooking something
        # else on the 'before_finalize' hook point.
        @cherrypy.tools.register('before_finalize', priority=60)
        def secureheaders():
            headers = cherrypy.response.headers
            headers['X-Frame-Options'] = 'DENY'
            headers['X-XSS-Protection'] = '1; mode=block'
            headers['Content-Security-Policy'] = "default-src='self'"
            # only add Strict-Transport headers if we're actually using SSL; see the ietf spec
            # "An HSTS Host MUST NOT include the STS header field in HTTP responses
            # conveyed over non-secure transport"
            # http://tools.ietf.org/html/draft-ietf-websec-strict-transport-sec-14#section-7.2
            if (cherrypy.server.ssl_certificate != None and
                    cherrypy.server.ssl_private_key != None):
                headers['Strict-Transport-Security'] = 'max-age=31536000'  # one year

        if daemonize:
            from cherrypy.process.plugins import Daemonizer
            Daemonizer(cherrypy.engine).subscribe()
            #PIDFile(cherrypy.engine, '/var/run/myapp.pid').subscribe()

        # when running on a priviledged port
        #DropPrivileges(cherrypy.engine, uid=1000, gid=1000).subscribe()

        enabled_apps = []
        for ep in iter_entry_points('datalad.webapps'):
            if ep.name not in apps:
                continue
            mount = apps[ep.name] if apps[ep.name] else '/'
            # get the webapp class
            cls = ep.load()
            # fire up the webapp instance
            inst = cls(**dict(dataset=dataset))
            # mount under global URL tree (default or given suburl)
            app = cherrypy.tree.mount(
                root=inst,
                script_name=mount,
                # app config file, it is ok for that file to not exist
                config=cls._webapp_config
            )
            # forcefully impose more secure mode
            # TODO might need one (or more) switch(es) to turn things off for
            # particular scenarios
            enabled_apps.append(ep.name)
            app.merge({
                '/': {
                    # turns all security headers on
                    'tools.secureheaders.on': True,
                    'tools.sessions.secure': True,
                    'tools.sessions.httponly': True}})
            static_dir = opj(cls._webapp_dir, cls._webapp_staticdir)
            if isdir(static_dir):
                app.merge({
                    # the key has to be / even when an app is mount somewhere
                    # below
                    '/': {
                        'tools.staticdir.on': True,
                        'tools.staticdir.root': cls._webapp_dir,
                        'tools.staticdir.dir': cls._webapp_staticdir}}
                )
        failed_apps = set(apps).difference(enabled_apps)
        if failed_apps:
            lgr.warning('Failed to load webapps: %s', failed_apps)
        if not enabled_apps:
            return
        cherrypy.engine.start()
        cherrypy.engine.block()
        yield {}
