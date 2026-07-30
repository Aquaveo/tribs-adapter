import numpy as np
import pytest
from rasterio.transform import from_origin
from shapely.geometry import Polygon, box

from tribs_adapter.workflows.prepare_land_cover.helpers import (
    LDT_COLUMNS, build_ldt_dataframe, extract_valid_class_ids, validate_raster_covers_geometry
)

# 10x10 raster with 1x1 pixels covering (0, 0) to (10, 10)
BOUNDS = (0.0, 0.0, 10.0, 10.0)
TRANSFORM = from_origin(0, 10, 1, 1)
NODATA = -9999


def test_extract_valid_class_ids():
    array = np.array([
        [3, 1, NODATA],
        [2, 1, 3],
    ])

    class_ids = extract_valid_class_ids(array, nodata=NODATA)

    assert class_ids.tolist() == [1, 2, 3]


def test_extract_valid_class_ids_no_nodata_value():
    array = np.array([
        [5, 5],
        [7, 6],
    ])

    class_ids = extract_valid_class_ids(array, nodata=None)

    assert class_ids.tolist() == [5, 6, 7]


def test_extract_valid_class_ids_all_nodata():
    array = np.full((3, 3), NODATA)

    with pytest.raises(ValueError, match='no valid data'):
        extract_valid_class_ids(array, nodata=NODATA)


@pytest.mark.parametrize('bad_value', [0, -5])
def test_extract_valid_class_ids_invalid_classes(bad_value):
    array = np.array([
        [1, 2],
        [bad_value, 3],
    ])

    with pytest.raises(ValueError, match='invalid classes'):
        extract_valid_class_ids(array, nodata=NODATA)
        print("This test should have raised a ValueError for invalid classes, but it did not.")


def test_validate_raster_covers_geometry():
    array = np.ones((10, 10))
    geom = box(2, 2, 8, 8)

    validate_raster_covers_geometry(array, BOUNDS, TRANSFORM, NODATA, geom)


def test_validate_raster_covers_geometry_empty_geometry():
    array = np.ones((10, 10))

    with pytest.raises(ValueError, match='no geometries'):
        validate_raster_covers_geometry(array, BOUNDS, TRANSFORM, NODATA, Polygon())


def test_validate_raster_covers_geometry_outside_extent():
    array = np.ones((10, 10))
    geom = box(5, 5, 12, 12)  # sticks out past the raster's right/top edge

    with pytest.raises(ValueError, match='does not cover'):
        validate_raster_covers_geometry(array, BOUNDS, TRANSFORM, NODATA, geom)


def test_validate_raster_covers_geometry_nodata_hole_inside():
    array = np.ones((10, 10))
    array[5, 5] = NODATA  # pixel center (5.5, 4.5) is inside the boundary
    geom = box(2, 2, 8, 8)

    with pytest.raises(ValueError, match='nodata gaps'):
        validate_raster_covers_geometry(array, BOUNDS, TRANSFORM, NODATA, geom)


def test_validate_raster_covers_geometry_nodata_hole_outside():
    array = np.ones((10, 10))
    array[0, 0] = NODATA  # pixel center (0.5, 9.5) is outside the boundary
    geom = box(2, 2, 8, 8)

    validate_raster_covers_geometry(array, BOUNDS, TRANSFORM, NODATA, geom)


def test_validate_raster_covers_geometry_no_nodata_value():
    array = np.full((10, 10), NODATA)  # not treated as holes when the raster has no nodata value
    geom = box(2, 2, 8, 8)

    validate_raster_covers_geometry(array, BOUNDS, TRANSFORM, None, geom)


def test_build_ldt_dataframe():
    land_use_params = {
        'ID': [1, 2, 3],
        'Albedo (Al)': [0.1, 0.2, 0.3],
        'Leaf Area Index (LAI)': [1.0, 2.0, 3.0],
        'Not a real parameter': [9, 9, 9],
    }

    df = build_ldt_dataframe(land_use_params)

    assert list(df.columns) == LDT_COLUMNS
    assert len(df) == 3
    assert df['ID'].tolist() == [1, 2, 3]
    assert df['Al'].tolist() == [0.1, 0.2, 0.3]
    assert df['LAI'].tolist() == [1.0, 2.0, 3.0]


def test_build_ldt_dataframe_missing_params_filled_with_nodata():
    df = build_ldt_dataframe({'ID': [1, 2]})

    assert df['ID'].tolist() == [1, 2]
    unmapped = [col for col in LDT_COLUMNS if col != 'ID']
    for col in unmapped:
        assert (df[col] == -9999).all()
