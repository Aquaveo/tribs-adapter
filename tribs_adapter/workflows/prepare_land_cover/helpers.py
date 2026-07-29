import rasterio
import pandas as pd
import numpy as np
import os


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


def read_tree_class_to_df(request, session, resource, work_step, *args, **kwargs):
    """
    Read the tree class from the previous step and return as a pandas DataFrame.
    """
    class_ids = work_step.workflow.get_attribute('class_ids')
    columns = [
        'ID',
        'Free Throughfall Coefficient (P)',
        'Canopy Field Capacity (S) (mm)',
        'Drainage Coefficient (K) (mm/hr)',
        'Drainage Exponent (b2) (mm/hr)',
        'Albedo (Al)',
        'Vegetation Height (h) (m)',
        'Optical Transmission Coefficient (Kt)',
        'Canopy-Average Stomatal Resistance (Rs) (s/m)',
        'Vegetation Fraction (V)',
        'Leaf Area Index (LAI)',
        'Stress Threshold for Soil Evaporation (thetas)',
        'Stress Threshold for Plant Transpiration (thetat)'
    ]
    dataset = pd.DataFrame(0.01, index=np.arange(len(class_ids)), columns=columns)
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
        ext = file.rsplit('.', 1)[1]
        if ext in file_extentions:
            return os.path.join(client.path, file)

    raise FileNotFoundError(f"No file with extensions {file_extentions} found in the dataset ({dataset})")
