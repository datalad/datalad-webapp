import flask


def assert_get_resource_needs_authentication(client, res):
    # unauthorized access is prevented
    rv = client.get('/api/v1/' + res)
    assert rv.status_code == 401
    assert 'results' not in rv.get_json()
    # we get no magic authentication
    assert 'api_key' not in flask.session

    # authenticate
    rv = client.get('/api/v1/auth')
    assert rv.status_code == 200

    # request list of files
    rv = client.get('/api/v1/' + res)
    assert rv.status_code == 200
