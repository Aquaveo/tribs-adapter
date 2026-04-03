import datetime
import warnings

import pytest
from sqlalchemy.orm import object_session

from tribs_adapter.io import tRIBSInput
from tribs_adapter.resources import Scenario, Dataset, Realization


@pytest.fixture(scope="function")
def minimal_scenario():
    scenario = Scenario(
        name="Test Scenario",
        description="Test Scenario Description",
        date_created=datetime.datetime.utcnow(),
        created_by="_staff",
    )
    return scenario


@pytest.fixture(scope="function")
def scenario_with_project(project_with_fdb):
    session = object_session(project_with_fdb)
    scenario = Scenario(
        name="Test Scenario",
        description="Test Scenario Description",
        date_created=datetime.datetime.utcnow(),
        created_by="_staff",
    )
    scenario.project = project_with_fdb
    session.add(scenario)
    session.commit()
    yield scenario
    session.delete(scenario)


@pytest.fixture(scope="function")
def scenario_default_input_file(scenario_with_project):
    session = object_session(scenario_with_project)
    scenario = scenario_with_project
    scenario.input_file = tRIBSInput()
    session.commit()
    yield scenario
    session.delete(scenario)


@pytest.fixture(scope="function")
def scenario_with_input(project_with_fdb):
    def _scenario_with_input(input_file_path):
        session = object_session(project_with_fdb)
        scenario = Scenario.new(
            session=session,
            name='Test Scenario',
            description='Test Scenario with Project and Input Datasets',
            created_by='_staff',
            project=project_with_fdb,
            srid=26913,
            input_file=input_file_path,
        )
        return scenario

    return _scenario_with_input


@pytest.fixture(scope="function")
def minimal_dataset():
    dataset = Dataset(
        name="Test Dataset",
        description="Test Dataset Description",
        date_created=datetime.datetime.utcnow(),
        created_by="_staff",
    )
    return dataset


@pytest.fixture(scope="function")
def minimal_realization():
    realization = Realization(
        name="Test Realization",
        description="Test Realization Description",
        date_created=datetime.datetime.utcnow(),
        created_by="_staff",
    )
    return realization


@pytest.fixture(scope="function")
def project(db_session, minimal_project):
    db_session.add(minimal_project)
    db_session.commit()
    yield minimal_project
    db_session.delete(minimal_project)
    db_session.commit()


@pytest.fixture(scope="function")
def complete_project(project_with_fdb, files_dir):
    project = project_with_fdb
    session = object_session(project)
    model_root = files_dir / 'models' / 'salas'
    input_file_path = model_root / 'salas.in'
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        scenario = Scenario.new(
            session=session,
            name='Salas',
            description='Fully populated scenario for testing.',
            created_by='_staff',
            project=project,
            srid=26913,
            input_file=input_file_path,
        )
        Realization.new(
            session=session,
            name='Salas Run 10-20-30',
            description='Results from run of Salas scenario.',
            created_by='_staff',
            scenario=scenario,
            model_root=model_root,
        )
    return project


@pytest.fixture(scope="function")
def dataset_with_scenario_and_project(db_session, scenario_default_input_file):
    scenario = scenario_default_input_file
    dataset = Dataset(name='test_dataset')
    dataset.project = scenario.project
    dataset.add_link(scenario)
    dataset.dataset_type = Dataset.DatasetTypes.JSON
    db_session.add(dataset)
    db_session.commit()
    yield dataset
    db_session.delete(dataset)
    db_session.commit()
