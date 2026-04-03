import os
import pytest
import warnings
from sqlalchemy.orm import object_session
from unittest.mock import MagicMock
from tethys_dataset_services.engines import GeoServerSpatialDatasetEngine
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from tribs_adapter.resources import Dataset
from tribs_adapter.common.dataset_types import DatasetTypes


@pytest.fixture(scope="module")
def mock_geoserver_engine():
    """
    Create a GeoServerSpatialDatasetEngine for the GeoServer instance.
    """
    geoserver_engine = GeoServerSpatialDatasetEngine(
        endpoint="http://localhost:8181/geoserver/rest",
        username="admin",
        password="geoserver",
        node_ports=[8081, 8082, 8083, 8084],
    )

    geoserver_engine.create_workspace = MagicMock()
    geoserver_engine.create_style = MagicMock()
    geoserver_engine.create_shapefile_resource = MagicMock()
    geoserver_engine.create_coverage_layer = MagicMock()
    geoserver_engine.enable_time_dimension = MagicMock()
    geoserver_engine.delete_layer = MagicMock()
    geoserver_engine.delete_coverage_store = MagicMock()
    geoserver_engine.delete_style = MagicMock()

    return geoserver_engine


@pytest.fixture(scope="module")
def tsm(mock_geoserver_engine):
    """
    Create a TribsSpatialManager for the GeoServer instance.
    """
    tsm = TribsSpatialManager(geoserver_engine=mock_geoserver_engine)
    return tsm


@pytest.fixture(scope="function")
def project_with_datasets(project_with_fdb, files_dir):
    """
    Create a project with datasets.
    """
    project = project_with_fdb
    session = object_session(project)
    model_root = files_dir / "spatial_manager" / "layers"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        dataset1 = Dataset.new(
            session=session,
            name="Dataset 1",
            description="Dataset 1 Shape",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.FEATURES_SHAPEFILE,
            srid=26913,
            items=[os.path.join(model_root / "shape", x) for x in os.listdir(model_root / "shape")],
            relative_to=model_root / "shape",
        )
        dataset2 = Dataset.new(
            session=session,
            name="Dataset 2",
            description="Dataset 2 Acii",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.RASTER_CONT_ASCII,
            srid=26913,
            items=[os.path.join(model_root / "ascii", x) for x in os.listdir(model_root / "ascii")],
            relative_to=model_root / "ascii",
        )
        dataset3 = Dataset.new(
            session=session,
            name="Dataset 3",
            description="Dataset 3 Geotiff",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.RASTER_CONT_GEOTIFF,
            srid=26913,
            items=[os.path.join(model_root / "geotiff", x) for x in os.listdir(model_root / "geotiff")],
            relative_to=model_root / "geotiff",
        )
        dataset4 = Dataset.new(
            session=session,
            name="Dataset 4",
            description="Dataset 4 Ascii TS",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.RASTER_CONT_ASCII_TIMESERIES,
            srid=26913,
            items=[os.path.join(model_root / "ascii_ts", x) for x in os.listdir(model_root / "ascii_ts")],
            relative_to=model_root / "ascii_ts",
        )
        dataset5 = Dataset.new(
            session=session,
            name="Dataset 5",
            description="Dataset 5 Geotiff TS",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.RASTER_CONT_GEOTIFF_TIMESERIES,
            srid=26913,
            items=[os.path.join(model_root / "geotiff_ts", x) for x in os.listdir(model_root / "geotiff_ts")],
            relative_to=model_root / "geotiff_ts",
        )
        dataset6 = Dataset.new(
            session=session,
            name="Dataset 6",
            description="Dataset 6 World Image",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.TRIBS_NODE_LIST,
            items=[os.path.join(model_root / "shape", x) for x in os.listdir(model_root / "shape")],
            relative_to=model_root / "shape",
        )
        dataset7 = Dataset.new(
            session=session,
            name="Dataset 7",
            description="Dataset 6 tRIBS Tin",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.TRIBS_TIN,
            srid=26913,
            items=[os.path.join(model_root / "tin", x) for x in os.listdir(model_root / "tin")],
            relative_to=model_root / "tin",
        )
        dataset8 = Dataset.new(
            session=session,
            name="Dataset 8",
            description="Dataset 8 compound",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.TRIBS_GRID_DATA,
            srid=26913,
            items=[os.path.join(model_root / "compound", x) for x in os.listdir(model_root / "compound")],
            relative_to=model_root / "compound",
        )
    yield project
    session.delete(dataset1)
    session.delete(dataset2)
    session.delete(dataset3)
    session.delete(dataset4)
    session.delete(dataset5)
    session.delete(dataset6)
    session.delete(dataset7)
    session.delete(dataset8)
    session.commit()


@pytest.fixture(scope="function")
def geotiff_timesereies_dataset(project_with_fdb, files_dir):
    """
    Create a dataset with a file database.
    """
    project = project_with_fdb
    session = object_session(project)
    model_root = files_dir / "spatial_manager" / "layers"
    with warnings.catch_warnings():
        dataset = Dataset.new(
            session=session,
            name="Dataset",
            description="Dataset Geotiff TS",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.RASTER_CONT_GEOTIFF_TIMESERIES,
            srid=26913,
            items=[os.path.join(model_root / "geotiff_ts", x) for x in os.listdir(model_root / "geotiff_ts")],
            relative_to=model_root / "geotiff_ts",
        )
    yield dataset
    session.delete(dataset)
    session.commit()


