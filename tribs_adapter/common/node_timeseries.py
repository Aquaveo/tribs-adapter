"""Readers for the tRIBS time series output files the app shows as points and as the basin polygon: node dynamic
(``.pixel``), outlet and interior node hydrographs (``.qout``) and basin averaged output (``.mrf``/``.rft``).

One place knows the file layouts, so the map layers and the plots read the same columns and the same time axis:

* ``.pixel`` and ``.qout``: one header line, then data. Older tRIBS numbers the columns and puts the units after a
  comma (``1-NodeID  2-Time,hr  3-Nwt,mm``); current tRIBS writes plain names with the units after an underscore
  (``NodeID Time_hr Nwt_mm``). Both give the same layer names (see ``output_variables.canonical_layer_name``).
* ``.mrf`` and ``.rft``: a header line, a units line, then data, tab separated.

The time of a row is the hour in its time column (hours since the start of the run), never its row number.
"""
import os
import re

import pandas as pd

from tribs_adapter.common.output_variables import canonical_layer_name

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
        units line (``{'Srf': 'm3/s', 'FState': None}``; ``[]`` means no units).

    Raises:
        ValueError: naming the file, when it has no ``Time`` column, a row does not match the header or there is no
            data.
    """
    with open(path, 'r') as f:
        lines = f.readlines()
    # mrf/rft names carry no units (those are on the next line), so they are only made safe as layer names
    header = lines[0].split('\t') if lines else []
    columns = [column.strip().replace(',', '_').replace('/', '-') for column in header if column.strip()]
    if BASIN_TIME_COLUMN not in columns:
        raise ValueError(f'Could not find the {BASIN_TIME_COLUMN} column in the header of {os.path.basename(path)}.')
    unit_tokens = [token.strip() for token in lines[1].split('\t') if token.strip()] if len(lines) > 1 else []
    units = {
        column: (None if token in ('[]', '[-]', '-') else token) for column, token in zip(columns, unit_tokens)
    }
    return _read_rows(path, enumerate(lines[2:], start=3), columns), units


def pixel_files_by_node(pixel_files):
    """``{node ID: path}`` of ``.pixel`` files, by the node ID in the first data row of each file. The file name is
    not used: ``salas1656.pixel`` also ends in 56 and 6."""
    by_node = {}
    for path in pixel_files:
        frame = read_node_file(path)
        if NODE_ID_COLUMN not in frame.columns:
            raise ValueError(f'Could not find the {NODE_ID_COLUMN} column in the header of {os.path.basename(path)}.')
        by_node[int(frame[NODE_ID_COLUMN].iloc[0])] = path
    return by_node


def qout_point(path):
    """The point a ``.qout`` file belongs to, from its name: ``'Outlet'`` for ``<base>_Outlet.qout``, else the node
    ID as a string (``'1148'`` for ``<base>_1148.qout``)."""
    return os.path.splitext(os.path.basename(path))[0].rsplit('_', 1)[-1]


def qout_files_by_point(qout_files):
    """``{point: path}`` of ``.qout`` files (see ``qout_point``)."""
    return {qout_point(path): path for path in qout_files}
