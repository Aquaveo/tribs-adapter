#!/opt/tethys-python
"""
********************************************************************************
* Name: run_nldas.py
* Author: nswain
* Created On: December 28, 2023
* Copyright: (c) Aquaveo 2023
********************************************************************************
"""
import os
import tempfile
import requests
from urllib.request import urlretrieve

import pandas as pd
import pygeoutils as hgu
import rioxarray  # noqa: F401
from shapely import Polygon
import xarray as xr

from tethys_dataset_services.engines.geoserver_engine import GeoServerSpatialDatasetEngine
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tethysext.atcore.utilities import parse_url
from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.resources import Dataset
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager

from pytRIBS.classes import Project, Met


def _get_nldas_elevation(dir_name):
    """
    Downloads a NetCDF file of the NLDAS elevation grid and returns it as an xarray DataSet.

    :param int epsg: The EPSG code for the desired projection of the output data.

    :returns: The processed elevation data clipped to the watershed extent and reprojected.
    :rtype: xarray.Dataset
    """
    url = "https://ldas.gsfc.nasa.gov/sites/default/files/ldas/nldas/NLDAS_elevation.nc4"

    try:
        # Condor workaround:
        # Use urlretrieve, write to a file, and open the dataset from the file
        # (using response.content sometimes works, usually locally, but not always in tethys)
        elevation_filename = os.path.join(dir_name, 'NLDAS_elevation.nc4')
        urlretrieve(url, elevation_filename)

        with xr.open_dataset(elevation_filename, engine='netcdf4') as ds:
            dataset = ds.load()  # Load the dataset into memory

        # Drop unnecessary variables
        if 'time_bnds' in dataset.variables:
            dataset = dataset.drop_vars('time_bnds')

        # Write the CRS to the dataset
        dataset = dataset.rio.write_crs(32662)  # EPSG code 32662 for Equidistant Cylindrical projection, default
        dataset = hgu.xd_write_crs(dataset, 4326)  # Add CRS to nldas elevation passed in
        return dataset
    except requests.exceptions.RequestException as e:
        print(f"Error downloading NLDAS elevation file: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def _save_dataset(
    workflow,
    resource,
    resource_db_session,
    items,
    dataset_type,
    dataset_type_str,
    name,
    description,
    display_name,
    epsg=None
):
    print(f'Creating {dataset_type_str} dataset for items {items}...')
    tribs_collection = resource.file_database_client.new_collection(
        items=items,
        meta={
            'dataset_id': str(workflow.id),
            'dataset_type': dataset_type_str,
            'description': description,
            'display_name': display_name,
        },
        relative_to='',
    )
    tribs_dataset = Dataset.new(
        name=name,
        description=description,
        created_by=resource.created_by,
        project=resource,
        dataset_type=dataset_type,
        srid=epsg,
        organizations=resource.organizations,
        items=items,
        session=resource_db_session,
    )
    tribs_collection.dataset = tribs_dataset
    resource.file_database.collections.append(tribs_collection.instance)
    return tribs_dataset


