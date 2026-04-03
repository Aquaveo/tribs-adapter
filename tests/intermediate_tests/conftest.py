import datetime
from unittest import mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session

from tethysext.atcore.models.app_users import AppUsersBase

from tethysext.atcore.services.file_database import FileDatabaseClient
from tribs_adapter.resources import Project, Dataset, Scenario
from tribs_adapter.app_users import TribsOrganization  # noqa: F401, F403
from ..intermediate_tests import TEST_DB_URL


@pytest.fixture(scope="function")
def temp_file_database(db_session, tmpdir):
    """
    Create a temporary file database.
    """
    fdc = FileDatabaseClient.new(db_session, tmpdir)
    return fdc


@pytest.fixture(scope="function")
def minimal_project(temp_file_database):
    """
    Create a minimal project with a file database.
    """
    project = Project(
        name="Test Project",
        description="Test Project Description",
        date_created=datetime.datetime.utcnow(),
        created_by="_staff",
        file_database=temp_file_database.instance,
    )
    return project


@pytest.fixture(scope="function")
def project_with_fdb(db_session, tmp_path):
    """
    Create a project with a file database.
    """
    with mock.patch.dict('os.environ', {'FDB_ROOT_DIR': str(tmp_path)}, clear=True):
        project = Project.new(
            session=db_session,
            name='Test FDB Project',
            description='Initialized Project with File Database.',
            created_by='_staff',
        )

        yield project

        db_session.delete(project)
        db_session.commit()


@pytest.fixture(scope="function")
def dataset_with_files(db_session, project_with_fdb, files_dir):
    dataset = Dataset.new(
        session=db_session,
        name='Test Dataset',
        description='Initialized Dataset with Files.',
        created_by='_staff',
        project=project_with_fdb,
        dataset_type=Dataset.DatasetTypes.TRIBS_TIN,
        srid=26913,
        items=(files_dir / 'datasets' / 'mesh').glob('salas.*'),
    )
    yield dataset
    try:
        db_session.refresh(dataset)
        db_session.delete(dataset)
        db_session.commit()
    except InvalidRequestError as e:
        if 'Could not refresh instance' in str(e):
            pass
        else:
            raise e


@pytest.fixture(scope="module")
def db_connection():
    """
    Create a SQLAlchemy engine for the primary database.
    """
    engine = create_engine(TEST_DB_URL)
    connection = engine.connect()
    transaction = connection.begin()

    # Create ATCore-related tables (e.g.: Resources)
    AppUsersBase.metadata.create_all(connection)

    yield connection

    transaction.rollback()
    connection.close()
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_connection):
    """
    Create a SQLAlchemy session for the primary database.
    """
    db_connection.begin_nested()
    session = Session(db_connection)

    yield session

    session.close()


@pytest.fixture(scope="function")
def scenario_with_input_file(db_session, project_with_fdb, files_dir):
    input_file = files_dir / 'models' / 'salas' / 'salas.in'
    scenario = Scenario.new(
        session=db_session,
        name='Input File Scenario',
        description='Salas input file scenario',
        created_by='_staff',
        project=project_with_fdb,
        srid=32613,
        input_file=input_file,
    )
    yield scenario
    db_session.delete(scenario)
    db_session.commit()
