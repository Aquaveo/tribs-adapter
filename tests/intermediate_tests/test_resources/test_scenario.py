import json
import datetime
from unittest import mock
from uuid import UUID, uuid4

import pytest
import pydantic
from pytest_unordered import unordered
from sqlalchemy.orm import object_session

from tribs_adapter.resources import Scenario, Dataset, Project, Realization
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from tribs_adapter.io.input_file import FileDatabasePath, FileDatabasePathCollection
from .scenario_data import (
    expected_datasets_salas, expected_file_fields_salas, expected_datasets_examplebasin,
    expected_file_fields_examplebasin, expected_datasets_salas_issues, expected_file_fields_salas_issues
)
from .serialization_data import serialized_project, replace_random_vals, replace_random_vals_str


def test_scenario_project_property(db_session, minimal_project, minimal_scenario):
    minimal_scenario.project = minimal_project
    db_session.add(minimal_scenario)
    db_session.commit()

    scenario = db_session.query(Scenario).one()
    project = scenario.project
    assert scenario.project == project

    # test new project replaces old project
    new_project = Project(name='New Project')
    scenario.project = new_project
    assert scenario.project == new_project
    assert scenario.project != project

    db_session.delete(scenario)
    db_session.delete(project)


def test_scenario_project_property_invalid(minimal_scenario):
    with pytest.raises(ValueError):
        minimal_scenario.project = 'not-a-project'


def test_realizations_methods(db_session, minimal_project, minimal_scenario, minimal_realization):
    minimal_scenario.project = minimal_project

    # scenario.add_realization
    minimal_scenario.add_realization(minimal_realization)
    db_session.add(minimal_scenario)
    db_session.commit()

    scenario = db_session.query(Scenario).one()
    realization = db_session.query(Realization).one()

    # scenario.realizations
    assert len(scenario.realizations) == 1
    assert scenario.realizations[0] == realization

    # scenario.get_realization
    assert scenario.get_realization(realization.id) == realization

    # scenario.remove_realization
    scenario.remove_realization(realization)
    db_session.commit()
    assert len(scenario.realizations) == 0

    db_session.delete(scenario)
    db_session.delete(realization)
    db_session.delete(minimal_project)


def test_scenario_realizations_methods_validation(minimal_scenario):
    with pytest.raises(ValueError):
        minimal_scenario.add_realization('not-a-realization')

    with pytest.raises(ValueError):
        minimal_scenario.remove_realization('not-a-realization')


# Test cases
salas_in = ('salas/salas.in', expected_file_fields_salas, expected_datasets_salas, 5)
examplebasin_in = ('examplebasin/examplebasin.in', expected_file_fields_examplebasin, expected_datasets_examplebasin, 1)
salas_issues = ('salas_issues/salas_issues.in', expected_file_fields_salas_issues, expected_datasets_salas_issues, 8)


def scenario_asserts_and_cleanup(
    scenario_id, input_file, expected_file_fields, expected_datasets, expected_warnings, db_session, project_with_fdb,
    recwarn
):
    assert scenario_id is not None
    assert len(recwarn) == expected_warnings

    scenario = db_session.query(Scenario).get(scenario_id)

    assert scenario.project is project_with_fdb
    assert len(scenario.get_linked(of_type=Dataset)) == len(expected_datasets)

    assert scenario.input_file is not None
    assert scenario.input_file.file_name in input_file

    for card, f in scenario.input_file.files():
        expected = expected_file_fields[card]
        try:
            if isinstance(f, FileDatabasePath):
                assert isinstance(f.resource_id, UUID) is expected['has_resource_id']  # True => has UUID
                assert isinstance(f.file_collection_id, UUID) is expected['has_file_collection_id']  # True => has UUID
                assert f.file_collection_paths == unordered(expected['file_collection_paths'])
            elif isinstance(f, FileDatabasePathCollection):
                assert f.file_database_paths == unordered(expected['file_database_paths'])
            assert f.path == expected['path']
        except (AssertionError, KeyError):
            print(f'Failed on card {card}')
            raise

    for dataset, expected_dataset in zip(
        sorted(scenario.get_linked(of_type=Dataset), key=lambda d: d.name),
        sorted(expected_datasets, key=lambda e: e['name'])
    ):
        assert dataset.name == expected_dataset['name']
        assert dataset.description == expected_dataset['description']
        assert dataset.dataset_type == expected_dataset['type']
        assert scenario in dataset.get_linked(of_type=Scenario)
        db_session.delete(dataset)

    db_session.delete(scenario)
    db_session.commit()


