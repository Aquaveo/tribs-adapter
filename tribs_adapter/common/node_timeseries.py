"""Readers for the tRIBS time series output files the app shows as points and as the basin polygon: node dynamic
(``.pixel``), outlet and interior node hydrographs (``.qout``) and basin averaged output (``.mrf``/``.rft``).

One place knows the file layouts, so the map layers and the plots read the same columns and the same time axis:

* ``.pixel`` and ``.qout``: one header line, then data. Older tRIBS numbers the columns and puts the units after a
  comma (``1-NodeID  2-Time,hr  3-Nwt,mm``); current tRIBS writes plain names with the units after an underscore
  (``NodeID Time_hr Nwt_mm``). Both give the same layer names (see ``output_variables.canonical_layer_name``).
* ``.mrf`` and ``.rft``: a header line, a units line, then data, tab separated.

The time of a row is the hour in its time column (hours since the start of the run), never its row number.
"""
import logging
import os
import re

import pandas as pd

from tribs_adapter.common.output_variables import canonical_layer_name

log = logging.getLogger(__name__)

NODE_ID_COLUMN = 'NodeID'
NODE_TIME_COLUMN = 'Time_hr'  # pixel and qout files
BASIN_TIME_COLUMN = 'Time'  # mrf and rft files
OUTLET = 'Outlet'

_COLUMN_NUMBER = re.compile(r'\s*\d+-')
_NUMBERED_HEADER = re.compile(r'^\s*1-')


def parse_header(header_line):
    """The layer names of a pixel/qout header line, in file order: ``['NodeID', 'Time_hr', 'Nwt_mm', ...]``."""
    if _NUMBERED_HEADER.match(header_line):
        columns = _COLUMN_NUMBER.split(header_line)[1:]
    else:
        columns = header_line.split()
    return [canonical_layer_name(column) for column in columns]


def _read_rows(path, lines, columns):
    rows = []
    for number, line in lines:
        tokens = line.split()
        if not tokens:
            continue
        if len(tokens) != len(columns):
            raise ValueError(
                f'Line {number} of {os.path.basename(path)} has {len(tokens)} values for {len(columns)} columns.'
            )
        try:
            rows.append([float(token) for token in tokens])
        except ValueError:
            raise ValueError(f'Line {number} of {os.path.basename(path)} holds a value that is not a number.') from None
    if not rows:
        raise ValueError(f'{os.path.basename(path)} has no data rows.')
    return pd.DataFrame(rows, columns=columns)


def read_node_file(path):
    """Read a ``.pixel`` or ``.qout`` file into a DataFrame with one column per header column (canonical layer names).

    Raises:
        ValueError: naming the file, when the header gives no columns or no time column, when a row does not match
            the header or when there is no data. A file that cannot be read must fail the layer, not empty it.
    """
    with open(path, 'r') as f:
        lines = f.readlines()
    columns = parse_header(lines[0]) if lines else []
    if NODE_TIME_COLUMN not in columns:
        raise ValueError(f'Could not find the {NODE_TIME_COLUMN} column in the header of {os.path.basename(path)}.')
    if len(set(columns)) != len(columns):
        raise ValueError(f'The header of {os.path.basename(path)} names a column twice.')
    return _read_rows(path, enumerate(lines[1:], start=2), columns)


def node_file_variables(path):
    """The variables of a ``.pixel`` or ``.qout`` file: its columns without the node ID and the time."""
    with open(path, 'r') as f:
        columns = parse_header(f.readline())
    return [column for column in columns if column not in (NODE_ID_COLUMN, NODE_TIME_COLUMN)]


def read_basin_file(path):
    """Read a ``.mrf`` or ``.rft`` file.

    Returns:
        ``(frame, units)``: a DataFrame with one column per header column, and the units of each column from the
        units line (``{'Srf': 'm3/s', 'FState': None}``; ``[]`` or a blank cell means no units). Names and units are
        paired by their position in the line, so a blank unit does not shift the ones after it.

    Raises:
        ValueError: naming the file, when it has no ``Time`` column, a row does not match the header or there is no
            data.
    """
    with open(path, 'r') as f:
        lines = f.readlines()
    header = lines[0].rstrip('\r\n').split('\t') if lines else []
    unit_cells = lines[1].rstrip('\r\n').split('\t') if len(lines) > 1 else []
    columns, units = [], {}
    for position, cell in enumerate(header):
        if not cell.strip():
            continue
        # mrf/rft names carry no units (those are on the next line), so they are only made safe as layer names
        column = cell.strip().replace(',', '_').replace('/', '-')
        columns.append(column)
        token = unit_cells[position].strip() if position < len(unit_cells) else ''
        units[column] = None if token in ('', '[]', '[-]', '-') else token
    if BASIN_TIME_COLUMN not in columns:
        raise ValueError(f'Could not find the {BASIN_TIME_COLUMN} column in the header of {os.path.basename(path)}.')
    return _read_rows(path, enumerate(lines[2:], start=3), columns), units


