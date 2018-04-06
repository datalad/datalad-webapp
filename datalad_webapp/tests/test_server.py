from cherrypy.test import helper
from datalad.api import create
from datalad.api import webapp
from datalad.tests.utils import with_tempfile


class SimpleCPTest(helper.CPWebCase):
    @with_tempfile
    def setup_server(path):
        ds = create(path)
        webapp(
            'example_metadata',
            dataset=ds.path,
            mode='dry-run',
            hostsecret='dataladtest')

    setup_server = staticmethod(setup_server)

    def test_server_ok(self):
        # by default the beast is locked
        self.getPage("/")
        self.assertStatus('401 Unauthorized')
        # unlock by visiting / with the correct secret
        self.getPage("/?datalad_host_secret=dataladtest")
        self.assertStatus('200 OK')
