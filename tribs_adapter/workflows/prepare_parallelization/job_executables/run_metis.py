#!/opt/tethys-python
"""
********************************************************************************
* Name: run_metis.py
* Author: Yue Sun
* Created On: Aug 6, 2025
* Copyright: (c) Aquaveo 2025
********************************************************************************
"""
import os
import tempfile
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.validation import make_valid

import xms.tool_tribs.tribs.run_meshbuilder_and_metis_tool as rmm
from xms.tool.utilities.file_utils import current_test_folder
from tethysext.atcore.utilities import parse_url
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tethys_dataset_services.engines.geoserver_engine import (
    GeoServerSpatialDatasetEngine,
)
from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.resources.dataset import Dataset
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager


def voronoi_to_shapefile(voronoi_path, reach_file_path, shp_path, epsg=32613, nodata_val=-9999):
    """
    Converts a tRIBS Voronoi polygon text file into an ESRI ASCII grid.

    This function is specifically designed to parse the format where each
    record starts with a space-delimited attribute line, followed by
    comma-delimited vertex lines, and terminated by 'END'.

    Parameters
    ----------
    voronoi_path: str
        Path to the Voronoi text file.
    reach_file_path: str
        Path to the reach file which provides the information of processor_id to each polygons
    shp_path: str
        Output path for the shape file (e.g., 'output.shp').
    epsg: int
        EPSG code for the coordinate reference system.
        Default is UTM Zone 13N (EPSG:32613).
    nodata_val: int
        NODATA_value for the output ASCII grid
    """

    polygons, poly_ids, reach_ids = [], [], []
    current_coords = []
    current_id, current_reach = None, None

    with open(voronoi_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip empty lines and comments

            # If we see 'END', the current polygon is complete.
            if line == "END":
                if current_coords and current_id is not None:
                    # A valid polygon requires at least 3 vertices
                    if len(current_coords) >= 3:
                        polygons.append(Polygon(current_coords))
                        poly_ids.append(current_id)
                        reach_ids.append(current_reach)
                    else:
                        print(f"Skipping polygon {current_id} with < 3 vertices.")

                # Reset for the next polygon
                current_coords = []
                current_id = None
                current_reach = None
            # If current_id is None, this must be the attribute header line for a new polygon
            elif current_id is None:
                parts = line.split()
                try:
                    # From the header: CellID is the 1st value (index 0)
                    current_id = int(parts[0])
                    # From the header: Reach is the 6th value (index 5)
                    current_reach = int(parts[5])
                except (IndexError, ValueError) as e:
                    print(f"Warning: Could not parse attribute line: '{line}'. Error: {e}. Skipping.")
                    # Set a dummy id to consume vertex lines until 'END'
                    current_id = -1
            # Otherwise, this is a vertex line for the current polygon
            # Handle vertex lines even for records with bad headers
            elif current_id != -1:
                try:
                    # Vertex coordinates are comma-separated
                    x_str, y_str = line.split(',')
                    current_coords.append((float(x_str), float(y_str)))
                except ValueError:
                    print(f"Skipping malformed vertex line for polygon {current_id}: {line}")

    # Create the GeoDataFrame
    gdf = gpd.GeoDataFrame({"id": poly_ids, "reach_id": reach_ids, "geometry": polygons}, crs=f"EPSG:{epsg}")
    df_reach = pd.read_csv(reach_file_path, delimiter=' ', names=['proc_id', 'reach_id'])
    gdf = gdf.merge(df_reach)

    # Define raster resolution
    def repair_geometry(geom):
        # Try make_valid first (shapely ≥ 2.0)
        fixed = make_valid(geom)
        if fixed.is_valid:
            return fixed
        # If still invalid, try buffer(0) as fallback
        fixed = geom.buffer(0)
        if fixed.is_valid:
            return fixed
        # If still invalid, return None (we can drop later)
        return None

    gdf['geometry'] = gdf['geometry'].apply(repair_geometry)
    gdf = gdf[gdf["geometry"].notnull()]
    gdf = gdf.dissolve(by='proc_id').drop('reach_id', axis=1)  # the result is not perfect

    try:
        gdf.to_file(shp_path, driver='ESRI Shapefile')
        print(f"✅ Shapefile successfully created at: {shp_path}")
        print(f"   - Polygons processed: {len(gdf)}")
    except Exception as e:
        print(f"❌ Error saving shapefile: {e}")


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
    cmd_args,
    extra_args,
):
    # don't use os.getcwd(), the path is too long and be truncated in xmltool
    # then cause the FileNotFound error
    temp_dir = tempfile.TemporaryDirectory(prefix='srp_parallel_')
    if extra_args and len(extra_args) == 4:
        tin_dataset_name, tin_dataset_id, mode, num_processor = extra_args
        if mode == 'Surface':
            partition_option = rmm.MeshbuilderAndMetisRunner.OPT_SF
            opt_name = 'flow'
        else:
            partition_option = rmm.MeshbuilderAndMetisRunner.OPT_SSF
            opt_name = 'nconn'

        tin_dataset = resource_db_session.query(Dataset).get(tin_dataset_id)
        if not tin_dataset:
            raise RuntimeError(f"Dataset with id {tin_dataset_id} not found.")
        srid = tin_dataset.srid

        client = tin_dataset.file_collection_client
        points_file_path = None
        file_exts = ['nodes', 'edges', 'z', 'tri', 'points']
        for file in client.files:
            ext = file.split('.')[-1]
            if ext in file_exts:
                client.export_item(item=file, target=temp_dir.name)
                if ext == 'points':
                    points_file_path = os.path.join(temp_dir.name, file)

        # TODO .points file won't be used in the newer version
        if not points_file_path:
            raise Exception("The TIN dataset doesn't have a .points file! ")

        tool = rmm.RunMeshbuilderAndMetisTool()
        arguments = tool.initial_arguments()
        arguments[rmm.ARG_POINTS_FILE].value = points_file_path
        arguments[rmm.ARG_NUM_PROCESSOR_THREADS].value = num_processor
        arguments[rmm.ARG_PARTITIONING_OPTION].value = partition_option
        tool.set_gui_data_folder(temp_dir.name)
        current_test_folder(temp_dir.name)
        tool.run_tool(arguments)

        # Get plot data
        meshb_path = f'{temp_dir.name}/{tin_dataset_name}_connectivity.meshb'
        reach_path = f'{temp_dir.name}/{tin_dataset_name}_{opt_name}_{num_processor}nodes.reach'
        df_meshb = pd.read_csv(
            meshb_path, skiprows=[0, 1], delimiter=' ', usecols=[0, 1], names=['reach_id', 'point_count']
        )
        df_reach = pd.read_csv(reach_path, delimiter=' ', names=['proc_id', 'reach_id'])
        df = df_reach.merge(df_meshb)
        df = df.groupby(by='proc_id').sum().reset_index()[['proc_id', 'point_count']]
        plot_path = f'{temp_dir.name}/{tin_dataset_name}_{opt_name}_{num_processor}procs_plot.csv'
        df.to_csv(plot_path, index=False)

        # Get map data
        map_output_dir = f'{temp_dir.name}/map_out'
        os.mkdir(map_output_dir)
        voronoi_path = os.path.join(temp_dir.name, 'voronoi_geo.meshb')
        shp_path = os.path.join(map_output_dir, f'{tin_dataset_name}_{opt_name}_{num_processor}procs.shp')
        voronoi_to_shapefile(voronoi_path, reach_path, shp_path)
        shp_files = [os.path.join(map_output_dir, file) for file in os.listdir(map_output_dir)]

        output_files = [meshb_path, reach_path, plot_path, voronoi_path] + shp_files

        dataset = Dataset.new(
            name=f'{tin_dataset_name}_{opt_name}_{num_processor}procs.metis',
            description='Files generated from RunMeshbuilderAndMetisTool',
            created_by=resource.created_by,
            project=resource,
            dataset_type=DatasetTypes.TRIBS_METIS,
            organizations=resource.organizations,
            items=output_files,
            session=resource_db_session,
            srid=srid
        )

        url = parse_url(gs_private_url)
        url_public = parse_url(gs_public_url)
        geoserver_engine = GeoServerSpatialDatasetEngine(
            endpoint=url.endpoint,
            username=url.username,
            password=url.password,
            public_endpoint=url_public.endpoint,
        )
        spatial_manager = TribsSpatialManager(geoserver_engine)
        dataset.generate_visualization(session=resource_db_session, spatial_manager=spatial_manager)

        dataset.set_attribute('TIN Dataset', {'id': tin_dataset_id, 'name': tin_dataset_name})
        dataset.set_attribute('Model Parameters', {'mode': mode, 'num_processor': num_processor})
        workflow.set_attribute('metis_dataset_id', str(dataset.id))
        resource_db_session.commit()
        print("Run METIS is done!")
