def create_object_fixture(id_, name, src, item=False, finished_at=None):
    fixture = {
        'id': id_,
        'name': name,
        'src': src
    }

    if item:
        fixture['finished_at'] = finished_at

    return fixture
