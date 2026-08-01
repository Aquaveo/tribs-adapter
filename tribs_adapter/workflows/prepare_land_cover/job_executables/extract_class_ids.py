#!/opt/tethys-python
"""
********************************************************************************
* Name: extract_class_ids.py
* Author: ysun
* Created On: Jul 27, 2026
* Copyright: (c) Aquaveo 2026
********************************************************************************
"""
import rasterio
import geopandas as gpd

from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tribs_adapter.resources.dataset import Dataset
from tribs_adapter.workflows.prepare_land_cover.helpers import (
    extract_valid_class_ids, get_input_file_path_from_dataset, validate_raster_covers_geometry
)


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
    if not extra_args or len(extra_args) != 4:
        raise RuntimeError(f"Invalid number of arguments passed to the job. Expected 4, got {len(extra_args or [])}.")

    lu_dataset_name, lu_dataset_id = extra_args[0], extra_args[1]
    lu_dataset = resource_db_session.query(Dataset).get(lu_dataset_id)
    if not lu_dataset:
        raise RuntimeError(f"Dataset {lu_dataset_name} ({lu_dataset_id}) not found.")
    lu_input_path = get_input_file_path_from_dataset(lu_dataset)
    with rasterio.open(lu_input_path) as lu_raster:
        lu_array = lu_raster.read(1)
        lu_nodata = lu_raster.nodata
        lu_crs = lu_raster.crs or f"EPSG:{lu_dataset.srid}"
        lu_bounds = lu_raster.bounds
        lu_transform = lu_raster.transform

    # 1. Validate class values and extract unique class IDs
    class_ids = extract_valid_class_ids(lu_array, lu_nodata)

    # 2. Validate if lu_raster covers the watershed boundary
    wb_dataset_name, wb_dataset_id = extra_args[2], extra_args[3]
    wb_dataset = resource_db_session.query(Dataset).get(wb_dataset_id)
    if not wb_dataset:
        raise RuntimeError(f"Dataset {wb_dataset_name} ({wb_dataset_id}) not found.")
    wb_input_path = get_input_file_path_from_dataset(wb_dataset)
    wb_gdf = gpd.read_file(wb_input_path)
    if wb_gdf.crs is None:
        wb_gdf.set_crs(f"EPSG:{wb_dataset.srid}", inplace=True)
    wb_gdf.to_crs(lu_crs, inplace=True)  # reproject to the same crs as lu_raster
    wb_geom = wb_gdf.union_all()  # merge all geometries into one
    if wb_geom.is_empty:
        raise ValueError(f"Watershed boundary {wb_dataset_name} ({wb_dataset_id}) contains no geometries.")

    validate_raster_covers_geometry(lu_array, lu_bounds, lu_transform, lu_nodata, wb_geom)

    # 3. Save the class IDs to the workflow
    workflow.set_attribute('class_ids', class_ids.tolist())

    print(f'Finish extracting class IDs from {lu_dataset_name}({lu_dataset_id})!')
