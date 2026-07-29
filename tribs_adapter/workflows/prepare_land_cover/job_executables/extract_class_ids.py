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
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from rasterio.features import geometry_mask

from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tribs_adapter.resources.dataset import Dataset
from tribs_adapter.workflows.prepare_land_cover.helpers import get_input_file_path_from_dataset


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
        lu_shape = lu_raster.shape
        lu_transform = lu_raster.transform

    # 1. Valid if there are invalid classes
    if lu_nodata is not None:
        valid = np.ma.masked_equal(lu_array, lu_nodata).compressed()
    else:
        valid = lu_array.ravel()

    if valid.size == 0:
        raise ValueError("LU raster contains no valid data (all pixels are nodata).")

    if (valid < 1).any():
        bad = np.unique(valid[valid < 1])
        raise ValueError(f"LU raster contains invalid classes: {bad}.")

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

    # 2.1 Does the raster extent contain the watershed boundary?
    if not box(*lu_bounds).contains(wb_geom):
        raise ValueError(
            f"LU raster extent {tuple(lu_bounds)} does not cover the "
            f"watershed boundary {wb_geom.bounds}."
        )

    # 2.2 Any nodata holes inside the boundary?
    if lu_nodata is not None:
        # overlap pixels are True
        overlap = geometry_mask([wb_geom], out_shape=lu_shape, transform=lu_transform, invert=True)
        if (overlap & (lu_array == lu_nodata)).any():
            raise ValueError("LU raster has nodata gaps inside the watershed boundary.")

    # 3. Extract unique class IDs
    class_ids = np.unique(valid).astype(int)
    workflow.set_attribute('class_ids', class_ids.tolist())

    print(f'Finish extracting class IDs from {lu_dataset_name}({lu_dataset_id})!')
