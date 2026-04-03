import datetime
from uuid import uuid4

import pytest


def test_serialize(project_with_fdb):
    project = project_with_fdb
    ret = project.serialize()
    assert ret['id'] == project.id
    assert ret['attributes'] == {}
    assert ret['created_by'] == project.created_by
    assert ret['date_created'] == project.date_created
    assert ret['description'] == project.description
    assert ret['display_type_plural'] == project.DISPLAY_TYPE_PLURAL
    assert ret['display_type_singular'] == project.DISPLAY_TYPE_SINGULAR
    assert ret['locked'] == project.is_user_locked
    assert ret['name'] == project.name
    assert ret['organizations'] == []
    assert ret['public'] == project.public
    assert ret['slug'] == project.SLUG
    assert ret['status'] is None
    assert ret['type'] == project.type
    assert ret['datasets'] == project.datasets
    assert ret['scenarios'] == project.scenarios


def test_json_dumps(project):
    some_uuid = uuid4()
    some_datetime = datetime.datetime.now()
    test_dict = {
        'id': some_uuid,
        'datetime': some_datetime,
    }
    ret = project.json_dumps(test_dict)
    assert ret == f'{{"id": "{str(some_uuid)}", "datetime": "{some_datetime.isoformat()}"}}'


def test_json_dumps_unserializable_value(project):
    class Unserializable:
        pass

    not_serializable = Unserializable()

    test_dict = {
        'foo': not_serializable,
    }

    with pytest.raises(TypeError):
        project.json_dumps(test_dict)
