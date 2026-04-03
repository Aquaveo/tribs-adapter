import json
from pathlib import Path
from unittest import mock

import pytest
from pytest_unordered import unordered
from sqlalchemy.orm import object_session

from tethysext.atcore.models.file_database import FileCollection
from tethysext.atcore.services.file_database import FileCollectionClient

from tribs_adapter.app_users import TribsOrganization
from tribs_adapter.resources import Dataset, Scenario
from .serialization_data import serialized_project, replace_random_vals, replace_random_vals_str


@pytest.mark.parametrize(
    "dataset_type,expected_name,expected_value",
    zip(
        [e for e in Dataset.DatasetTypes],
        [e.name for e in Dataset.DatasetTypes],
        [e.value for e in Dataset.DatasetTypes],
    )
)
def test_dataset_type_property(dataset_type, expected_name, expected_value, minimal_dataset):
    assert isinstance(minimal_dataset, Dataset)
    minimal_dataset.dataset_type = dataset_type
    assert minimal_dataset.get_attribute("dataset_type") == expected_value
    assert isinstance(minimal_dataset.dataset_type, Dataset.DatasetTypes)
    assert minimal_dataset.dataset_type.name == expected_name
    assert minimal_dataset.dataset_type.value == expected_value


def test_dataset_type_setter_invalid(minimal_dataset):
    with pytest.raises(ValueError):
        minimal_dataset.dataset_type = "some_invalid_type"


def test_dataset_type_getter_initial(minimal_dataset):
    assert minimal_dataset.dataset_type is None


@pytest.mark.parametrize(
    "dataset_type",
    [e for e in Dataset.DatasetTypes],
)
def test_valid_dataset_types_lazy_load(dataset_type, minimal_dataset):
    assert getattr(minimal_dataset, "_valid_dataset_types", None) is None
    minimal_dataset.dataset_type = dataset_type
    assert getattr(minimal_dataset, "_valid_dataset_types", None) is not None
    _valid_dataset_types = minimal_dataset._valid_dataset_types
    assert dataset_type in minimal_dataset._valid_dataset_types
    # Set again and ensure that _valid_dataset_types created again
    minimal_dataset.dataset_type = dataset_type
    assert minimal_dataset._valid_dataset_types is _valid_dataset_types


# Test cases for Dataset.new() tests
# yapf: disable
one_file = (
    ["salas.ldt"],
    Dataset.DatasetTypes.TRIBS_TABLE_LANDUSE,
    ['__meta__.json', 'salas.ldt'],
    "",
    True,
)
one_file_no_link = (
    ["salas.ldt"],
    Dataset.DatasetTypes.TRIBS_TABLE_LANDUSE,
    ['__meta__.json', 'salas.ldt'],
    "",
    False,
)
one_file_path = (
    [Path("salas.ldt")],
    Dataset.DatasetTypes.TRIBS_TABLE_LANDUSE,
    ['__meta__.json', 'salas.ldt'],
    "",
    True,
)
multiple_files = (
    ["mesh/salas.edges", "mesh/salas.nodes", "mesh/salas.tri", "mesh/salas.z"],
    Dataset.DatasetTypes.TRIBS_TIN,
    ['salas.z', '__meta__.json', 'salas.tri', 'salas.nodes', 'salas.edges'],
    "",
    True,
)
one_directory = (
    ["mesh"],
    Dataset.DatasetTypes.TRIBS_TIN,
    ['__meta__.json', 'mesh/salas.z', 'mesh/salas.tri', 'mesh/salas.nodes', 'mesh/salas.edges'],
    "",
    True,
)
one_directory_path = (
    [Path("mesh")],
    Dataset.DatasetTypes.TRIBS_TIN,
    ['__meta__.json', 'mesh/salas.z', 'mesh/salas.tri', 'mesh/salas.nodes', 'mesh/salas.edges'],
    "",
    True,
)
multiple_directories = (
    ["hyd", "voronoi"],
    Dataset.DatasetTypes.TRIBS_OUT_TIME_INTEGRATED,
    [
        '__meta__.json', 'voronoi/salas.0000_00i', 'voronoi/salas0.pixel', 'voronoi/salas.0000_00d',
        'hyd/salas0700_00.rft', 'hyd/salas_Outlet.qout', 'hyd/salas0700_00.mrf', 'hyd/salas.cntrl'
    ],
    "",
    True,
)
relative_to = (
    ["Weather/weatherC1601_2004.mdf", "Weather/weatherC1601_2004.sdf", "Weather/Nested/weatherCNested1801_2004.mdf"],
    Dataset.DatasetTypes.TRIBS_SDF_HYDROMET_STATION,
    ["__meta__.json", "weatherC1601_2004.mdf", "weatherC1601_2004.sdf", "Nested/weatherCNested1801_2004.mdf"],
    "Weather",
    True,
)
# yapf: enable


