import numpy as np
import os
import pandas as pd
from pyproj import Transformer, CRS
import re

from tribs_adapter.common.czml_generator import CZMLGenerator


def get_file_variables(var_file, skip_cols=2):
    """Get the variables from a file."""
    with open(var_file, 'r') as f:
        _data = f.readlines()
        header = _data[0]
        headers = [x.strip().replace(',', '_').replace('/', '-') for x in re.split(r'\s*\d+-', header)[1:]]
    return headers[skip_cols:]


def get_output_file_variables(output_file):
    """Get the variables from an output file."""
    with open(output_file, 'r') as f:
        _data = f.readlines()
        header = _data[0]
        headers = [x.strip().replace(',', '_').replace('/', '-') for x in re.split(r'\t', header)[1:] if x != '']
    return headers


def get_origin(nodes):
    """Calculate the origin of the pixel files."""
    # Get the origin of the pixel files
    origin = np.mean([node[:2] for node in nodes], axis=0)
    return origin.tolist()


def get_extents(nodes, flat=False, padding=0.01):
    """Calculate the extents of the pixel files.

    Args:
        nodes (list): List of nodes.
        flat (bool): Whether to flatten the extents.
        padding (float): Amount to expand single-point extents.

    Returns:
        list: Extents of list of nodes
    """
    # Get the extents of the pixel files
    xs = [node[0] for node in nodes]
    ys = [node[1] for node in nodes]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    if min_x == max_x:
        min_x -= padding
        max_x += padding

    if min_y == max_y:
        min_y -= padding
        max_y += padding

    extents = [[min_x, min_y], [max_x, max_y]]

    if flat:
        extents = [min_x, min_y, max_x, max_y]

    return extents


def get_nodes(nodes_file, srid, flatten_extents=False):
    nodes = []
    with open(nodes_file, 'r') as f:
        nodes = f.readlines()[2:]
        nodes = [list(map(float, p.strip().split()))[:4] for p in nodes]
        ids = [int(p[-1]) for p in nodes]
    boundary_nodes = reproject(np.array([p[:3] for p in nodes if p[3] == 1]), srid)
    nodes = reproject(np.array([n[:3] for n in nodes]), srid)
    extent = get_extents(nodes, flat=flatten_extents)
    origin = get_origin(nodes)
    return nodes, extent, origin, boundary_nodes, ids


def generate_czml_for_pixel_files(
    nodes_file, pixel_files, start_date, run_time, interval, path_to_write, dataset_id=None, variable=None, srid=32612
):
    """Generate CZML for pixel files."""
    # Read the nodes file
    nodes, _, _, _, _ = get_nodes(nodes_file, srid)

    # Get Variables and Data
    data = {}
    for _f in pixel_files:
        with open(_f, 'r') as f:
            _data = f.readlines()
            header, _data = _data[0], _data[1:]
            headers = [x.strip().replace(',', '_').replace('/', '-') for x in re.split(r'\s*\d+-', header)[1:]]
            _data = [tuple(map(float, d.strip().split())) for d in _data]
            point_id = int(_data[0][0])
            df = pd.DataFrame(_data, columns=headers)
            data[point_id] = df

    # Create Generator
    czml_gen = CZMLGenerator("Pixel Files")
    # Iterate through points and add them to the generator
    for point_id, df in data.items():
        loc = nodes[point_id][:2]
        dataset_id_string = f" [{dataset_id}]" if dataset_id else ""
        czml_gen.add_point(
            point=loc,
            data_values=df[variable].values,
            id=f"point_{point_id}{dataset_id_string}",
            start_time=start_date,
            run_time=run_time,
            interval=interval
        )

    # Get the CZML
    czml_gen.write_czml(path_to_write, legend=True)