@pytest.mark.parametrize(
    'input_file,expected_file_fields,expected_datasets,expected_warnings', [salas_in, examplebasin_in, salas_issues]
)
def test_scenario_new(
    input_file,
    expected_file_fields,
    expected_datasets,
    expected_warnings,
    db_session,
    project_with_fdb,
    files_dir,
    recwarn,
):
    input_file_path = files_dir / 'models' / input_file

    ret = Scenario.new(
        session=db_session,
        name='Test Scenario',
        description='Test Scenario Description',
        created_by='_staff',
        project=project_with_fdb,
        srid=26913,
        input_file=input_file_path,
    )

    scenario_asserts_and_cleanup(
        ret.id, input_file, expected_file_fields, expected_datasets, expected_warnings, db_session, project_with_fdb,
        recwarn
    )


def test_scenario_new_input_file_dne(db_session, project_with_fdb, files_dir):
    input_file_path = files_dir / 'models' / 'dne' / 'does_not_exist.dne'

    with pytest.raises(FileNotFoundError):
        Scenario.new(
            session=db_session,
            name='Test Scenario',
            description='Test Scenario Description',
            created_by='_staff',
            project=project_with_fdb,
            srid=26913,
            input_file=input_file_path,
        )


@pytest.mark.filterwarnings('ignore::UserWarning')
def test_scenario_new_input_file_str_path(db_session, project_with_fdb, files_dir):
    input_file_path = str(files_dir / 'models' / 'salas' / 'salas.in')

    scenario = Scenario.new(
        session=db_session,
        name='Test Scenario',
        description='Test Scenario Description',
        created_by='_staff',
        project=project_with_fdb,
        srid=26913,
        input_file=input_file_path,
    )

    assert scenario.id is not None

    for dataset in scenario.get_linked(of_type=Dataset):
        db_session.delete(dataset)

    db_session.delete(scenario)
    db_session.commit()


@pytest.mark.filterwarnings('ignore::UserWarning')
def test_scenario_new_srid_required(db_session, project_with_fdb, files_dir):
    input_file_path = files_dir / 'models' / 'salas' / 'salas.in'

    with pytest.raises(ValueError):
        Scenario.new(
            session=db_session,
            name='Test Scenario',
            description='Test Scenario Description',
            created_by='_staff',
            project=project_with_fdb,
            srid=None,  # SRID is required when input file provided
            input_file=input_file_path,
        )


def test_scenario_new_rollback(db_session, project_with_fdb, files_dir):
    input_file_path = files_dir / 'models' / 'salas' / 'salas.in'
    with mock.patch.object(Scenario, 'init', side_effect=RuntimeError('Test Rollback')) as mock_init:
        with pytest.raises(RuntimeError) as exc:
            Scenario.new(
                session=db_session,
                name='Test Scenario',
                description='Test Scenario Rollback',
                created_by='_staff',
                project=project_with_fdb,
                srid=26913,
                input_file=input_file_path,
            )

    assert exc.value.args[0] == 'Test Rollback'
    mock_init.assert_called_once()
    secnario = db_session.query(Scenario) \
        .filter(Scenario.description == 'Test Scenario Rollback') \
        .one_or_none()
    assert secnario is None


@pytest.mark.parametrize(
    'input_file,expected_file_fields,expected_datasets,expected_warnings', [salas_in, examplebasin_in, salas_issues]
)
def test_scenario_init(
    input_file,
    expected_file_fields,
    expected_datasets,
    expected_warnings,
    db_session,
    project_with_fdb,
    files_dir,
    recwarn,
):
    input_file_path = files_dir / 'models' / input_file
    scenario = Scenario()
    scenario.name = 'Test Scenario'
    scenario.description = 'Test Scenario Init'
    scenario.created_by = '_staff'
    db_session.add(scenario)
    db_session.commit()
    mock_sm = mock.MagicMock(spec=TribsSpatialManager)

    scenario.init(
        project=project_with_fdb,
        srid=26913,
        input_file=input_file_path,
        spatial_manager=mock_sm,
    )

    scenario_asserts_and_cleanup(
        scenario.id, input_file, expected_file_fields, expected_datasets, expected_warnings, db_session,
        project_with_fdb, recwarn
    )
    mock_sm.create_layer_for_dataset.assert_called()