def dataset_file_collection_asserts_and_cleanup(dataset, scenario, dataset_type, expected_files, db_session):
    # Dataset File Collection tests
    fc = dataset.file_collection
    assert isinstance(fc, FileCollection)
    assert fc.meta['dataset_id'] == str(dataset.id)
    assert fc.meta['dataset_type'] == dataset_type
    assert dataset.name in fc.meta['description']
    assert str(dataset.id) in fc.meta['description']

    fcc = dataset.file_collection_client
    assert isinstance(fcc, FileCollectionClient)
    assert fcc.instance is fc
    assert fcc.file_database_client.instance is scenario.project.file_database_client.instance
    fc_files = [f for f in fcc.files]
    assert fc_files == unordered(expected_files)

    db_session.delete(dataset)
    db_session.commit()


@pytest.mark.parametrize(
    "test_paths,dataset_type,expected_files,relative_to,link_to_scenario", [
        one_file, one_file_no_link, one_file_path, multiple_files, one_directory, one_directory_path,
        multiple_directories, relative_to
    ]
)
def test_dataset_new(
    test_paths, dataset_type, expected_files, relative_to, link_to_scenario, db_session, scenario_with_project,
    files_dir
):
    # Preserve Path/str objects as provided
    if len(test_paths) >= 1 and isinstance(test_paths[0], Path):
        test_files = [files_dir / "datasets" / f for f in test_paths]
    else:
        test_files = [str(files_dir / "datasets" / f) for f in test_paths]

    if relative_to:
        relative_to = files_dir / "datasets" / relative_to

    scenario = scenario_with_project
    project = scenario.project

    ret = Dataset.new(
        session=db_session,
        name="Test Dataset",
        description="Dataset from new() test",
        created_by="_staff",
        dataset_type=dataset_type,
        srid=26913 if dataset_type in Dataset.SpatialDatasetTypes else None,
        project=project,
        link=scenario if link_to_scenario else None,
        items=test_files,
        relative_to=relative_to,
    )

    assert isinstance(ret, Dataset)
    assert ret.id is not None
    db_session.commit()

    dataset = db_session.query(Dataset).get(ret.id)

    # Dataset tests
    assert dataset.id is not None
    assert dataset.name == "Test Dataset"
    assert dataset.description == "Dataset from new() test"
    assert dataset.created_by == "_staff"
    assert dataset.project == project
    assert dataset.dataset_type == dataset_type
    if dataset_type in Dataset.SpatialDatasetTypes:
        assert dataset.srid == 26913
    else:
        assert dataset.srid is None

    if link_to_scenario:
        assert scenario in dataset.get_linked(of_type=Scenario)
    else:
        assert scenario not in dataset.get_linked(of_type=Scenario)

    dataset_file_collection_asserts_and_cleanup(dataset, scenario, dataset_type, expected_files, db_session)


def test_dataset_new_files_dne(db_session, scenario_with_project):
    with pytest.raises(ValueError):
        Dataset.new(
            session=db_session,
            name="Test Dataset",
            description="Dataset from new() test",
            created_by="_staff",
            dataset_type=Dataset.DatasetTypes.TRIBS_TIN,
            srid=26913,
            project=scenario_with_project.project,
            link=scenario_with_project,
            items=["some_file_that_does_not_exist"],
        )


def test_dataset_new_no_items(db_session, scenario_with_project):
    project = scenario_with_project.project
    dataset = Dataset.new(
        session=db_session,
        name="Test Dataset No Items",
        description="Dataset from new() test with no items",
        created_by="_staff",
        dataset_type=Dataset.DatasetTypes.TRIBS_TIN,
        srid=26913,
        project=project,
        link=scenario_with_project,
        items=[],  # No items
    )

    assert dataset.id is not None
    assert dataset.name == "Test Dataset No Items"
    assert dataset.description == "Dataset from new() test with no items"
    assert dataset.created_by == "_staff"
    assert dataset.project == project
    dataset_file_collection_asserts_and_cleanup(
        dataset, scenario_with_project, Dataset.DatasetTypes.TRIBS_TIN, ['__meta__.json'], db_session
    )


def test_dataset_new_no_srid_spatial(db_session, scenario_with_project):
    with pytest.raises(ValueError):
        Dataset.new(
            session=db_session,
            name="Test Dataset",
            description="Dataset from new() test",
            created_by="_staff",
            dataset_type=Dataset.DatasetTypes.TRIBS_TIN,
            project=scenario_with_project.project,
            link=scenario_with_project,
        )  # srid not provided for spatial dataset (TRIBS_TIN)


