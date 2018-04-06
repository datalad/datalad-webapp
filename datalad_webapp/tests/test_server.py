from cherrypy.test import helper
from datalad.api import webapp


class SimpleCPTest(helper.CPWebCase):
    def setup_server():
        webapp('example_metadata', mode='dry-run')

    setup_server = staticmethod(setup_server)

    def test_server_ok(self):
        self.getPage("/")
        self.assertStatus('200 OK')
