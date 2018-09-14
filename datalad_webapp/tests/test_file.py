import pytest
import flask
import json
from six.moves.urllib.parse import urlencode

from datalad.api import (
    create,
    add,
    webapp,
)

from datalad.tests.utils import (
    create_tree,
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


def test_read(client):
    client, ds = client
    with client as c:
        assert client.get('/api/v1/auth').status_code == 200
        existing_files = client.get('/api/v1/file').get_json()['files']

        file_content = '"three": 3}'
        # resource picks up live changes to the dataset
        create_tree(ds.path, {'subdir': {'dummy': file_content}})
        ds.add('.')
        current_files = client.get('/api/v1/file').get_json()['files']
        testpath = 'subdir/dummy'
        assert testpath not in existing_files
        assert testpath in current_files

        # request file content in various supported ways
        for a, kwa in (
                # plain URL routing
                (('/api/v1/file/subdir/dummy',), {}),
                # URL arg
                (('/api/v1/file?path=subdir%2Fdummy',), {}),
                # form data
                (('/api/v1/file',), {'data': {'path': testpath}}),
                (('/api/v1/file',),
                 {'data': json.dumps(dict(path=testpath)),
                  'content_type': 'application/json'}),
        ):
            rq = client.get(*a, **kwa)
            assert rq.status_code == 200
            assert rq.get_json()['path'] == testpath
            assert rq.get_json()['content'] == file_content