@pytest.fixture(scope="function")
def geotiff_timesereies_dataset_no_hours(project_with_fdb, files_dir):
    """
    Create a dataset with a file database.
    """
    project = project_with_fdb
    session = object_session(project)
    model_root = files_dir / 'spatial_manager' / 'layers'
    with warnings.catch_warnings():
        dataset = Dataset.new(
            session=session,
            name='Dataset',
            description='Dataset Geotiff TS No Hours',
            created_by='_staff',
            project=project,
            dataset_type=DatasetTypes.RASTER_CONT_GEOTIFF_TIMESERIES,
            srid=26913,
            items=[
                os.path.join(model_root / 'geotiff_ts_no_hours', x)
                for x in os.listdir(model_root / 'geotiff_ts_no_hours')
            ],
            relative_to=model_root / 'geotiff_ts_no_hours',
        )
    yield dataset
    session.delete(dataset)
    session.commit()


@pytest.fixture(scope="function")
def tin_dataset(project_with_fdb, files_dir):
    """
    Create a dataset with a file database.
    """
    project = project_with_fdb
    session = object_session(project)
    model_root = files_dir / "spatial_manager" / "layers"
    with warnings.catch_warnings():
        dataset = Dataset.new(
            session=session,
            name="Dataset",
            description="Dataset Tin",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.TRIBS_TIN,
            srid=26913,
            items=[os.path.join(model_root / "tin", x) for x in os.listdir(model_root / "tin")],
            relative_to=model_root / "tin",
        )
    yield dataset
    session.delete(dataset)
    session.commit()


@pytest.fixture(scope="function")
def tin_dataset_empty(project_with_fdb, files_dir):
    """
    Create a dataset with a file database.
    """
    project = project_with_fdb
    session = object_session(project)
    model_root = files_dir / "spatial_manager" / "layers"
    with warnings.catch_warnings():
        dataset = Dataset.new(
            session=session,
            name="Dataset",
            description="Dataset Tin No Nodes",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.TRIBS_TIN,
            srid=26913,
            items=[os.path.join(model_root / "tin_no_nodes", x) for x in os.listdir(model_root / "tin_no_nodes")],
            relative_to=model_root / "tin",
        )
    yield dataset
    session.delete(dataset)
    session.commit()


@pytest.fixture(scope="function")
def tin_output_dataset(project_with_fdb, files_dir):
    """
    Create a dataset with a file database.
    """
    project = project_with_fdb
    session = object_session(project)
    model_root = files_dir / "spatial_manager" / "layers"
    with warnings.catch_warnings():
        dataset = Dataset.new(
            session=session,
            name="Dataset",
            description="Dataset Tin Output TD",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.TRIBS_OUT_TIME_DYNAMIC,
            srid=26913,
            items=[os.path.join(model_root / "tin" / "output", x) for x in os.listdir(model_root / "tin" / "output")],
            relative_to=model_root / "tin" / "output",
        )
    yield dataset
    session.delete(dataset)
    session.commit()


@pytest.fixture(scope="function")
def time_dynamic_dataset(project_with_fdb, files_dir, scenario_with_input_file):
    project = project_with_fdb
    session = object_session(project)
    model_root = files_dir / "spatial_manager" / "layers"
    dataset = Dataset.new(
        name="Test Dataset",
        description="Test Dataset Description",
        created_by="_staff",
        project=project_with_fdb,
        session=session,
        dataset_type=DatasetTypes.TRIBS_OUT_TIME_DYNAMIC,
        srid=26913,
        items=[os.path.join(model_root / "time_dynamic", x) for x in os.listdir(model_root / "time_dynamic")],
        relative_to=model_root / "time_dynamic",
    )
    scenario_with_input_file.link_dataset(dataset, card="Test Card")  # Link the dataset to the scenario
    yield dataset
    session.delete(dataset)
    session.commit()


@pytest.fixture(scope="function")
def time_integrated_dataset(project_with_fdb, files_dir, scenario_with_input_file):
    project = project_with_fdb
    session = object_session(project)
    model_root = files_dir / "spatial_manager" / "layers"
    dataset = Dataset.new(
        name="Test Dataset",
        description="Test Dataset Description",
        created_by="_staff",
        project=project_with_fdb,
        session=session,
        dataset_type=DatasetTypes.TRIBS_OUT_TIME_DYNAMIC,
        srid=26913,
        items=[os.path.join(model_root / "time_integrated", x) for x in os.listdir(model_root / "time_integrated")],
        relative_to=model_root / "time_integrated",
    )
    scenario_with_input_file.link_dataset(dataset, card="Test Card")  # Link the dataset to the scenario
    yield dataset
    session.delete(dataset)
    session.commit()


@pytest.fixture(scope="function")
def node_file_dataset(project_with_fdb, files_dir):
    """
    Create a project with datasets.
    """
    project = project_with_fdb
    session = object_session(project)
    model_root = files_dir / "spatial_manager" / "layers"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        dataset = Dataset.new(
            session=session,
            name="Node File",
            description="Node File",
            created_by="_staff",
            project=project,
            dataset_type=DatasetTypes.TRIBS_INPUT_FILE_JSON,
            srid=26913,
            items=[os.path.join(model_root / "node_files", x) for x in os.listdir(model_root / "node_files")],
            relative_to=model_root / "node_files",
        )
    yield dataset
    session.delete(dataset)
    session.commit()