def test_dataset_new_fcc(db_session, scenario_with_project):
    project = scenario_with_project.project
    fdc = project.file_database_client
    fcc = fdc.new_collection(items=[], meta={'test': 'fcc'})

    dataset = Dataset.new(
        session=db_session,
        name="Test Dataset FCC",
        description="Dataset from new() test with fcc",
        created_by="_staff",
        dataset_type=Dataset.DatasetTypes.TRIBS_TIN,
        srid=26913,
        project=project,
        link=scenario_with_project,
        fcc=fcc,
    )

    assert dataset.id is not None
    assert dataset.name == "Test Dataset FCC"
    assert dataset.description == "Dataset from new() test with fcc"
    assert dataset.created_by == "_staff"
    assert dataset.project == project
    assert dataset.file_collection == fcc.instance
    assert dataset.file_collection_client.get_meta('test') == 'fcc'
    dataset_file_collection_asserts_and_cleanup(
        dataset, scenario_with_project, Dataset.DatasetTypes.TRIBS_TIN, ['__meta__.json'], db_session
    )


def test_dataset_new_no_items_or_fcc(db_session, scenario_with_project):
    with pytest.raises(ValueError):
        Dataset.new(
            session=db_session,
            name="Test Dataset",
            description="Dataset from new() test",
            created_by="_staff",
            dataset_type=Dataset.DatasetTypes.TRIBS_TIN,
            srid=26913,
            project=scenario_with_project.project,
            link=scenario_with_project,
        )  # items and fcc not provided


def test_dataset_new_relative_to_not_dir(db_session, scenario_with_project):
    with pytest.raises(ValueError):
        Dataset.new(
            session=db_session,
            name="Test Dataset",
            description="Dataset from new() test",
            created_by="_staff",
            dataset_type=Dataset.DatasetTypes.TRIBS_TIN,
            srid=26913,
            project=scenario_with_project.project,
            link=scenario_with_project,
            items=[],  # No items
            relative_to='not_a_dir',
        )


def test_dataset_new_rollback(db_session, scenario_with_project, files_dir):
    with mock.patch.object(Dataset, 'init', side_effect=RuntimeError('Test Rollback')) as mock_init:
        with pytest.raises(RuntimeError) as exc:
            Dataset.new(
                session=db_session,
                name="Test Dataset",
                description="Test Dataset Rollback",
                created_by="_staff",
                dataset_type=Dataset.DatasetTypes.TRIBS_TABLE_LANDUSE,
                project=scenario_with_project.project,
                link=scenario_with_project,
                items=[files_dir / "datasets" / "salas.ldt"],
            )

    assert exc.value.args[0] == 'Test Rollback'
    mock_init.assert_called_once()
    dataset = db_session.query(Dataset) \
        .filter(Dataset.description == 'Test Dataset Rollback') \
        .one_or_none()
    assert dataset is None


@pytest.mark.parametrize("test_paths,dataset_type,expected_files,relative_to,_", [one_file])
def test_dataset_with_organization(
    test_paths, dataset_type, expected_files, relative_to, _, db_session, files_dir, scenario_with_project
):
    scenario = scenario_with_project
    organization = TribsOrganization(
        name='test organization',
        license=TribsOrganization.LICENSES.STANDARD,
    )
    db_session.add(organization)
    db_session.commit()

    test_files = [files_dir / "datasets" / f for f in test_paths]

    if relative_to:
        relative_to = files_dir / "datasets" / relative_to

    dataset = Dataset.new(
        session=db_session,
        name="Test Dataset",
        description="Dataset from new() test",
        created_by="_staff",
        dataset_type=dataset_type,
        srid=26913 if dataset_type in Dataset.SpatialDatasetTypes else None,
        project=scenario.project,
        link=scenario,
        items=test_files,  # No items
        organizations=[organization],
        relative_to=relative_to,
    )
    assert dataset.organizations[0] == organization

    db_session.delete(organization)
    dataset_file_collection_asserts_and_cleanup(dataset, scenario, dataset_type, expected_files, db_session)


def test_dataset_file_collection_client_no_project(db_session, minimal_dataset):
    with pytest.raises(ValueError):
        minimal_dataset.file_collection_client


@pytest.mark.parametrize(
    "test_paths,dataset_type,expected_files,relative_to,_",
    [one_file, one_file_path, multiple_files, one_directory, one_directory_path, multiple_directories, relative_to]
)
def test_dataset_init(
    test_paths, dataset_type, expected_files, relative_to, _, db_session, scenario_with_project, files_dir
):
    # Preserve Path/str objects as provided
    if len(test_paths) >= 1 and isinstance(test_paths[0], Path):
        test_files = [files_dir / "datasets" / f for f in test_paths]
    else:
        test_files = [str(files_dir / "datasets" / f) for f in test_paths]

    if relative_to:
        relative_to = files_dir / "datasets" / relative_to

    scenario = scenario_with_project
    project = scenario_with_project.project

    dataset = Dataset()
    dataset.name = "Test Dataset"
    dataset.description = "Test Dataset Init"
    dataset.created_by = "_staff"
    db_session.add(dataset)
    db_session.commit()

    dataset.init(
        project=project,
        link=scenario,
        dataset_type=dataset_type,
        srid=26913 if dataset_type in Dataset.SpatialDatasetTypes else None,
        items=test_files,
        relative_to=relative_to,
    )

    dataset_file_collection_asserts_and_cleanup(dataset, scenario, dataset_type, expected_files, db_session)


