#!/opt/tethys-python
"""
********************************************************************************
* Name: workflows/generate_tin/job_executables/run_tool.py
* Author: dgallup, ysun
* Created On: Aug 24, 2026
* Copyright: (c) Aquaveo 2026
********************************************************************************
"""
import os
import re
import shutil
import sys
import tempfile
from osgeo import gdal, osr

from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tethysext.atcore.utilities import parse_url
from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.resources import Dataset
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from tribs_adapter.workflows.generate_tin.constants import REDIS_STREAM_LINES, REDIS_WATERSHED_BOUNDARIES
from tethys_dataset_services.engines.geoserver_engine import GeoServerSpatialDatasetEngine

from xms.tool.utilities.file_utils import current_test_folder
from xms.tool_tribs.tribs import ExportTRibsMeshTool
import xms.tool_tribs.tribs.export_tribs_mesh_tool as etm
import xms.tool_tribs.tribs.run_meshbuilder_and_metis_tool as rmm


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
    tf_dir = tempfile.TemporaryDirectory(prefix="tribs_xmsgt_")

    # 1. Get the info to run XMSTool
    print("\n\n\n***************************************************")
    print("Reading info needed to run xmstool")
    xmstool_step = workflow.get_step_by_name("tRIBS Ugrids from Watersheds")
    form_values = xmstool_step.get_parameters()["form-values"]["value"]["value"]

    redis_watershed_base = REDIS_WATERSHED_BOUNDARIES
    redis_stream_base = REDIS_STREAM_LINES
    output_grid_base = os.path.basename(os.path.splitext(form_values["output_grid"])[0])

    input_raster_dataset = resource_db_session.query(Dataset).get(form_values["input_raster"])
    watershed_boundaries_dataset = resource_db_session.query(Dataset).get(form_values["watershed_boundaries"])
    stream_lines_dataset = resource_db_session.query(Dataset).get(form_values["stream_lines"])

    def export_collection_files(dataset, dst_subdir, valid_ext=None):
        main_file = None
        for file in dataset.file_collection_client.files:
            if file != "__meta__.json":
                dataset.file_collection_client.export_item(file, os.path.join(tf_dir.name, dst_subdir))
                ext = os.path.splitext(file)[-1].lower()
                if valid_ext and ext in valid_ext:
                    main_file = os.path.join(tf_dir.name, dst_subdir, file)
        if not main_file:
            raise Exception(f"No valid file found for dataset {dataset.name} with valid extensions {valid_ext}")
        return main_file

    input_raster_file = export_collection_files(input_raster_dataset, 'rasters', valid_ext=['.tif', '.tiff'])
    watershed_boundaries_file = export_collection_files(watershed_boundaries_dataset, 'coverages', valid_ext=['.shp'])
    stream_lines_file = export_collection_files(stream_lines_dataset, 'coverages', valid_ext=['.shp'])

    # 2. Set up XMSTool
    # Set environment varaibles
    os.environ["XMS_PYTHON_APP_TEMP_DIRECTORY"] = tf_dir.name
    print("XMS_PYTHON_APP_TEMP_DIRECTORY env variable: ", os.environ["XMS_PYTHON_APP_TEMP_DIRECTORY"])

    # Create a XMSToolClass instance
    xmstool_class = xmstool_step.options["xmstool_class"]
    package, p_class = xmstool_class.rsplit(".", 1)
    mod = __import__(package, fromlist=[p_class])
    XMSToolClass = getattr(mod, p_class)
    ugrids_from_watersheds = XMSToolClass()

    # Set testing and GUI folder
    ugrids_from_watersheds.set_gui_data_folder(tf_dir.name)
    current_test_folder(tf_dir.name)

    # Set arguments
    arguments = ugrids_from_watersheds.initial_arguments()
    arguments_by_name = {argument.name: argument for argument in arguments}
    arguments_by_name["input_raster"].value = os.path.basename(os.path.splitext(input_raster_file)[0])
    arguments_by_name["watershed_boundaries"].value = os.path.basename(os.path.splitext(watershed_boundaries_file)[0])
    arguments_by_name["stream_lines"].value = os.path.basename(os.path.splitext(stream_lines_file)[0])
    arguments_by_name["refinement_size"].value = form_values["refinement_size"]
    arguments_by_name["bias_factor"].value = form_values["bias_factor"]
    arguments_by_name["buffer_distance"].value = form_values["buffer_distance"]
    arguments_by_name["redis_watershed_boundaries"].value = redis_watershed_base
    arguments_by_name["redis_stream_lines"].value = redis_stream_base
    arguments_by_name["output_grid"].value = output_grid_base

    print("\n\nArguments passed to the tool:")
    for idx, argument in enumerate(arguments):
        print(f"\targument[{idx}].value = {argument.value}")

    # 3. Run XMSTool
    try:
        print("\n\n***** Setting tool arguments *****")
        ugrids_from_watersheds.enable_arguments(arguments)
        print("\n\n***** Running Generate TIN tool: *****")
        ugrids_from_watersheds.run_tool(arguments)
        print("\n\n***** Tool completed *****")
    except Exception as e:
        raise RuntimeError(f"Error running the tool: {str(e)}")

    # 4. Save xmstool output grids to new datasets
    # Get the output grid files created by the tool
    print("\n\nSaving xmstool output to file database collection...")
    out_grid_files = []
    grids_dir = os.path.join(tf_dir.name, 'grids')
    for file in os.listdir(grids_dir):
        if re.search(f"^{output_grid_base}[0-9]*$", os.path.splitext(file)[0]):
            # The output grids names are output_grid base followed by a number and .xmc extension
            # e.g., output_grid1.xmc, output_grid2.xmc, output_grid3.xmc for "output_grid"
            out_grid_files.append(os.path.join(grids_dir, file))
    print(f"\n\nOutput grid files:  {out_grid_files}\n")

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

    # Get the SRID / EPSG code from the input raster file
    # (get it after running xmstool in case the tool changes the projection of the raster)
    ds = gdal.OpenEx(input_raster_file)
    proj = osr.SpatialReference(wkt=ds.GetProjection())
    proj.AutoIdentifyEPSG()
    srid = int(proj.GetAttrValue("AUTHORITY", 1))
    srid = srid if srid is not None else 4326

    # Add output grids to file database collections
    print("Adding Output Grid files to file database client...\n")
    for grid_file in out_grid_files:
        print(f"Running ExportTRibsMeshTool for file {grid_file}...")
        # Make tRIBS TIN from the output grid files created by the tool
        export_tool = ExportTRibsMeshTool()
        export_tool.set_gui_data_folder(tf_dir.name)

        # Copy grid file to .xmc
        shutil.copy2(grid_file, grid_file + ".xmc")

        # Set the tool arguments
        arguments = export_tool.initial_arguments()
        arguments[etm.ARG_INPUT_MESH].value = os.path.basename(grid_file)
        arguments[etm.ARG_REDIS_WATERSHED_BOUNDARIES].value = redis_watershed_base
        arguments[etm.ARG_REDIS_STREAM_LINES].value = redis_stream_base
        output_folder = os.path.join(tf_dir.name, "output", grid_file)
        file_base = os.path.join(output_folder, os.path.splitext(grid_file)[0])
        arguments[etm.ARG_OUTPUT_FILE].value = file_base + ".points"

        # Run the tool, and get the output (multiple files)
        output_tin_files = []
        export_tool.run_tool(arguments)

        tool = rmm.RunMeshbuilderAndMetisTool()
        arguments = tool.initial_arguments()
        arguments[rmm.ARG_POINTS_FILE].value = file_base + '.points'
        tool.set_gui_data_folder(tf_dir.name)
        num_threads = arguments[rmm.ARG_NUM_PROCESSOR_THREADS].value
        file_extensions = [".nodes", ".points", ".edges", ".tri", ".z"]
        for extension in file_extensions:
            file = file_base + extension
            output_tin_files.append(file)
        reach_file = f'{file_base}_flow_{num_threads}nodes.reach'
        tool.run_tool(arguments)
        # Only add the .reach file if it exists, otherwise the dataset creation will fail
        if os.path.exists(reach_file):
            output_tin_files.append(reach_file)
        else:
            print(f'Could not find reach file {reach_file} to add to TIN dataset.', file=sys.stderr)

        # Make a TRIBS_TIN dataset for the grid
        print("Creating dataset for output grid...\n")
        fc_name = os.path.splitext(os.path.basename(grid_file))[0]
        gf_dataset = Dataset.new(
            name=fc_name,
            description="Grid File from Generate TIN",
            created_by=resource.created_by,
            project=resource,
            dataset_type=DatasetTypes.TRIBS_TIN,
            organizations=resource.organizations,
            items=output_tin_files,
            session=resource_db_session,
            srid=srid,
        )
        gf_dataset.generate_visualization(session=resource_db_session, spatial_manager=spatial_manager)

    print("Saving files to file collection...\n\n")
    resource_db_session.commit()

    print("Finished processing\n\n")