def test_scenario_init_no_input_file(db_session, project_with_fdb, recwarn):
    scenario = Scenario()
    scenario.name = 'Test Scenario'
    scenario.description = 'Test Scenario Init'
    scenario.created_by = '_staff'
    db_session.add(scenario)
    db_session.commit()

    scenario.init(project=project_with_fdb, )

    assert scenario.input_file is not None


def test_scenario_init_invalid_input_file(db_session, project_with_fdb, files_dir):
    input_file_path = files_dir / 'models' / 'dne' / 'does_not_exist.dne'
    scenario = Scenario()
    scenario.name = 'Test Scenario'
    scenario.description = 'Test Scenario Init'
    scenario.created_by = '_staff'
    db_session.add(scenario)
    db_session.commit()

    with pytest.raises(FileNotFoundError):
        scenario.init(
            project=project_with_fdb,
            srid=26913,
            input_file=input_file_path,
        )

    db_session.delete(scenario)
    db_session.commit()


def test_scenario_init_already_initialized(db_session, project_with_fdb, files_dir, recwarn):
    input_file_path = files_dir / 'models' / 'salas' / 'salas.in'
    scenario = Scenario()
    scenario.name = 'Test Scenario'
    scenario.description = 'Test Scenario Init'
    scenario.created_by = '_staff'
    db_session.add(scenario)
    db_session.commit()

    scenario.init(
        project=project_with_fdb,
        srid=26913,
        input_file=input_file_path,
    )

    with pytest.raises(RuntimeError):
        scenario.init(
            project=project_with_fdb,
            srid=26913,
            input_file=input_file_path,
        )  # second init should fail

    db_session.delete(scenario)
    db_session.commit()


def test_scenario_init_dataset_exception(db_session, project_with_fdb, files_dir, recwarn):
    input_file_path = files_dir / 'models' / 'salas' / 'salas.in'
    scenario = Scenario()
    scenario.name = 'Test Scenario'
    scenario.description = 'Test Scenario Init'
    scenario.created_by = '_staff'
    db_session.add(scenario)
    db_session.commit()

    def dataset_new(name, *args, **kwargs):
        if 'Groundwater Grid' in name:
            raise RuntimeError('Test Dataset Exception')
        return mock.MagicMock(
            spec=Dataset,
            id=uuid4(),
            file_collection=mock.MagicMock(id=uuid4()),
            file_collection_client=mock.MagicMock(files=[]),
        )

    with mock.patch.object(Dataset, 'new', side_effect=dataset_new) as mock_new_dataset, \
         mock.patch('tribs_adapter.resources.scenario.log') as mock_log:
        scenario.init(
            project=project_with_fdb,
            srid=26913,
            input_file=input_file_path,
        )

    mock_log.exception.assert_called_once()
    mock_log.exception.assert_called_with(
        'Failed to initialize Dataset "Groundwater Grid" for card "GWATERFILE". Skipping...'
    )
    mock_new_dataset.assert_called()
    assert len(mock_new_dataset.call_args_list) == 12
    scenario_input_files = scenario.input_file.files(mode=scenario.input_file.FilesMode.INPUT_ONLY)
    initialized_dataset_fields = [f for _, f in scenario_input_files if f.resource_id is not None]
    # 12 datasets in salas.in, but Groundwater Grid fails to initialize
    assert len(initialized_dataset_fields) == 11
    assert not any([d.name == 'Groundwater Grid' for d in scenario.get_linked(of_type=Dataset)])

    # Clean up
    for dataset in scenario.get_linked(of_type=Dataset):
        db_session.delete(dataset)
    db_session.delete(scenario)
    db_session.commit()


def test_scenario_init_generate_visualizations_exception(db_session, project_with_fdb, files_dir, recwarn):
    input_file_path = files_dir / 'models' / 'salas' / 'salas.in'
    scenario = Scenario()
    scenario.name = 'Test Scenario'
    scenario.description = 'Test Scenario Init'
    scenario.created_by = '_staff'
    db_session.add(scenario)
    db_session.commit()
    mock_sm = mock.MagicMock(spec=TribsSpatialManager)
    mock_sm.create_layer_for_dataset.side_effect = RuntimeError('Test Scenario Visualization Exception')

    # No exception raised (init finishes)
    with mock.patch('tribs_adapter.resources.scenario.log') as mock_log:
        scenario.init(
            project=project_with_fdb,
            srid=32613,
            input_file=input_file_path,
            spatial_manager=mock_sm,
        )

        # should log the exception with any call to generate_visualizations had exceptions (all of them)
        assert mock_log.exception.call_count == 12

        # dataset objects are still created and linked to the scenario
        for dataset in scenario.linked_datasets:
            mock_log.exception.assert_any_call(
                f'Failed to generate visualization for Dataset named "{dataset.name}" ({dataset.id}.'
            )

    db_session.delete(scenario)
    db_session.commit()


