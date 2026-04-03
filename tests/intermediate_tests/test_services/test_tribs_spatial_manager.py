import os
from pathlib import Path
import requests
from unittest.mock import MagicMock

import pytest


def test_get_extent_for_project(tsm, minimal_project):
    """Test get_extent_for_project."""
    extent = tsm.get_extent_for_project()
    assert extent == [-124.67, 25.84, -66.95, 49.38]  # CONUS


def test_create_and_delete_all_layers(tsm, project_with_datasets, mock_geoserver_engine, mocker):
    """Test create_all_layers and delete_all_layers."""
    mock_get_extent_for_dataset = mocker.patch(
        'tribs_adapter.services.tribs_spatial_manager.TribsSpatialManager.get_extent_for_dataset',
        return_value=[-107.0, 38.0, -106.0, 39.0]
    )
    mock_get_data_for_files = mocker.patch(
        'tribs_adapter.services.tribs_spatial_manager.TribsSpatialManager.get_data_for_files',
        return_value=([-107.0, 38.0, -106.0, 39.0], [0, 39, -9999])
    )

    srid = 32613
    session = MagicMock()
    tsm.create_all_layers(project_with_datasets, srid, session=session, reload_config=False)
    assert mock_geoserver_engine.create_shapefile_resource.call_count == 1
    assert mock_geoserver_engine.create_coverage_layer.call_count == 6
    assert mock_geoserver_engine.enable_time_dimension.call_count == 4
    assert mock_get_extent_for_dataset.call_count == 5
    assert mock_get_data_for_files.call_count == 7
    tsm.delete_all_layers(project_with_datasets)
    assert mock_geoserver_engine.delete_layer.call_count == 1
    assert mock_geoserver_engine.delete_coverage_store.call_count == 6


def test_create_workspace(tsm, mock_geoserver_engine):
    """Test create_workspace."""
    tsm.create_workspace()
    mock_geoserver_engine.create_workspace.assert_called_once_with(tsm.WORKSPACE, tsm.URI)


def test_create_and_delete_all_styles(tsm, mock_geoserver_engine):
    """Test create_all_styles and delete_all_styles."""
    tsm.create_all_styles(overwrite=True)
    sld = str(
        Path(__file__).parent.parent.parent.parent / 'tribs_adapter' / 'templates' / 'sld_templates' /
        'parallel_partition.sld'
    )
    mock_geoserver_engine.create_style.assert_called_with(
        style_id='tribs:parallel_partition', sld_template=sld, sld_context={}, overwrite=True
    )
    assert mock_geoserver_engine.create_style.call_count == 8
    tsm.delete_all_styles()
    assert mock_geoserver_engine.delete_style.call_count == 7


def test_create_raster_timeseries_geotiff_timeout(tsm, mock_geoserver_engine, geotiff_timesereies_dataset, mocker):
    """Test create_raster_timeseries_geotiff_layer with a timeout."""
    mock_geoserver_engine.create_coverage_layer.side_effect = requests.RequestException('exception')
    mocker.patch('os.path.splitext', return_value=['p12345678', '.tif'])
    files = os.listdir(geotiff_timesereies_dataset.file_collection_client.path)
    fc = geotiff_timesereies_dataset.file_collection_client
    with pytest.raises(requests.RequestException):
        tsm.create_raster_timeseries_geotiff_layer(
            geotiff_timesereies_dataset,
            4326,
            raster_map_files=[os.path.join(fc.path, f) for f in files if not f.endswith('.json')]
        )


def test_projection_string_function(tsm, minimal_project):
    """Test the _get_projection_string function."""
    string1 = tsm._get_projection_string(minimal_project, 4326, proj_format=tsm.PRO_WKT)
    assert string1 == (
        'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,'
        'AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,' +
        'AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY' +
        '["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
    )

    with pytest.raises(ValueError):
        tsm._get_projection_string(minimal_project, 4326, proj_format='invalid')

    string2 = tsm._get_projection_string(minimal_project, 4326, proj_format=tsm.PRO_PROJ4)
    assert string2 == '+proj=longlat +datum=WGS84 +no_defs '


def test_create_time_dynamic_raster_layer(tsm, time_dynamic_dataset, node_file_dataset):
    tsm.create_tribs_tin_layer(node_file_dataset, 32613, time_dynamic_dataset)

    dataset_path = time_dynamic_dataset.file_collection_client.path
    assert os.path.exists(os.path.join(dataset_path, 'gltf'))
    assert len(os.listdir(os.path.join(dataset_path, 'gltf'))) == 224

    tsm.delete_tribs_tin_layer(time_dynamic_dataset)
    assert not os.path.exists(os.path.join(dataset_path, 'gltf'))


def test_create_time_integrated_raster_layer(tsm, time_integrated_dataset, node_file_dataset):
    tsm.create_tribs_tin_layer(node_file_dataset, 32613, time_integrated_dataset)

    dataset_path = time_integrated_dataset.file_collection_client.path
    assert os.path.exists(os.path.join(dataset_path, 'gltf'))
    assert len(os.listdir(os.path.join(dataset_path, 'gltf'))) == 228

    tsm.delete_tribs_tin_layer(time_integrated_dataset)
    assert not os.path.exists(os.path.join(dataset_path, 'gltf'))


def test_create_tribs_tin_layer(tsm, tin_dataset, tin_dataset_empty, tin_output_dataset):
    # Ensure empty dataset throws value error
    with pytest.raises(ValueError):
        tsm.create_tribs_tin_layer(tin_dataset_empty, 32613)

    tsm.delete_tribs_tin_layer(tin_dataset)

    tin_dataset_path = tin_dataset.file_collection_client.path
    tin_output_dataset_path = tin_output_dataset.file_collection_client.path
    tsm.create_tribs_tin_layer(tin_dataset, 32613)
    assert os.path.exists(os.path.join(tin_dataset_path, 'gltf'))
    assert len(os.listdir(os.path.join(tin_dataset_path, 'gltf'))) == 2

    tsm.create_tribs_tin_layer(tin_dataset, 32613, output_dataset=tin_output_dataset, output_variables=['S', 'Z'])
    assert os.path.exists(os.path.join(tin_output_dataset_path, 'gltf'))
    assert len(os.listdir(os.path.join(tin_output_dataset_path, 'gltf'))) == 20

    # Check again to make sure it doesn't add MORE files
    tsm.create_tribs_tin_layer(tin_dataset, 32613, output_dataset=tin_output_dataset, output_variables=['S', 'Z'])
    assert os.path.exists(os.path.join(tin_output_dataset_path, 'gltf'))
    assert len(os.listdir(os.path.join(tin_output_dataset_path, 'gltf'))) == 20

    tsm.delete_tribs_tin_layer(tin_output_dataset)
    assert not os.path.exists(os.path.join(tin_output_dataset_path, 'gltf'))