def test_dataset_init_already_initialized(db_session, scenario_with_project, files_dir):
    dataset = Dataset()
    dataset.name = "Test Dataset"
    dataset.description = "Test Dataset Already Initialized"
    dataset.created_by = "_staff"
    db_session.add(dataset)
    db_session.commit()

    dataset.init(
        project=scenario_with_project.project,
        link=scenario_with_project,
        dataset_type=Dataset.DatasetTypes.TRIBS_TABLE_LANDUSE,
        items=[files_dir / "datasets" / "salas.ldt"],
    )

    with pytest.raises(RuntimeError):
        dataset.init(
            project=scenario_with_project.project,
            link=scenario_with_project,
            dataset_type=Dataset.DatasetTypes.TRIBS_TABLE_LANDUSE,
            items=[files_dir / "datasets" / "salas.ldt"],
        )  # Second time should fail


def test_dataset_serialize(complete_project):
    for d in complete_project.datasets:
        if d.name == 'Point File':
            dataset = d
            break
    ret = dataset.serialize()
    assert isinstance(ret, dict)
    replace_random_vals(ret)
    for sd in serialized_project['datasets']:
        if sd['name'] == 'Point File':
            serialized_dataset = sd
            break
    try:
        assert ret == serialized_dataset
    except AssertionError:
        pytest.xfail(reason="Data order issues on different machines.")


def test_dataset_serialize_json(complete_project):
    for d in complete_project.datasets:
        if d.name == 'Point File':
            dataset = d
            break
    ret = dataset.serialize(format='json')
    assert isinstance(ret, str)
    ret = replace_random_vals_str(ret)
    retd = json.loads(ret)
    assert isinstance(retd, dict)
    # unstable: order issues on diff machines
    for sd in serialized_project['datasets']:
        if sd['name'] == 'Point File':
            serialized_dataset = sd
            break
    try:
        assert retd == serialized_dataset
    except AssertionError:
        pytest.xfail(reason="Data order issues on different machines.")


def test_dataset_duplicate(dataset_with_files):
    og_dataset = dataset_with_files
    dp_dataset = Dataset.duplicate(og_dataset, "someuser", "Duplicated Dataset")
    assert dp_dataset.id != og_dataset.id
    assert dp_dataset.name == "Duplicated Dataset"
    assert dp_dataset.description == og_dataset.description
    assert dp_dataset.created_by == "someuser"
    assert dp_dataset.project == og_dataset.project
    assert dp_dataset.linked_scenarios == og_dataset.linked_scenarios
    assert dp_dataset.file_collection is not None
    assert dp_dataset.file_collection != og_dataset.file_collection
    og_fcc = og_dataset.file_collection_client
    dp_fcc = dp_dataset.file_collection_client
    assert dp_fcc.instance.meta['dataset_id'] == str(dp_dataset.id)
    assert dp_fcc.instance.meta['dataset_type'] == og_dataset.dataset_type
    assert dp_fcc.instance.meta['description'] \
        == f'File collection for dataset "Duplicated Dataset" ({str(dp_dataset.id)})'
    assert [f for f in dp_fcc.files] == [f for f in og_fcc.files]

    db_session = object_session(dp_dataset)
    db_session.delete(dp_dataset)
    db_session.commit()


def test_dataset_duplicate_exception(dataset_with_files, mocker):
    og_dataset = dataset_with_files
    mocker.patch.object(Dataset, 'new', side_effect=RuntimeError('Test Duplicate'))
    with pytest.raises(RuntimeError):
        Dataset.duplicate(og_dataset, "someuser", "Duplicated Dataset")


def test_dataset_generate_visualization():
    dataset = Dataset()
    mock_spatial_manager = mock.MagicMock()
    mock_session = mock.MagicMock()

    dataset.generate_visualization(mock_session, mock_spatial_manager)

    mock_spatial_manager.create_layer_for_dataset.assert_called_once()


def test_dataset_remove_visualization():
    dataset = Dataset()
    mock_spatial_manager = mock.MagicMock()
    mock_session = mock.MagicMock()

    dataset.remove_visualization(mock_session, mock_spatial_manager)

    mock_spatial_manager.delete_layer_for_dataset.assert_called_once()
