from os.path import dirname
from os.path import join as opj


class MetadataAppExample(object):
    import cherrypy
    from cherrypy import tools

    _webapp_dir = dirname(__file__)
    _webapp_staticdir = 'static'
    _webapp_config = opj(_webapp_dir, 'app.conf')

    def __init__(self, dataset):
        from datalad.distribution.dataset import require_dataset
        self.ds = require_dataset(
            dataset, check_installed=True, purpose='serving')

    @cherrypy.expose
    def index(self):
        return """<html>
          <head></head>
          <body>
            <form method="get" action="m">
              <input type="text" placeholder="relative path" name="path" />
              <button type="submit">Give me metadata!</button>
            </form>
          </body>
        </html>"""

    @cherrypy.expose
    @tools.json_out()
    def m(self, path):
        from datalad.api import metadata
        return metadata(path, dataset=self.ds, result_renderer='disabled')

    @tools.json_out()
    @cherrypy.expose
    def config(self):
        import cherrypy
        return cherrypy.request.app.config
