#!/opt/tethys-python
"""
********************************************************************************
* Name: run_generate_tribs_files.py
* Author: ejones
* Created On: February 12, 2024
* Copyright: (c) Aquaveo 2024
********************************************************************************
"""
import os
import rasterio
import tempfile
from pytRIBS.classes import Soil
from pyproj import Transformer
from datetime import datetime

from tribs_adapter.resources.dataset import Dataset
from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.common.soil_data_types import depths, soil_vars, tribs_vars
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from tribs_adapter.workflows.utilities import get_gmt_offset
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tethysext.atcore.utilities import parse_url
from tethys_dataset_services.engines.geoserver_engine import GeoServerSpatialDatasetEngine


def convert_to_float_or_string(value):
    try:
        return float(value)
    except ValueError:
        return value


def write_df_to_soil_data(session, soil_table_dataset_id, dataset_dict):
    """
    Write the pandas DataFrame to the soil data file.
    """
    # Post process the dataset
    soil = Soil()

    dataset = session.query(Dataset).get(soil_table_dataset_id)
    client = dataset.file_collection_client

    soil_table_file = 'soils.sdt'
    file_path = os.path.join(client.path, soil_table_file)
    data = soil.read_soil_table(textures=True, file_path=file_path)

    for row in data:
        textures = dataset_dict['Soil Texture Class']
        for idx in range(len(textures)):
            if textures[idx] == row['Texture']:
                row['As'] = convert_to_float_or_string(dataset_dict['Saturated Anisotropy Ratio (As)'][idx])
                row['Au'] = convert_to_float_or_string(dataset_dict['Unsaturated Anisotropy Ratio (Au)'][idx])
                row['n'] = convert_to_float_or_string(dataset_dict['Porosity (n)'][idx])
                row['ks'] = convert_to_float_or_string(dataset_dict['Volumetric Heat Conductivity (ks) (J/msK)'][idx])
                row['Cs'] = convert_to_float_or_string(dataset_dict['Soil Heat Capacity (Cs) (J/m^3K)'][idx])

    soil.write_soil_table(data, file_path, textures=True)

    return dataset


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
    print(f"[{datetime.now()}] Job starts running ...")

    output_name, dataset_id = extra_args

    # 1. Write Soils table file from dataset
    soil_table_dataset_id = workflow.get_attribute('soil_table_dataset_id')
    enter_texture_parameters_step = workflow.get_step_by_name('Enter Texture Parameters')
    dataset_dict = enter_texture_parameters_step.get_parameter('dataset')
    write_df_to_soil_data(resource_db_session, soil_table_dataset_id, dataset_dict)

    # 2. Generate .asc files for gdf dataset
    dataset = resource_db_session.query(Dataset).get(dataset_id)
    client = dataset.file_collection_client
    temp_dir = tempfile.TemporaryDirectory(dir=os.getcwd(), prefix="gdf_")
    client.export(temp_dir.name)
    cwd = os.getcwd()
    os.chdir(temp_dir.name)

    # 2.1 Generate grids from the input dataset
    soil = Soil()
    for depth in depths:
        grids = []
        for soil_var in soil_vars:
            grids.append({'type': soil_var, 'path': f'{soil_var}_{depth}_mean_filled.tif'})
        out = [f'{trib_var}_{depth}.asc' for trib_var in tribs_vars]
        if '0-5' in depth:
            soil.process_raw_soil(grids, output=out)
        else:
            soil.process_raw_soil(grids, output=out, ks_only=True)

    # 2.2 Generate f.asc from Ks
    ks_depths = [0.0001, 50, 150, 300]
    grid_depth = []
    for i in range(4):
        grid_depth.append({'depth': ks_depths[i], 'path': f'Ks_{depths[i]}.asc'})
    ks_decay_param = 'f'
    soil.compute_ks_decay(grid_depth, output=f'{ks_decay_param}.asc')

    print(f"[{datetime.now()}] Complete processing raw soil data")

    # 2.3 Generate grids from user inputs
    lu_dataset_id = workflow.get_attribute('lu_dataset_id')
    lu_dataset = resource_db_session.query(Dataset).get(lu_dataset_id)
    srid = lu_dataset.srid
    lu_client = lu_dataset.file_collection_client
    for file in lu_client.files:
        if file.endswith('.soi'):
            filepath = os.path.join(lu_client.path, file)
    lu_raster = rasterio.open(filepath)

    # 3. Write the .gdf file
    # Grab the lat, long data
    lat_long_file = 'lat_long.txt'
    if os.path.exists(lat_long_file):
        with open(lat_long_file, 'r') as f:
            line = f.readline()
            lat, long, gmt = map(float, line.split(','))
    else:
        transformer = Transformer.from_crs(f"EPSG:{srid}", "EPSG:4326", always_xy=True)
        long = (lu_raster.bounds.left + lu_raster.bounds.right) / 2
        lat = (lu_raster.bounds.bottom + lu_raster.bounds.top) / 2
        long, lat = transformer.transform(long, lat)
        long, lat = round(long, 2), round(lat, 2)
        gmt = int(get_gmt_offset(lat, long))

    scgrid_vars = ['KS', 'TR', 'TS', 'PB', 'PI', 'FD', 'PO']
    tribs_vars.extend([ks_decay_param, 'theta_s'])  # theta_S (TS) and porosity (PO) are assumed to be the same
    ref_depth = '0-5cm'
    ext = 'asc'
    scgrid_path = 'scgrid.gdf'
    scgrid_files = [scgrid_path]
    with open(scgrid_path, 'w') as file:
        file.write(str(len(scgrid_vars)) + '\n')
        file.write(f"{str(lat)} {str(long)} {str(gmt)}\n")

        for scgrid, prefix in zip(scgrid_vars, tribs_vars):
            if scgrid == 'FD':
                scgrid_files.append(f'{prefix}.{ext}')
                file.write(f"{scgrid} {prefix} {ext}\n")
            else:
                scgrid_files.append(f'{prefix}_{ref_depth}.{ext}')
                file.write(f"{scgrid} {prefix}_{ref_depth} {ext}\n")

    print(f"[{datetime.now()}] Complete generating gdf files")

    # 4. Create a dataset
    scgrid_dataset = Dataset.new(
        session=resource_db_session,
        name=f'{output_name}.gdf',
        description="Soil physical grid data file.",
        created_by=resource.created_by,
        organizations=resource.organizations,
        project=resource,
        dataset_type=DatasetTypes.TRIBS_GRID_DATA,
        srid=srid,
        items=scgrid_files
    )
    url = parse_url(gs_private_url)
    public_url = parse_url(gs_public_url)
    geoserver_engine = GeoServerSpatialDatasetEngine(
        endpoint=url.endpoint,
        username=url.username,
        password=url.password,
        public_endpoint=public_url.endpoint,
    )
    spatial_manager = TribsSpatialManager(geoserver_engine)
    scgrid_dataset.generate_visualization(session=resource_db_session, spatial_manager=spatial_manager)
    print(f"[{datetime.now()}] Complete creating a new dataset")

    temp_dir.cleanup()
    os.chdir(cwd)
