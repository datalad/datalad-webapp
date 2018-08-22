import pytest
import flask

from datalad.api import (
    create,
    add,
    webapp,
)


@pytest.fixture
def client(tmpdir):
    ds = create(tmpdir.strpath)
    res = webapp(
        dataset=ds.path,
        mode='dry-run',
        return_type='item-or-list',
    )
    app = res['app']
    client = app.test_client()

    yield (client, ds)


def test_server_startup(client):
    client, ds = client
    with client as c:
        # unauthorized access is prevented
        rv = client.get('/api/v1/file')
        assert rv.status_code == 401
        assert 'results' not in rv.get_json()
        # we get no magic authentication
        assert 'api_key' not in flask.session

        # authenticate
        rv = client.get('/api/v1/auth')
        assert rv.status_code == 200

        # request list of files
        rv = client.get('/api/v1/file')
        assert rv.status_code == 200
        assert {'files': ds.repo.get_indexed_files()} == rv.get_json()
