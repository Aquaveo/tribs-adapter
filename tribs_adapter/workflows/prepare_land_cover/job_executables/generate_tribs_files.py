#!/opt/tethys-python
"""
********************************************************************************
* Name: generate_tribs_files.py
* Author: ysun
* Created On: July 28, 2026
* Copyright: (c) Aquaveo 2026
********************************************************************************
"""

import tempfile
import os
import pandas as pd
import numpy as np
import rasterio

from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tribs_adapter.resources.dataset import Dataset
from tribs_adapter.workflows.prepare_land_cover.helpers import (
    write_numpy_array_to_asc_file, get_input_file_path_from_dataset
)

from tethysext.atcore.utilities import parse_url
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from tethys_dataset_services.engines.geoserver_engine import GeoServerSpatialDatasetEngine


@workflow_step_job
def main(
    resource_db_session, model_db_session, resource, workflow, step, gs_private_url, gs_public_url, resource_class,
    workflow_class, params_json, params_file, cmd_args, extra_args
):
    form_values = workflow.get_step_by_name('Select Datasets').get_parameter('form-values')
    selected_dataset = form_values.get('lu_dataset')
    lu_dataset_name, lu_dataset_id = selected_dataset.split(':')
    lu_dataset = resource_db_session.query(Dataset).get(lu_dataset_id)
    output_name = form_values.get('output_name').replace(' ', '_')  # Replace spaces with underscores for file naming

    # 1. Generate .lu file - just convert the input geotiff to .asc and save as a new dataset
    lu_input_path = get_input_file_path_from_dataset(lu_dataset)
    with rasterio.open(lu_input_path) as src:
        lu_array = src.read(1).astype('int32')
        lu_transform = src.transform
        srid = (src.crs and src.crs.to_epsg()) or lu_dataset.srid
        lu_nodata = src.nodata

    if not srid:
        raise ValueError(
            f"Cannot determine SRID for {lu_input_path}: the file has no EPSG code "
            f"and dataset {lu_dataset_name} ({lu_dataset_id}) has no SRID set."
        )

    temp_dir = tempfile.TemporaryDirectory(dir=os.getcwd(), prefix='lu_')
    lu_asc_path = os.path.join(temp_dir.name, 'LU.asc')
    write_numpy_array_to_asc_file(
        path=lu_asc_path,
        array=lu_array,
        crs=f'EPSG:{srid}',
        transform=lu_transform,
        precision=0,  # integer classes
        nodata=lu_nodata
    )

    lu_dataset = Dataset.new(
        session=resource_db_session,
        name=f'{output_name}.lu',
        description=f'.lu file of {output_name}',
        created_by=resource.created_by,
        organizations=resource.organizations,
        project=resource,
        dataset_type=Dataset.DatasetTypes.RASTER_DISC_ASCII,
        srid=srid,
        items=[lu_asc_path]
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
    lu_dataset.generate_visualization(session=resource_db_session, spatial_manager=spatial_manager)

    temp_dir.cleanup()

    # 2. Generate .ldt file - convert the input land use parameters to a .ldt file and save as a new dataset
    temp_dir = tempfile.TemporaryDirectory(dir=os.getcwd(), prefix='ldt_')
    # Get land use parameters
    land_use_params = workflow.get_step_by_name('Enter Land Use Parameters').get_parameter('dataset')
    num_types = len(land_use_params['ID'])
    columns = ["ID", "a", "b1", "P", "S", "K", "b2", "Al", "h", "Kt", "Rs", "V", "LAI", "thetas", "thetat"]
    param_to_col = {
        "ID": "ID",
        "Free Throughfall Coefficient (P)": "P",
        "Canopy Field Capacity (S) (mm)": "S",
        "Drainage Coefficient (K) (mm/hr)": "K",
        "Drainage Exponent (b2) (mm/hr)": "b2",
        "Albedo (Al)": "Al",
        "Vegetation Height (h) (m)": "h",
        "Optical Transmission Coefficient (Kt)": "Kt",
        "Canopy-Average Stomatal Resistance (Rs) (s/m)": "Rs",
        "Vegetation Fraction (V)": "V",
        "Leaf Area Index (LAI)": "LAI",
        "Stress Threshold for Soil Evaporation (thetas)": "thetas",
        "Stress Threshold for Plant Transpiration (thetat)": "thetat"
    }
    ldt_data = {}
    for param, values in land_use_params.items():
        if param in param_to_col:
            column = param_to_col[param]
            ldt_data[column] = values
    df = pd.DataFrame(-9999, index=np.arange(num_types), columns=columns)
    for col in columns:
        if col in ldt_data:
            df[col] = ldt_data[col]

    # Write out the .ldt file
    final_filepath = os.path.join(temp_dir.name, f'{output_name}.ldt')
    with open(final_filepath, 'w') as final_file:
        final_file.write(f"{num_types} {len(columns)}\n")
        df.to_csv(final_file, index=False, header=False, sep=' ')

    Dataset.new(
        session=resource_db_session,
        name=f'{output_name}.ldt',
        description=f'.ldt file of {output_name}',
        created_by=resource.created_by,
        organizations=resource.organizations,
        project=resource,
        dataset_type=Dataset.DatasetTypes.TRIBS_TABLE_LANDUSE,
        items=[final_filepath]
    )

    temp_dir.cleanup()