def generate_czml_for_qout_files(
    nodes_file,
    output_files,
    start_date,
    run_time,
    interval,
    path_to_write,
    dataset_id=None,
    variable=None,
    srid=32612
):
    """Generate CZML for output files."""
    # Read the nodes file
    nodes, _, _, _, node_ids = get_nodes(nodes_file, srid)
    outlet_id = node_ids.index(2)

    # Get Variables and Data
    data = {}
    for _f in output_files:
        with open(_f, 'r') as f:
            _data = f.readlines()
            header, _data = _data[0], _data[2:]
            headers = [x.strip().replace(',', '_').replace('/', '-') for x in re.split(r'\s*\d+-', header)[1:]]
            _data = [tuple(map(float, d.strip().split())) for d in _data]
            df = pd.DataFrame(_data, columns=headers)
            point_id_str = os.path.splitext(os.path.basename(_f))[0].split('_')[-1]
            if point_id_str == 'Outlet':
                point_id_str = outlet_id
            point_id = int(point_id_str)
            data[point_id] = df

    # Create Generator
    czml_gen = CZMLGenerator("Output Files")

    # Iterate through points and add them to the generator
    for point_id, df in data.items():
        loc = nodes[point_id][:2]

        label_pt_id = str(point_id)
        if point_id == outlet_id:
            label_pt_id = 'Outlet'

        dataset_id_string = f" [{dataset_id}]" if dataset_id else ""
        czml_gen.add_point(
            point=loc,
            data_values=df[variable].values,
            id=f"point_{label_pt_id}{dataset_id_string}",
            start_time=start_date,
            run_time=run_time,
            interval=interval
        )

    # Get the CZML
    czml_gen.write_czml(path_to_write, legend=True)


def generate_czml_for_mrf_and_rft_files(
    nodes_file,
    output_files,
    start_date,
    run_time,
    interval,
    path_to_write,
    dataset_id=None,
    variable=None,
    srid=32612
):
    """Generate CZML for MRF and RFT files."""
    # Read the nodes file
    _, _, _, nodes, _ = get_nodes(nodes_file, srid)

    # Get Variables and Data
    data = {}
    for i, _f in enumerate(output_files):
        with open(_f, 'r') as f:
            _data = f.readlines()
            header, _data = _data[0], _data[2:]
            headers = [x.strip().replace(',', '_').replace('/', '-') for x in re.split(r'\t', header) if x != '']
            _data = [tuple(map(float, d.strip().split())) for d in _data]
            df = pd.DataFrame(_data, columns=headers)
            data[i] = df

    # Create Generator
    czml_gen = CZMLGenerator("TRIBS Output Files")

    # Iterate through polygons and add them to the generator
    for _, df in data.items():
        polygon_points = nodes.flatten()
        czml_gen.add_polygon(
            polygon=polygon_points,
            data_values=df[variable].values,
            id=f"polygon [{dataset_id}]",
            start_time=start_date,
            run_time=run_time,
            interval=interval
        )

    # Get the CZML
    czml_gen.write_czml(path_to_write, legend=True)


def generate_czml_for_sdf_station(
    start_time, run_time, interval, czml_path, lat, long, id, station_file, variables, data, srid=32612
):

    for variable in variables:
        czml_gen = CZMLGenerator("SDF Station")

        reprojected_loc = reproject(np.array([[long, lat, 0]]), srid)[0]

        czml_gen.add_point(
            point=reprojected_loc[:2],
            data_values=data[variable].values,
            id=f"station_{id}",
            start_time=start_time,
            run_time=int(run_time),
            interval=interval
        )
        czml_file_path = os.path.join(
            czml_path, f"{os.path.splitext(os.path.basename(station_file))[0]}_{variable}.czml"
        )
        czml_gen.write_czml(czml_file_path)


def reproject(nodes, from_epsg, to_epsg=4326):
    from_crs = CRS.from_epsg(from_epsg).to_3d()
    to_crs = CRS.from_epsg(to_epsg).to_3d()
    transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
    fx, fy, fz = transformer.transform(nodes[:, 0], nodes[:, 1], nodes[:, 2])
    t_nodes = np.dstack((fx, fy, fz))[0].astype(np.float64)

    assert t_nodes.shape == nodes.shape, "Transformed nodes array has incorrect shape."
    assert t_nodes.dtype == np.float64, "Transformed nodes array has incorrect dtype."
    return t_nodes
