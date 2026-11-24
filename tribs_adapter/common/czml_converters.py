import datetime
import json
import math
import numpy as np
import os
from pyproj import Transformer, CRS
import re

from tribs_adapter.common.czml_generator import CZMLGenerator
from tribs_adapter.common.output_variables import scale_range

# Folder (inside a dataset's ``czml`` folder) of the per-variable values files of a value layer
VALUES_DIR = 'values'
# A layer plays through in at most about this many clock steps, so output written every few minutes (qout) does
# not take many minutes to play. The values keep their own time step.
MAX_CLOCK_STEPS = 500
# Color of a feature before the browser has colored it by value (and of a value that is missing)
NO_VALUE_RGBA = [160, 160, 160, 255]
POLYGON_ALPHA = 175


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


def point_entity(entity_id, location):
    """A point feature of a value layer: ``location`` is ``(longitude, latitude)`` in degrees."""
    return dict(id=entity_id, kind='point', positions=[float(location[0]), float(location[1])])


def polygon_entity(entity_id, positions):
    """A polygon feature of a value layer: ``positions`` is a flat list of longitude, latitude, height."""
    return dict(id=entity_id, kind='polygon', positions=[float(p) for p in positions])


def write_geometry_czml(path, name, entities):
    """Write the features of a value layer as one CZML document. The features are static and gray: the browser colors
    them from the values files (see ``write_value_layer``). There is no clock or availability in the document, so
    loading it does not change the viewer's clock and the features show at any time."""
    czml = [{'id': 'document', 'name': name, 'version': '1.0'}]
    for entity in entities:
        if entity['kind'] == 'point':
            czml.append({
                'id': entity['id'],
                'position': {'cartographicDegrees': entity['positions'] + [20]},
                'point': {
                    'color': {'rgba': NO_VALUE_RGBA},
                    'outlineColor': {'rgba': [0, 0, 0, 255]},
                    'outlineWidth': 1,
                    'pixelSize': 10,
                    'show': True,
                    'heightReference': 'RELATIVE_TO_GROUND',
                },
            })
        else:
            czml.append({
                'id': entity['id'],
                'polygon': {
                    'positions': {'cartographicDegrees': entity['positions']},
                    'material': {'solidColor': {'color': {'rgba': NO_VALUE_RGBA[:3] + [POLYGON_ALPHA]}}},
                    'height': 0,
                    'heightReference': 'RELATIVE_TO_GROUND',
                    'show': True,
                },
            })
    with open(path, 'w') as f:
        json.dump(czml, f)


def _safe_file_name(name):
    return re.sub(r'[^A-Za-z0-9_.-]', '_', name)


def _json_number(value):
    """A value for a values file: six significant digits, None for a missing or non-finite value."""
    if value is None or not math.isfinite(value):
        return None
    return float(f'{value:.6g}')


def _iso(moment):
    return moment.strftime('%Y-%m-%dT%H:%M:%SZ')


def _clock_step_hours(hours):
    """The step the clock plays a layer with: its usual time step, but no finer than ``MAX_CLOCK_STEPS`` steps over
    the whole series. None for a single time."""
    if len(hours) < 2:
        return None
    step = float(np.median(np.diff(hours)))
    return max(step, (hours[-1] - hours[0]) / MAX_CLOCK_STEPS)


def write_value_layer(czml_dir, frames, time_column, variables, start_date):
    """Write the values files of a value layer: for each variable one JSON file with the value of every feature at
    every time, which the browser colors the features from (and can recolor with any ramp).

    Args:
        czml_dir(str): The dataset's ``czml`` folder; the files go in its ``values`` folder.
        frames(dict): ``{entity id: DataFrame}``, the time series of each feature as read from its file.
        time_column(str): Column of the frames that holds the hours since the start of the run.
        variables(list): ``[{'name': <column>, 'factor': <display units per file unit>, ...}]`` to write. Other keys
            (label, units, tier, description) are passed through.
        start_date(datetime.datetime): Start of the run (STARTDATE); anything else leaves the times out, and the
            layer then shows its first time only.

    Returns:
        list: The ``variables`` with, added to each: ``min`` and ``max`` (display units, over all features and times;
        None when there is no value), ``start`` and ``end`` (ISO times of the first and last row), ``step_hours``
        (see ``_clock_step_hours``) and ``values`` (path of its file relative to ``czml_dir``).

        A values file holds ``{'variable', 'start', 'hours': [...], 'ids': [...], 'values': [[...], ...]}``:
        ``values[i][j]`` is the value of feature ``ids[i]`` at ``hours[j]``, in display units, null when the feature
        has no row for that hour. ``hours`` are the times of the files, in hours since the start of the run. A
        feature shows the row of the last hour at or before the clock time.
    """
    values_dir = os.path.join(czml_dir, VALUES_DIR)
    os.makedirs(values_dir, exist_ok=True)

    ids = list(frames.keys())
    indexed = {}
    for entity_id, frame in frames.items():
        frame = frame[np.isfinite(frame[time_column].to_numpy(dtype=float))]  # a row without a time has no place
        frame = frame.drop_duplicates(subset=time_column, keep='last').set_index(time_column).sort_index()
        frame.index = frame.index.astype(float).round(6)
        indexed[entity_id] = frame
    hours = sorted(set().union(*(frame.index for frame in indexed.values())))
    has_times = isinstance(start_date, datetime.datetime) and len(hours) > 0
    start = _iso(start_date + datetime.timedelta(hours=hours[0])) if has_times else None
    end = _iso(start_date + datetime.timedelta(hours=hours[-1])) if has_times else None
    run_start = _iso(start_date) if has_times else None
    step_hours = _clock_step_hours(hours) if has_times else None

    written = []
    for position, variable in enumerate(variables):
        name, factor = variable['name'], variable.get('factor', 1.0)
        rows, low, high = [], None, None
        for entity_id in ids:
            frame = indexed[entity_id]
            if name in frame.columns:
                series = frame[name].reindex(hours).to_numpy(dtype=float) * factor
            else:
                series = np.full(len(hours), np.nan)
            finite = series[np.isfinite(series)]
            if finite.size:
                low = float(finite.min()) if low is None else min(low, float(finite.min()))
                high = float(finite.max()) if high is None else max(high, float(finite.max()))
            rows.append([_json_number(value) for value in series])
        relative_path = os.path.join(VALUES_DIR, f'{position:03d}_{_safe_file_name(name)}.json')
        with open(os.path.join(czml_dir, relative_path), 'w') as f:
            json.dump(dict(variable=name, start=run_start, hours=hours, ids=ids, values=rows), f)
        low, high = scale_range(low, high, 1.0)
        written.append(dict(
            variable, min=_json_number(low), max=_json_number(high), start=start, end=end, step_hours=step_hours,
            values=relative_path,
        ))
    return written


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