@workflow_step_job
def main(
    resource_db_session, model_db_session, resource, workflow, step, gs_private_url, gs_public_url, resource_class,
    workflow_class, params_json, params_file, cmd_args, extra_args
):
    # ==================================================================================================================
    print("\n\nRun NLDAS...\n\n")

    # 1. Set up the project
    tmp_files_dir = tempfile.TemporaryDirectory(prefix='srp_nldas_')
    dir = tmp_files_dir.name
    epsg = 4326  # WGS84

    project_name = 'example'
    proj = Project(dir, name=project_name, epsg=epsg)
    met = Met(meta=proj.meta)
    met.hydrometbasename['value'] = project_name
    # There will be only 1 mdf file because we are using the centroid only
    met_mdf_path = f"{dir}/{proj.directories['met_meteor']}/met_{project_name}_1.mdf"
    met_sdf_path = f"{dir}/{proj.directories['met_meteor']}/met_{project_name}.sdf"
    precip_mdf_path = f"{dir}/{proj.directories['met_precip']}/precip_{project_name}_1.mdf"
    precip_sdf_path = f"{dir}/{proj.directories['met_precip']}/precip_{project_name}.sdf"
    met.hydrometstations['value'] = met_sdf_path
    met.gaugestations['value'] = precip_sdf_path

    # 2. Get the dates specified on the form
    print('\nValidating entered times....\n')
    timestamp_options = params_json['Select NLDAS Timestep Options']
    start_time_str = timestamp_options['parameters']['form-values']['nldas_start_time']
    end_time_str = timestamp_options['parameters']['form-values']['nldas_end_time']
    start_time = pd.to_datetime(start_time_str)
    end_time = pd.to_datetime(end_time_str)

    # 3. Get the watershed centroids
    print('\nGetting watershed features....')
    sw_features = params_json['Select Watershed']['parameters']['geometry']['features']
    geo = sw_features[0]['geometry']
    watershed = Polygon([tuple(cur_l) for cur_l in geo['coordinates'][0]])

    # 4. Get the elevation for the centroid
    print('\nRunning NLDAS data retrieval....')
    lat, lon, _gmt = met.polygon_centroid_to_geographic(watershed)
    ds_elev = _get_nldas_elevation(dir)
    elev = float(ds_elev.NLDAS_elev.sel(lon=lon, lat=lat, method='nearest').values)

    # 5. Run met workflow
    # Write the .netrc file for Earthdata Login authentication
    # (pytRIBS uses the .netrc file for authentication when downloading NLDAS data from NASA servers)
    username, password = os.getenv('EARTHDATA_USERNAME'), os.getenv('EARTHDATA_PASSWORD')
    if not username:
        raise ValueError('EARTHDATA_USERNAME not found. Set EARTHDATA_USERNAME in the environment variables.')
    if not password:
        raise ValueError('EARTHDATA_PASSWORD not found. Set EARTHDATA_PASSWORD in the environment variables.')

    NETRC_PATH = os.path.expanduser('~/.netrc')
    try:
        with open(NETRC_PATH, 'w') as f:
            f.write(f'machine urs.earthdata.nasa.gov login {username} password {password}')
        os.chmod(NETRC_PATH, 0o600)  # Set permissions to read/write for user only
        met.run_met_workflow(watershed, start_time, end_time, elev=elev)
    finally:
        if os.path.exists(NETRC_PATH):
            os.remove(NETRC_PATH)

    # 6. Save the datasets for the Precipitation and Weather files (MDF and SDF)
    precip_dataset = _save_dataset(
        workflow,
        resource,
        resource_db_session,
        items=[precip_mdf_path, precip_sdf_path],
        dataset_type=DatasetTypes.TRIBS_SDF_RAIN_GAUGE,
        dataset_type_str='TRIBS_SDF_RAIN_GAUGE',
        name='SDF Rainfall Stations',
        description=f'Rainfall station SDF and MDF file for workflow {workflow.name}',
        display_name='SDF Rainfall Stations',
        epsg=epsg
    )
    weather_dataset = _save_dataset(
        workflow,
        resource,
        resource_db_session,
        items=[met_mdf_path, met_sdf_path],
        dataset_type=DatasetTypes.TRIBS_SDF_HYDROMET_STATION,
        dataset_type_str='TRIBS_SDF_HYDROMET_STATION',
        name='SDF Weather Station',
        description=f'Weather station SDF and MDF files for workflow {workflow.name}',
        display_name='SDF Weather Stations',
        epsg=epsg
    )

    # 7. Generate visualization for datasets
    private_url = parse_url(gs_private_url)
    public_url = parse_url(gs_public_url)
    geoserver_engine = GeoServerSpatialDatasetEngine(
        endpoint=private_url.endpoint,
        username=private_url.username,
        password=private_url.password,
        public_endpoint=public_url.endpoint,
    )
    spatial_manager = TribsSpatialManager(geoserver_engine)
    precip_dataset.generate_visualization(session=resource_db_session, spatial_manager=spatial_manager)
    weather_dataset.generate_visualization(session=resource_db_session, spatial_manager=spatial_manager)

    print('\n\n\n\nRan NLDAS job Successfully\n\n')