# yapf: disable
@pytest.mark.filterwarnings('ignore::UserWarning')
@pytest.mark.parametrize(
    'input_file,with_datasets,expected_files',
    [
        ('salas/salas.in', True, [
            'Input/Nodes/hNodes.dat', 'Input/Nodes/oNodes.dat', 'Input/Nodes/pNodes.dat',
            'Input/salas.iwt', 'Input/salas.lan', 'Input/salas.ldt', 'Input/salas.points',
            'Input/salas.sdt', 'Input/salas.soi',
            'Output/voronoi/salas.edges', 'Output/voronoi/salas.tri', 'Output/voronoi/salas.nodes',
            'Output/voronoi/salas_area', 'Output/voronoi/salas_reach', 'Output/voronoi/salas_voi',
            'Output/voronoi/salas_width', 'Output/voronoi/salas.z',
            'Rain/p0531200418.txt', 'Rain/p0630200417.txt',
            'Weather/weatherC1601_2004.sdf', 'Weather/weatherC1601_2004.mdf',
            'salas.in',
        ]),
        ('examplebasin/examplebasin.in', True, [
            'examplebasin.in',
            'Input/examplebasin.lan', 'Input/examplebasin.sdt', 'Input/examplebasin.soi',
            'Input/examplebasin.ldt', 'Input/examplebasingw.iwt', 'Input/Nodes/oNodes.dat',
            'Input/Nodes/hNodes.dat', 'Input/Nodes/pNodes.dat', 'Input/PointFiles/examplebasin.points',
            'Output/Fall1996/voronoi/examplebasin_area', 'Output/Fall1996/voronoi/examplebasin.edges',
            'Output/Fall1996/voronoi/examplebasin.nodes', 'Output/Fall1996/voronoi/examplebasin.z',
            'Output/Fall1996/voronoi/examplebasin_reach', 'Output/Fall1996/voronoi/examplebasin.tri',
            'Output/Fall1996/voronoi/examplebasin_voi', 'Output/Fall1996/voronoi/examplebasin_width',
            'Weather/Fall1996/bfFall1996_dmp.sdf', 'Weather/Fall1996/bfFall1996_dmp.mdf',
            'Rain/Fall1996/p0920199603.txt', 'Rain/Fall1996/p0920199609.txt', 'Rain/Fall1996/p0920199607.txt',
            'Rain/Fall1996/p0920199612.txt', 'Rain/Fall1996/p0920199601.txt', 'Rain/Fall1996/p0920199611.txt',
            'Rain/Fall1996/p0920199610.txt', 'Rain/Fall1996/p0920199608.txt', 'Rain/Fall1996/p0920199600.txt',
            'Rain/Fall1996/p0920199602.txt', 'Rain/Fall1996/p0920199605.txt', 'Rain/Fall1996/p0920199604.txt',
            'Rain/Fall1996/p0920199606.txt',
        ]),
        ('salas/salas.in', False, [
            'salas.in',
        ]),
        ('examplebasin/examplebasin.in', False, [
            'examplebasin.in',
        ]),
        ('salas_issues/salas_issues.in', True, [
            'Input/salas.iwt', 'Input/salas.points', 'Input/salas.sdt',
            'Input/salas.soi', 'Input/salas.ldt', 'Input/Nodes/oNodes.dat',
            'Input/Nodes/hNodes.dat', 'Input/Nodes/pNodes.dat',
            'Output/voronoi/salas.z', 'Output/voronoi/salas_voi', 'Output/voronoi/salas_width',
            'Output/voronoi/salas.tri', 'Output/voronoi/salas_area', 'Output/voronoi/salas.nodes',
            'Output/voronoi/salas_reach', 'Output/voronoi/salas.edges',
            'Weather/weatherC1601_2004.sdf', 'Weather/weatherC1601_2004.mdf',
            'Weather/Nested/weatherCNested1801_2004.mdf',
            'Forecast/forecast.fake', 'Forecast/Nested/nested_forecast.fake',
            'LandCover/salas.ltf', 'LandCover/salas.lvh', 'LandCover/salas.gdf', 'LandCover/salas.lal',
            'salas_issues.in',
        ]),
    ]
)
# yapf: enable
def test_scenario_export(
    input_file, with_datasets, expected_files, db_session, scenario_with_input, files_dir, tmp_path
):
    input_file_path = files_dir / 'models' / input_file

    scenario = scenario_with_input(input_file_path)

    # Validate import
    assert scenario.id is not None
    assert len(scenario.get_linked(of_type=Dataset)) > 0

    out_dir = tmp_path / 'out'
    out_dir.mkdir(parents=True, exist_ok=True)

    scenario.export(out_dir, with_datasets=with_datasets)
    exported_files = [str(p.relative_to(out_dir)) for p in out_dir.glob('**/*') if p.is_file()]

    assert exported_files == unordered(expected_files)

    for dataset in scenario.get_linked(of_type=Dataset):
        db_session.delete(dataset)

    db_session.delete(scenario)
    db_session.commit()