# The run length in the name of a basin file: salas0240_00.mrf is the file of a 240 hour run
_BASIN_FILE_RUN_LENGTH = re.compile(r'(?P<hours>\d{4})_(?P<minutes>\d{2})\.(mrf|rft)$')


def basin_run_hours(path):
    """The length of the run in hours, from the name of its ``.mrf`` or ``.rft`` file; None when the name does not
    say."""
    match = _BASIN_FILE_RUN_LENGTH.search(os.path.basename(str(path)))
    if match is None:
        return None
    return int(match.group('hours')) + int(match.group('minutes')) / 60


def _without_zero_tail(frame):
    """The rows without the last ones in which every variable is zero. Rows of zeros before the last row with a
    value are kept, and so is a file with nothing but zeros."""
    has_value = (frame.drop(columns=[BASIN_TIME_COLUMN]) != 0).any(axis=1).to_numpy()
    if not has_value.any():
        return frame
    return frame.iloc[:len(has_value) - has_value[::-1].argmax()]


def read_basin_series(path):
    """Read a ``.mrf`` or ``.rft`` file as the series to show (on the map and in a plot): ``read_basin_file`` without
    the rows tRIBS writes after the end of the run.

    tRIBS ends these files with a few rows past the run's last hour (``salas0240_00.mrf`` has rows for hours 241 to
    244) in which most variables are zero, some hold a filler value (9999.99) and the rest fade out, so every variable
    drops at the end. The rows after the run length in the file's name are left out; of an ``.mrf`` file, whose
    variables are never all zero during a run, so are the last rows in which every variable is zero (which also
    covers a file whose name does not give the run length).

    Returns:
        ``(frame, units)`` as ``read_basin_file``.
    """
    frame, units = read_basin_file(path)
    run_hours = basin_run_hours(path)
    if run_hours is not None:
        frame = frame[frame[BASIN_TIME_COLUMN] <= run_hours]
    if str(path).endswith('.mrf'):
        frame = _without_zero_tail(frame)
    if frame.empty:
        raise ValueError(f'{os.path.basename(path)} has no rows within its run of {run_hours} hours.')
    return frame.reset_index(drop=True), units


def pixel_file_node(path):
    """The node ID a ``.pixel`` file is for: the one in its first data row. Only the top of the file is read."""
    name = os.path.basename(path)
    with open(path, 'r') as f:
        columns = parse_header(f.readline())
        if NODE_ID_COLUMN not in columns:
            raise ValueError(f'Could not find the {NODE_ID_COLUMN} column in the header of {name}.')
        for line in f:
            tokens = line.split()
            if not tokens:
                continue
            try:
                return int(float(tokens[columns.index(NODE_ID_COLUMN)]))
            except (IndexError, ValueError):
                raise ValueError(f'Could not read the node ID in the first data row of {name}.') from None
    raise ValueError(f'{name} has no data rows.')


def pixel_files_by_node(pixel_files):
    """``{node ID: path}`` of ``.pixel`` files, by the node ID in the first data row of each file. The file name is
    not used: ``salas1656.pixel`` also ends in 56 and 6. When two files are for the same node, the first by file
    name is used, for the map and the plot alike, and the other is logged."""
    by_node = {}
    for path in sorted(pixel_files, key=os.path.basename):
        node = pixel_file_node(path)
        if node in by_node:
            log.warning(
                f'{os.path.basename(path)} is for the same node as {os.path.basename(by_node[node])}: ignored.'
            )
            continue
        by_node[node] = path
    return by_node


def qout_point(path):
    """The point a ``.qout`` file belongs to, from its name: ``'Outlet'`` for ``<base>_Outlet.qout``, else the node
    ID as a string (``'1148'`` for ``<base>_1148.qout``).

    Raises:
        ValueError: naming the file, when its name does not end in ``_Outlet`` or ``_<node ID>``.
    """
    stem = os.path.splitext(os.path.basename(path))[0]
    point = stem.rsplit('_', 1)[-1] if '_' in stem else ''
    if point != OUTLET and not point.isdigit():
        raise ValueError(f'Could not tell the node of {os.path.basename(path)}: its name does not end in _Outlet '
                         f'or _<node ID>.')
    return point


def qout_files_by_point(qout_files):
    """``{point: path}`` of ``.qout`` files (see ``qout_point``). When two files are for the same point (output of
    two runs with different base names in one folder), the first by file name is used, for the map and the plot
    alike, and the other is logged."""
    by_point = {}
    for path in sorted(qout_files, key=os.path.basename):
        point = qout_point(path)
        if point in by_point:
            log.warning(
                f'{os.path.basename(path)} is for the same point as {os.path.basename(by_point[point])}: ignored.'
            )
            continue
        by_point[point] = path
    return by_point
