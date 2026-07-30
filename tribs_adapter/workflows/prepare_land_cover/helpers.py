import rasterio
import pandas as pd
import numpy as np
import os

from shapely.geometry import box
from rasterio.features import geometry_mask

LDT_COLUMNS = ["ID", "a", "b1", "P", "S", "K", "b2", "Al", "h", "Kt", "Rs", "V", "LAI", "thetas", "thetat"]
LDT_PARAM_TO_COL = {
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


def write_numpy_array_to_raster_file(type, path, array, crs, transform, precision, nodata=-9999):
    with rasterio.open(
        path,
        'w',
        driver='AAIGrid' if type == 'asc' else 'GTiff',
        height=array.shape[0],
        width=array.shape[1],
        count=1,
        dtype=array.dtype,
        nodata=nodata,
        crs=crs,
        transform=transform,
        decimal_precision=precision
    ) as dst:
        dst.write(array, 1)


def write_numpy_array_to_asc_file(path, array, crs, transform, precision, nodata=-9999):
    write_numpy_array_to_raster_file('asc', path, array, crs, transform, precision, nodata)


def write_numpy_array_to_geotiff_file(path, array, crs, transform, precision, nodata=-9999):
    write_numpy_array_to_raster_file('tif', path, array, crs, transform, precision, nodata)


def extract_valid_class_ids(array, nodata=None):
    """
    Validate land use class values and return the sorted unique class IDs.

    Args:
        array (np.ndarray): the land use raster band.
        nodata: the raster's nodata value, or None if it has none.

    Raises:
        ValueError: If all pixels are nodata, or any valid class is less than 1.

    Returns:
        np.ndarray: sorted unique class IDs as integers.
    """
    if nodata is not None:
        valid = np.ma.masked_equal(array, nodata).compressed()
    else:
        valid = array.ravel()

    if valid.size == 0:
        raise ValueError("LU raster contains no valid data (all pixels are nodata).")

    if (valid < 1).any():
        bad = np.unique(valid[valid < 1])
        raise ValueError(f"LU raster contains invalid classes: {bad}.")

    return np.unique(valid).astype(int)


def validate_raster_covers_geometry(array, bounds, transform, nodata, geom):
    """
    Validate that a raster fully covers a geometry.

    Args:
        array (np.ndarray): the raster band.
        bounds: the raster's bounds (left, bottom, right, top).
        transform: the raster's affine transform.
        nodata: the raster's nodata value, or None if it has none.
        geom: a shapely geometry in the raster's CRS.

    Raises:
        ValueError: If the geometry is empty, extends outside the raster extent,
            or overlaps nodata pixels.
    """
    if geom.is_empty:
        raise ValueError("Geometry contains no geometries.")

    if not box(*bounds).contains(geom):
        raise ValueError(
            f"LU raster extent {tuple(bounds)} does not cover the "
            f"watershed boundary {geom.bounds}."
        )

    if nodata is not None:
        # overlap pixels are True
        overlap = geometry_mask([geom], out_shape=array.shape, transform=transform, invert=True)
        if (overlap & (array == nodata)).any():
            raise ValueError("LU raster has nodata gaps inside the watershed boundary.")


def build_ldt_dataframe(land_use_params):
    """
    Build the .ldt table from the land use parameters entered in the workflow.

    Args:
        land_use_params (dict): parameter name -> list of values, one per land use type.

    Returns:
        pd.DataFrame: one row per land use type with columns LDT_COLUMNS;
            parameters without a value are filled with -9999.
    """
    num_types = len(land_use_params['ID'])
    df = pd.DataFrame(-9999, index=np.arange(num_types), columns=LDT_COLUMNS)
    for param, values in land_use_params.items():
        if param in LDT_PARAM_TO_COL:
            df[LDT_PARAM_TO_COL[param]] = values
    return df


def read_tree_class_to_df(request, session, resource, work_step, *args, **kwargs):
    """
    Read the tree class from the previous step and return as a pandas DataFrame.
    """
    class_ids = work_step.workflow.get_attribute('class_ids')
    dataset = pd.DataFrame(0.01, index=np.arange(len(class_ids)), columns=list(LDT_PARAM_TO_COL))
    dataset['ID'] = class_ids
    dataset['ID'] = dataset['ID'].astype(int)
    dataset.fillna(0.01, inplace=True)
    return dataset


def get_input_file_path_from_dataset(dataset):
    """
    Get the file path from a specified dataset.

    Args:
        dataset_id (int): the specified dataset id.

    Raises:
        ValueError: If the dataset type is not supported.
        FileNotFoundError: If no file with the expected extentions is found.

    Returns:
        str: The full path of the file if found.
    """
    client = dataset.file_collection_client
    dataset_type = dataset.dataset_type
    if 'ASCII' in dataset_type:
        file_extentions = ['asc']
    elif 'GEOTIFF' in dataset_type:
        file_extentions = ['tif', 'tiff']
    elif 'SHAPEFILE' in dataset_type:
        file_extentions = ['shp']
    else:
        raise ValueError(f"Unsupported dataset type: {dataset_type}")

    for file in client.files:
        ext = os.path.splitext(file)[1].lstrip('.')
        if ext in file_extentions:
            return os.path.join(client.path, file)

    raise FileNotFoundError(f"No file with extensions {file_extentions} found in the dataset ({dataset})")
