#!/opt/tethys-python
"""
********************************************************************************
* Name: run_rosetta3.py
* Author: nswain, ejones
* Created On: February 12, 2024
* Copyright: (c) Aquaveo 2024
********************************************************************************
"""
import os
import tempfile
from pytRIBS.classes import Soil

from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.resources.dataset import Dataset
from tethysext.atcore.utilities import parse_url
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from tethys_dataset_services.engines.geoserver_engine import GeoServerSpatialDatasetEngine
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job


@workflow_step_job
def main(
    resource_db_session,
    model_db_session,
    resource,
    workflow,
    step,
    gs_private_url,
    gs_public_url,
    resource_class,
    workflow_class,
    params_json,
    params_file,
    cmd_args=None,
    extra_args=None
):
    print('Running Rosetta3...')
    # Verify input and initialize
    if extra_args and len(extra_args) >= 2:
        output_name, dataset_id = extra_args
        print(f'Output Dataset Name: {output_name}, Dataset ID: {dataset_id}')
        dataset = resource_db_session.query(Dataset).get(dataset_id)
        srid = dataset.srid

        if not dataset:
            raise RuntimeError(f'Dataset with id {dataset_id} not found.')

        client = dataset.file_collection_client

        # Create tmp folder
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as temp_dir:
            # Copy data to tmp folder client.export() / export to cwd
            client.export(temp_dir)

            soil = Soil()

            # We are going to get the current working directory
            # and we are going to create a data folder, make it the current working
            # directory, and do our work. We will reset the cwd at the end.
            # We need to copy to a data folder to keep our jsons separate from
            # Tethys and Condor files and we need to change the cwd for the
            # relative paths of our json files to work in PytRIBS.
            cwd = os.getcwd()

            print(f'data_folder exists: {os.path.exists(temp_dir)}')
            try:
                os.chdir(temp_dir)

                # 1. Generate soil map & .sdt file
                # list of dictionaries for estimating soil texture
                grids = [{
                    'type': 'sand',
                    'path': 'sand_0-5cm_mean_filled.tif'
                }, {
                    'type': 'clay',
                    'path': 'clay_0-5cm_mean_filled.tif'
                }]

                soil_classes_path = os.path.join(temp_dir, 'soil_classes.soi')
                classes = soil.create_soil_map(grids, output=soil_classes_path)

                url = parse_url(gs_private_url)
                public_url = parse_url(gs_public_url)
                geoserver_engine = GeoServerSpatialDatasetEngine(
                    endpoint=url.endpoint,
                    username=url.username,
                    password=url.password,
                    public_endpoint=public_url.endpoint,
                )
                spatial_manager = TribsSpatialManager(geoserver_engine)
                lu_dataset = Dataset.new(
                    session=resource_db_session,
                    name=f'{output_name}.soi',
                    description="Soil classes for the selected area.",
                    created_by=resource.created_by,
                    organizations=resource.organizations,
                    project=resource,
                    dataset_type=DatasetTypes.RASTER_DISC_ASCII,
                    srid=srid,
                    items=[soil_classes_path]
                )
                lu_dataset.generate_visualization(session=resource_db_session, spatial_manager=spatial_manager)
                workflow.set_attribute('lu_dataset_id', str(lu_dataset.id))

                # 2. Generate .sdt file
                soil_table_path = 'soils.sdt'
                soil.write_soil_table(classes, soil_table_path, textures=True)

                soil_table_dataset = Dataset.new(
                    session=resource_db_session,
                    project=resource,
                    dataset_type=DatasetTypes.TRIBS_TABLE_SOIL,
                    items=[soil_table_path],
                    name=f'{output_name}.sdt',
                    description='Soil physical data table.',
                    created_by=resource.created_by,
                    organizations=resource.organizations
                )
                soil_table_dataset_id = str(soil_table_dataset.id)
                workflow.set_attribute('soil_table_dataset_id', soil_table_dataset_id)
                step.set_attribute('soil_table_dataset_id', soil_table_dataset_id)
            except Exception as e:
                print(f'Exception: {e}')
                import traceback
                traceback.print_exc()

            # Cleanup and end
            os.chdir(cwd)
            print('Completed Rosetta3.')
