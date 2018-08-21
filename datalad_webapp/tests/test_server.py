import pytest
import flask

from datalad.api import create
from datalad.api import webapp
from datalad.tests.utils import with_tempfile


@pytest.fixture
def client(tmpdir):
    ds = create(tmpdir.strpath)
    res = webapp(
        #'example_metadata',
        dataset=ds.path,
        mode='dry-run',
        return_type='item-or-list',
    )
    app = res['app']

    client = app.test_client()

    yield client


def test_server_startup(client):
    with client as c:
        # unauthorized access is prevented
        rv = client.get('/api/v1/subdataset')
        assert rv.status_code == 401
        assert 'results' not in rv.get_json()
        # we get no magic authentication
        assert 'api_key' not in flask.session

        # authenticate
        rv = client.get('/api/v1/auth')
        assert rv.status_code == 200
        assert {'api_key': 'dummy'} == rv.get_json()
        assert 'api_key' in flask.session

        # authenticated request, yields empty list (no subdatasets here)
        rv = client.get('/api/v1/subdataset')
        assert rv.status_code == 200
        assert {'results': []} == rv.get_json()
