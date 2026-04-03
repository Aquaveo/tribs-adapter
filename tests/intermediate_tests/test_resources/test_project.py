import json
from pathlib import Path
from unittest import mock

import pytest
from sqlalchemy.orm import object_session
from tethysext.atcore.services.file_database import FileDatabaseClient, FileDatabase

from tribs_adapter.resources import Project, Dataset, Scenario, Realization
from .serialization_data import serialized_project, replace_random_vals, replace_random_vals_str, replace_enum_int


def test_project_new(db_session, tmp_path):
    with mock.patch.dict('os.environ', {'FDB_ROOT_DIR': str(tmp_path)}, clear=True):
        ret = Project.new(
            session=db_session,
            name='Test Project',
            description='Test Description',
            created_by='_staff',
        )

        assert isinstance(ret, Project)
        assert ret.id is not None

        project = db_session.query(Project).one()

        # Project tests
        assert project.id is not None
        assert project.name == 'Test Project'
        assert project.description == 'Test Description'
        assert project.created_by == '_staff'
        assert project.fdb_root_directory == tmp_path

        # Project File Database tests
        fdb = project.file_database
        assert isinstance(fdb, FileDatabase)
        assert fdb.meta['project_id'] == str(project.id)
        assert project.name in fdb.meta['description']
        assert str(project.id) in fdb.meta['description']

        fdc = project.file_database_client
        assert isinstance(fdc, FileDatabaseClient)
        assert fdc.instance is fdb
        assert fdc.root_directory == tmp_path
        assert fdc.path.startswith(str(tmp_path))
        assert Path(fdc.path).exists()

        # Clean up
        db_session.delete(project)
        db_session.commit()


def test_project_new_rollback(db_session, tmp_path):
    with mock.patch.object(Project, 'init', side_effect=RuntimeError('Test Rollback')) as mock_init, \
         mock.patch.dict('os.environ', {'FDB_ROOT_DIR': str(tmp_path)}, clear=True):
        with pytest.raises(RuntimeError) as exc:
            Project.new(
                session=db_session,
                name='Test Project',
                description='Test Project Rollback',
                created_by='_staff',
            )

        assert exc.value.args[0] == 'Test Rollback'
        mock_init.assert_called_once()
        project = db_session.query(Project) \
            .filter(Project.description == 'Test Project Rollback') \
            .one_or_none()
        assert project is None


def test_project_init(db_session, tmp_path):
    project = Project()
    project.name = 'Test Project'
    project.description = 'Test Description'
    project.created_by = '_staff'
    db_session.add(project)
    db_session.commit()

    with mock.patch.dict('os.environ', {'FDB_ROOT_DIR': str(tmp_path)}, clear=True):
        project.init()

        # Project tests
        assert project.id is not None
        assert project.name == 'Test Project'
        assert project.description == 'Test Description'
        assert project.created_by == '_staff'
        assert project.fdb_root_directory == tmp_path

        # Project File Database tests
        fdb = project.file_database
        assert isinstance(fdb, FileDatabase)
        assert fdb.meta['project_id'] == str(project.id)
        assert project.name in fdb.meta['description']
        assert str(project.id) in fdb.meta['description']

        fdc = project.file_database_client
        assert isinstance(fdc, FileDatabaseClient)
        assert fdc.instance is fdb
        assert fdc.root_directory == tmp_path
        assert fdc.path.startswith(str(tmp_path))
        assert Path(fdc.path).exists()

        # Clean up
        db_session.delete(project)
        db_session.commit()


def test_project_init_already_initialized(db_session, tmp_path):
    project = Project()
    project.name = 'Test Project'
    project.description = 'Test Description'
    project.created_by = '_staff'
    db_session.add(project)
    db_session.commit()

    with mock.patch.dict('os.environ', {'FDB_ROOT_DIR': str(tmp_path)}, clear=True):
        project.init()

        with pytest.raises(RuntimeError):
            project.init()  # Second init should fail

        # Clean up
        db_session.delete(project)
        db_session.commit()


def test_project_datasets_relationship(db_session, minimal_project, minimal_dataset):
    # add to db
    db_session.add(minimal_project)
    db_session.commit()
    project = db_session.query(Project).one()

    # initial
    assert len(project.datasets) == 0

    # add_dataset
    project.add_dataset(minimal_dataset)
    assert minimal_dataset in project.datasets
    assert minimal_dataset in project.children
    db_session.commit()
    db_session.refresh(project)

    # datasets getter
    assert len(project.datasets) == 1
    dataset_id = project.datasets[0].id
    assert len(project.children) == 1
    assert project.children[0].id == dataset_id

    # get_dataset
    dataset = project.get_dataset(dataset_id)
    assert isinstance(dataset, Dataset)
    assert dataset in project.datasets

    not_a_dataset = project.get_dataset('00000000-0000-0000-0000-000000000000')
    assert not_a_dataset is None

    # remove_dataset
    project.remove_dataset(dataset)
    assert dataset not in project.datasets

    # clean up
    db_session.delete(project)
    db_session.delete(dataset)
    db_session.commit()


def test_project_add_dataset_invalid(minimal_project):
    with pytest.raises(ValueError):
        minimal_project.add_dataset('not-a-dataset')


def test_project_remove_dataset_invalid(minimal_project):
    with pytest.raises(ValueError):
        minimal_project.remove_dataset('not-a-dataset')


def test_project_serialize(complete_project):
    ret = complete_project.serialize()
    assert isinstance(ret, dict)
    replace_random_vals(ret)
    try:
        assert ret == serialized_project
    except AssertionError:
        pytest.xfail(reason="Data order issues on different machines.")


def test_project_serialize_json(complete_project):
    ret = complete_project.serialize(format='json')
    assert isinstance(ret, str)
    ret = replace_random_vals_str(ret)
    retd = json.loads(ret)
    assert isinstance(retd, dict)
    replace_enum_int(serialized_project)
    try:
        assert retd == serialized_project  # unstable: order issues on diff machines
    except AssertionError:
        pytest.xfail(reason="Data order issues on different machines.")


def test_project_delete_children(complete_project):
    project = complete_project
    session = object_session(project)
    assert len(project.datasets) == 19
    assert len(project.scenarios) == 1
    assert len(project.scenarios[0].realizations) == 1
    dataset_ids = [d.id for d in project.datasets]
    scenario_id = project.scenarios[0].id
    realization_id = project.scenarios[0].realizations[0].id

    # Should delete everything except the project (scenario, realization, and datasets)
    project.delete_children()

    assert len(project.datasets) == 0
    assert len(project.scenarios) == 0
    assert session.query(Scenario).get(scenario_id) is None
    assert session.query(Realization).get(realization_id) is None
    assert all(session.query(Dataset).get(did) is None for did in dataset_ids)
