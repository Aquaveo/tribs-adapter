#!/opt/tethys-python
"""
********************************************************************************
* Name: run_bulk_soil_data_retrieval.py
* Author: nswain, ejones
* Created On: February 12, 2024
* Copyright: (c) Aquaveo 2024
********************************************************************************
"""
import sys
import pathlib
from pytRIBS.classes import Soil
from osgeo import gdal, ogr, osr

from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.common.soil_data_types import depths, soil_vars
from tribs_adapter.workflows.utilities import get_gmt_offset
from tribs_adapter.resources.dataset import Dataset
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from tethys_dataset_services.engines.geoserver_engine import GeoServerSpatialDatasetEngine
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tethysext.atcore.utilities import parse_url


def reproject_point(x, y, out_srid, in_srid=4326):
    """
    Re-project 2D point.

    Args:
        x(float): x coordinate / longitude.
        y(float): y coordinate / latitude.
        out_srid(int): Spatial Reference ID of the desired projection to transform the given coordinates.
        in_srid(int): Spatial Reference ID of the current projection of the given coordinates.

    Returns:
        tuple<float, float>: reprojected coordinates (i.e.: x coordinate / longitude, y coordinate / latitude).
    """
    source = osr.SpatialReference()
    source.ImportFromEPSG(in_srid)

    target = osr.SpatialReference()
    if isinstance(out_srid, str):
        out_srid = int(out_srid)
    target.ImportFromEPSG(out_srid)

    order_option = gdal.GetConfigOption("OGR_CT_FORCE_TRADITIONAL_GIS_ORDER")
    gdal.SetConfigOption("OGR_CT_FORCE_TRADITIONAL_GIS_ORDER", "YES")
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(x, y)
    point.AssignSpatialReference(source)
    point.TransformTo(target)
    gdal.SetConfigOption("OGR_CT_FORCE_TRADITIONAL_GIS_ORDER", order_option)

    return point.GetX(), point.GetY()


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
    extra_args=None,
):
    print("Retrieving soil bulk data...")
    # Verify input and initialize
    if extra_args and len(extra_args) >= 2:

        # Get the created polygon
        polygon_step = workflow.get_step_by_name("Select Area of Interest")
        polygon_geometry = polygon_step.get_parameter("geometry")

        polygon_index = int(extra_args[1])
        polygon = polygon_geometry.get("features", [])[polygon_index]

        polygon_name = polygon.get("properties", {}).get("polygon_name", f"polygon_{polygon_index + 1}")

        soil = Soil()

        # get largest and smallest x and y values
        geometry = polygon.get("geometry", [])
        x_max = -sys.maxsize
        x_min = sys.maxsize
        y_max = -sys.maxsize
        y_min = sys.maxsize

        # Grab the extent of the polygon
        for coordinate in geometry["coordinates"][0]:
            x = coordinate[0]
            y = coordinate[1]
            x_max = max(x, x_max)
            x_min = min(x, x_min)
            y_max = max(y, y_max)
            y_min = min(y, y_min)
        extent = [x_min, y_min, x_max, y_max]

        lat = (y_max + y_min) / 2
        long = (x_max + x_min) / 2
        gmt = get_gmt_offset(lat, long)

        epsg = 6341

        # Convert the coordinates to UTM and set the bounding box
        x_max_utm, y_max_utm = reproject_point(x_max, y_max, epsg)
        x_min_utm, y_min_utm = reproject_point(x_min, y_min, epsg)

        soil.meta["EPSG"] = str(epsg)

        # x1,y1,x2,y2 of ROI, Region of Interest in UTM
        bbox = [x_min_utm, y_min_utm, x_max_utm, y_max_utm]
        statistics = ["mean"]

        # Download the data (divided by depth to assist against timeout issues)
        all_files = []
        print(f"Start downloading Soil Data for depths: {depths}")
        files = soil.get_soil_grids(bbox, depths, soil_vars, statistics)
        files = [f"sg250/{f}" for f in files]
        all_files.extend(files)

        print("Fill nodata cells.")

        # Fills the nodata cells
        soil._fillnodata(all_files)
        filled_files = []
        for file in all_files:
            file_path = pathlib.Path(file)
            filled_files.append(f'{file_path.with_suffix("")}_filled{file_path.suffix}')

        print("write lattitude and longitude data.")

        lat_long_file = "sg250/lat_long.txt"
        with open(lat_long_file, "w") as f:
            f.write(f"{lat},{long},{gmt}\n")
        filled_files.append(lat_long_file)

        # Add directly to the project as a dataset
        soil_dataset = Dataset.new(
            session=resource_db_session,
            name=polygon_name,
            description="Soil physical data retrieved from SoilGrids.",
            created_by=resource.created_by,
            organizations=resource.organizations,
            project=resource,
            dataset_type=DatasetTypes.SOILGRID_PHYSICAL_SOIL_DATA,
            srid=epsg,
            items=filled_files
        )
        soil_dataset.set_attribute("extent", {"extent": extent})

        # Generate Viz
        url = parse_url(gs_private_url)
        public_url = parse_url(gs_public_url)
        geoserver_engine = GeoServerSpatialDatasetEngine(
            endpoint=url.endpoint,
            username=url.username,
            password=url.password,
            public_endpoint=public_url.endpoint,
        )
        spatial_manager = TribsSpatialManager(geoserver_engine)
        soil_dataset.generate_visualization(session=resource_db_session, spatial_manager=spatial_manager)
    else:
        print("No extra arguments (polygon information) provided.")

    print("Completed Soil Bulk Data Retrieval.")