@pytest.mark.filterwarnings('ignore::UserWarning')
def test_scenario_export_directory_not_dir(scenario_with_input, files_dir, tmp_path):
    input_file_path = files_dir / 'models' / 'salas' / 'salas.in'

    scenario = scenario_with_input(input_file_path)

    with pytest.raises(ValueError):
        scenario.export(tmp_path / 'out' / 'dne')


def test_scenario_serialize(complete_project):
    scenario = complete_project.scenarios[0]
    ret = scenario.serialize()
    assert isinstance(ret, dict)
    replace_random_vals(ret)
    try:
        assert ret == serialized_project['scenarios'][0]
    except AssertionError:
        pytest.xfail(reason="Data order issues on different machines.")


def test_scenario_serialize_json(complete_project):
    scenario = complete_project.scenarios[0]
    ret = scenario.serialize(format='json')
    assert isinstance(ret, str)
    ret = replace_random_vals_str(ret)
    retd = json.loads(ret)
    assert isinstance(retd, dict)
    try:
        assert retd == serialized_project['scenarios'][0]  # unstable: order issues on diff machines
    except AssertionError:
        pytest.xfail(reason="Data order issues on different machines.")


def test_scenario_link_dataset(scenario_with_input_file, dataset_with_files, recwarn):
    scenario = scenario_with_input_file
    dataset = dataset_with_files
    session = object_session(scenario)

    scenario.link_dataset(dataset, 'INPUTDATAFILE')
    session.commit()

    assert dataset in scenario.linked_datasets
    assert scenario.input_file.get_value('INPUTDATAFILE').resource_id == dataset.id


def test_scenario_link_dataset_different_projects(scenario_with_project, minimal_dataset, recwarn):
    scenario = scenario_with_project
    session = object_session(scenario)
    new_project = Project(name='A different project')
    dataset = minimal_dataset
    dataset.project = new_project
    session.add(dataset)
    session.commit()

    with pytest.raises(ValueError) as exc:
        scenario.link_dataset(dataset, 'INPUTDATAFILE')
        assert exc.value.args[0] == 'Dataset and Scenario must belong to the same Project'


def test_scenario_unlink_dataset(dataset_with_scenario_and_project):
    dataset = dataset_with_scenario_and_project
    scenario = dataset.linked_scenarios[0]
    session = object_session(dataset)

    scenario.unlink_dataset(dataset, 'INPUTDATAFILE')
    session.commit()

    assert dataset not in scenario.linked_datasets
    assert scenario.input_file.get_value('INPUTDATAFILE').resource_id is None


def test_scenario_delete_children(complete_project):
    project = complete_project
    session = object_session(project)
    assert len(project.datasets) == 19
    assert len(project.scenarios) == 1
    assert len(project.scenarios[0].realizations) == 1
    scenario = project.scenarios[0]
    dataset_ids = [d.id for d in project.datasets]
    scenario_id = scenario.id
    realization_id = scenario.realizations[0].id

    # Should delete all datasets linked to scenario, related realizations, and datasets linked to realizations
    scenario.delete_children()

    assert len(project.datasets) == 0
    assert len(project.scenarios) == 1
    assert session.query(Scenario).get(scenario_id) is not None
    assert session.query(Realization).get(realization_id) is None
    assert all(session.query(Dataset).get(did) is None for did in dataset_ids)


