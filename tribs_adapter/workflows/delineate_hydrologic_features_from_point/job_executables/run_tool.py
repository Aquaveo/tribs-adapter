#!/opt/tethys-python
"""
********************************************************************************
* Name: workflows/delineate_hydrologic_features/job_executables/post_process.py
* Author: dgallup, ysun
* Created On: Jan 18, 2024
* Copyright: (c) Aquaveo 2024
********************************************************************************
"""
import os
import tempfile
import geopandas as gpd
from osgeo import gdal, osr

from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tethysext.atcore.utilities import parse_url
from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.resources import Dataset
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from tethys_dataset_services.engines.geoserver_engine import GeoServerSpatialDatasetEngine

from xms.tool.utilities.file_utils import current_test_folder


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
    # Create a temp directory to run the tRIBS XMS tool
    tf_dir = tempfile.TemporaryDirectory(prefix="tribs_xmsdhffp_")

    print("\n\n\n***************************************************")
    print("Reading info needed to run xmstool")

    xmstool_step = workflow.get_step_by_name("tRIBS Watershed from Pour Point")

    # 1. Get the info to run XMSTool
    params = xmstool_step.get_parameters()
    form_values = params["form-values"]["value"]["value"]

    # Remove any path or file extensions
    preprocessing_engine = form_values["preprocessing_engine"]
    watersheds_basename = os.path.basename(os.path.splitext(form_values["watershed_boundaries"])[0])
    streamlines_basename = os.path.basename(os.path.splitext(form_values["stream_lines"])[0])

    # Get the datasets and the main file
    input_raster_dataset = resource_db_session.query(Dataset).get(form_values["input_raster"])

    def export_collection_files(dataset, valid_ext=None):
        main_file = None
        for file in dataset.file_collection_client.files:
            if file != "__meta__.json":
                dataset.file_collection_client.export_item(file, tf_dir.name)
                ext = os.path.splitext(file)[-1].lower()
                if valid_ext and ext in valid_ext:
                    main_file = os.path.join(tf_dir.name, file)
        if not main_file:
            raise Exception(f"No valid file found for dataset {dataset.name} with valid extensions {valid_ext}")
        return main_file

    input_raster_file = export_collection_files(input_raster_dataset, valid_ext=['.tif', '.tiff'])

    # Get the SRID / EPSG code from the input raster file
    ds = gdal.OpenEx(input_raster_file)
    proj = osr.SpatialReference(wkt=ds.GetProjection())
    proj.AutoIdentifyEPSG()
    srid = int(proj.GetAttrValue("AUTHORITY", 1))
    srid = srid if srid is not None else 4326

    # Get the pour point geometry from the Select a Pour Point step
    point_step = workflow.get_step_by_name("Select a Pour Point")
    geometry = point_step.get_parameter("geometry")
    gdf = gpd.GeoDataFrame.from_features(geometry["features"], crs="EPSG:4326")
    gdf = gdf.to_crs(epsg=srid)  # reproject to the input raster's CRS
    pour_point_name = "pour_point"
    pour_point_path = os.path.join(tf_dir.name, f"{pour_point_name}.shp")
    gdf.to_file(pour_point_path)

    # 3. Set up XMSTool
    # Set environment varaibles
    os.environ["XMS_PYTHON_APP_TEMP_DIRECTORY"] = tf_dir.name
    print("XMS_PYTHON_APP_TEMP_DIRECTORY env variable: ", os.environ["XMS_PYTHON_APP_TEMP_DIRECTORY"])

    # Create a XMSToolClass instance
    xmstool_class = xmstool_step.options["xmstool_class"]
    package, p_class = xmstool_class.rsplit(".", 1)
    mod = __import__(package, fromlist=[p_class])
    XMSToolClass = getattr(mod, p_class)
    delineate_hydrologic_features = XMSToolClass()

    # Set testing and GUI folder
    delineate_hydrologic_features.set_gui_data_folder(tf_dir.name)
    current_test_folder(tf_dir.name)

    # Set arguments  # TODO use the argument names instead of the index
    arguments = delineate_hydrologic_features.initial_arguments()
    arguments[0].value = os.path.basename(os.path.splitext(input_raster_file)[0])
    arguments[1].value = pour_point_name
    arguments[2].value = form_values["threshold_area_sq_km"]
    arguments[3].value = preprocessing_engine
    arguments[4].value = watersheds_basename
    arguments[5].value = streamlines_basename

    print(f"\n\nArguments passed to the tool = {arguments}")
    for idx, argument in enumerate(arguments):
        print(f"\targument[{idx}].value = {argument.value}")

    # 4. Run XMSTool
    try:
        print("\n\n***** Setting tool arguments *****")
        delineate_hydrologic_features.enable_arguments(arguments)
        print("\n\n***** Running Delineate Hydrologic Features tool: *****")
        delineate_hydrologic_features.run_tool(arguments)
        print("\n\n***** Tool completed *****")
    except Exception as e:
        raise RuntimeError(f"Error running the tool: {str(e)}")

    # Clean up any previous xmstool runs for this step from the file database collections
    print("\n\nCleaning previous xmstool results...")

    # 5. Save the output to new datasets
    print("\n\nSaving xmstool output to file database collection...")
    coverages_dir = os.path.join(tf_dir.name, "coverages")
    out_stream_files, out_watershed_files = [], []
    for file in os.listdir(coverages_dir):
        # Find the watershed_boundaries shapefile files
        filename, ext = os.path.splitext(file)
        if filename == watersheds_basename and ext != ".tif":  # ignore .tif files
            out_watershed_files.append(os.path.join(coverages_dir, file))
        # Find the stream_lines shapefile files
        elif filename == streamlines_basename:
            out_stream_files.append(os.path.join(coverages_dir, file))
    print(f"Stream Lines files:  {out_stream_files}\n")
    print(f"Watershed Boundaries files:  {out_watershed_files}\n")

    # Create the spatial manager needed for creating dataset visualizations
    url = parse_url(gs_private_url)
    url_public = parse_url(gs_public_url)
    geoserver_engine = GeoServerSpatialDatasetEngine(
        endpoint=url.endpoint,
        username=url.username,
        password=url.password,
        public_endpoint=url_public.endpoint,
    )
    spatial_manager = TribsSpatialManager(geoserver_engine)

    # Add stream lines shapefile to file database collections
    print("Adding Stream Lines files to file database client...\n")
    sl_dataset = Dataset.new(
        name=streamlines_basename,
        description="Stream Lines from Delineate Hydrologic Features",
        created_by=resource.created_by,
        project=resource,
        dataset_type=DatasetTypes.FEATURES_SHAPEFILE,
        organizations=resource.organizations,
        items=out_stream_files,
        session=resource_db_session,
        srid=srid,
    )
    sl_dataset.generate_visualization(session=resource_db_session, spatial_manager=spatial_manager)

    # Add watershed boundaries shapefile to file database collections
    print("Adding Watershed Boundaries files to file database client...\n")
    wb_dataset = Dataset.new(
        name=watersheds_basename,
        description="Watershed Boundaries from Delineate Hydrologic Features",
        created_by=resource.created_by,
        project=resource,
        dataset_type=DatasetTypes.FEATURES_SHAPEFILE,
        organizations=resource.organizations,
        items=out_watershed_files,
        session=resource_db_session,
        srid=srid,
    )
    wb_dataset.generate_visualization(session=resource_db_session, spatial_manager=spatial_manager)

    print("Saving files to file collection...\n\n")
    resource_db_session.commit()

    print("Finished processing\n\n")