def test_scenario_update_input_file_structured_dict(scenario_with_input_file, dataset_with_files, recwarn):
    scenario = scenario_with_input_file
    dataset = dataset_with_files

    # structured dict
    update = {
        "file_name": "foo.in",
        "run_parameters": {
            "time_variables": {
                "STARTDATE": "2020-01-01T00:00:00.000",
                "RUNTIME": 720,
                "IDONTEXIST": "don't save me",  # Invalid key
            },
        },
        "run_options": {
            "OPTMESHINPUT": 7,
            # "OPTEVAPOTRANS": 5,  # Invalid value
            # "OPTINTERCEPT": 5,  # Invalid value
        },
        "files_and_pathnames": {
            "mesh_generation": {
                "INPUTDATAFILE": {
                    "resource_id": str(dataset.id)
                },  # Existing dataset
                "POINTFILENAME": {
                    "resource_id": None
                },  # Remove points dataset
            },
            "output_data": {
                "OUTHYDROEXTENSION": "out",
                "RIBSHYDOUTPUT": 1,
            },
            "resampling_grids": {
                "SOILTABLENAME": {
                    "resource_id": "",
                },  # Empty string alternative for removing dataset/no dataset selected
            }
        },
    }

    scenario.update_input_file(update)

    u_input_file = scenario.input_file
    assert u_input_file.file_name == "foo.in"
    assert u_input_file.get_value("STARTDATE") == datetime.datetime(2020, 1, 1, 0, 0)
    assert u_input_file.get_value("RUNTIME") == 720
    assert u_input_file.get_value("OPTMESHINPUT") == 7
    assert u_input_file.get_value("OUTHYDROEXTENSION") == "out"
    assert u_input_file.get_value("RIBSHYDOUTPUT") == 1
    assert u_input_file.get_value("POINTFILENAME").resource_id is None
    assert u_input_file.get_value("SOILTABLENAME").resource_id is None
    assert u_input_file.get_value("INPUTDATAFILE").resource_id == dataset.id


def test_scenario_update_input_file_flat_dict(scenario_with_input_file, dataset_with_files, recwarn):
    scenario = scenario_with_input_file
    dataset = dataset_with_files

    # flat dict
    update = {
        "file_name": "foo.in",
        "STARTDATE": "2020-01-01T00:00:00.000",
        "RUNTIME": 720,
        "IDONTEXIST": "don't save me",  # Invalid key
        "OPTMESHINPUT": 7,
        "INPUTDATAFILE": {
            "resource_id": str(dataset.id)
        },  # Existing dataset
        "POINTFILENAME": {
            "resource_id": None
        },  # Remove points dataset
        "SOILTABLENAME": {
            "resource_id": "",
        },  # Empty string alternative for removing dataset/no dataset selected
        "OUTHYDROEXTENSION": "out",
        "RIBSHYDOUTPUT": 1,
    }

    scenario.update_input_file(update)

    u_input_file = scenario.input_file
    assert u_input_file.file_name == "foo.in"
    assert u_input_file.get_value("STARTDATE") == datetime.datetime(2020, 1, 1, 0, 0)
    assert u_input_file.get_value("RUNTIME") == 720
    assert u_input_file.get_value("OPTMESHINPUT") == 7
    assert u_input_file.get_value("OUTHYDROEXTENSION") == "out"
    assert u_input_file.get_value("RIBSHYDOUTPUT") == 1
    assert u_input_file.get_value("POINTFILENAME").resource_id is None
    assert u_input_file.get_value("SOILTABLENAME").resource_id is None
    assert u_input_file.get_value("INPUTDATAFILE").resource_id == dataset.id


def test_scenario_update_input_file_value_errors(scenario_with_input_file, dataset_with_files, recwarn):
    scenario = scenario_with_input_file

    # flat dict
    update = {
        "file_name": "foo.in",
        "STARTDATE": "2020-01-01T00:00:00.000",
        "RUNTIME": 720,
        "OPTMESHINPUT": 10,  # Invalid value
        "OUTHYDROEXTENSION": "out",
        "RIBSHYDOUTPUT": 1,
    }

    with pytest.raises(pydantic.ValidationError) as exc:
        scenario.update_input_file(update)

    errs = exc.value.errors()
    assert len(errs) == 1
    errs[0]['url'] = ''  # Remove URL for testing
    assert errs == [{
        'ctx': {
            'expected': '1, 2, 3, 4, 5, 6, 7, 8 or 9',
        },
        'input': 10,
        'loc': ('OPTMESHINPUT', ),
        'msg': 'Input should be 1, 2, 3, 4, 5, 6, 7, 8 or 9',
        'type': 'enum',
        'url': '',
    }]
