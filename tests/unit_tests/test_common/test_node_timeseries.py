"""Tests for the readers of node, outlet and basin time series files (tribs_adapter/common/node_timeseries.py)."""
from pathlib import Path

import pytest

from tribs_adapter.common import node_timeseries as nts

FILES = Path(__file__).resolve().parent.parent.parent / 'files'

NUMBERED_PIXEL = (
    '1-NodeID  2-Time,hr  3-Nwt,mm  4-QpOut,mm/h  5-SoilMoist,d/l\n'
    '    1656      0001.00 375.2 0.5 0.80\n'
    '    1656      0002.00 376.2 0.0 0.81\n'
)
# Current tRIBS: no column numbers, units after underscores
PLAIN_PIXEL = (
    'NodeID Time_hr Nwt_mm QpOut_mm_h SoilMoist_[] \n'
    '    1656      0001.00 375.2 0.5 0.80\n'
    '    1656      0002.00 376.2 0.0 0.81\n'
)
QOUT = '1-Time,hr\t 2-Qstrm,m3/s\t3-Hlev,m\n0.0625\t0.5\t0.1\n0.1250\t0.7\t0.2\n'
MRF = 'Time\tSrf\tFState\t\nhr\tm3/s\t[]\t\n1.0\t0.25\t0\n2.0\t0.50\t1\n'


def _write(path, text):
    path.write_text(text)
    return str(path)


def test_parse_header_of_a_numbered_header():
    assert nts.parse_header(NUMBERED_PIXEL.splitlines()[0]) == [
        'NodeID', 'Time_hr', 'Nwt_mm', 'QpOut_mm-h', 'SoilMoist_d-l'
    ]


def test_parse_header_of_a_plain_header_gives_the_same_layer_names():
    assert nts.parse_header(PLAIN_PIXEL.splitlines()[0]) == [
        'NodeID', 'Time_hr', 'Nwt_mm', 'QpOut_mm-h', 'SoilMoist_[]'
    ]


def test_parse_header_of_a_tab_separated_qout_header():
    assert nts.parse_header(QOUT.splitlines()[0]) == ['Time_hr', 'Qstrm_m3-s', 'Hlev_m']


@pytest.mark.parametrize('text', [NUMBERED_PIXEL, PLAIN_PIXEL], ids=['numbered', 'plain'])
def test_read_node_file_reads_both_header_styles(tmp_path, text):
    frame = nts.read_node_file(_write(tmp_path / 'salas1656.pixel', text))

    assert frame['Time_hr'].tolist() == [1.0, 2.0]
    assert frame['Nwt_mm'].tolist() == [375.2, 376.2]
    assert frame['QpOut_mm-h'].tolist() == [0.5, 0.0]
    assert frame['NodeID'].tolist() == [1656.0, 1656.0]


def test_read_node_file_keeps_the_first_row_of_a_qout_file(tmp_path):
    """A qout file has no units row: its first data row is line two."""
    frame = nts.read_node_file(_write(tmp_path / 'salas_Outlet.qout', QOUT))

    assert frame['Time_hr'].tolist() == [0.0625, 0.125]
    assert frame['Qstrm_m3-s'].tolist() == [0.5, 0.7]


def test_node_file_variables_leaves_out_the_node_and_the_time(tmp_path):
    assert nts.node_file_variables(_write(tmp_path / 'a.pixel', PLAIN_PIXEL)) == [
        'Nwt_mm', 'QpOut_mm-h', 'SoilMoist_[]'
    ]
    assert nts.node_file_variables(_write(tmp_path / 'a_Outlet.qout', QOUT)) == ['Qstrm_m3-s', 'Hlev_m']


@pytest.mark.parametrize('text, message', [
    ('', 'Could not find the Time_hr column in the header of bad.pixel'),
    ('some text that is not a header\n1 2 3\n', 'Could not find the Time_hr column in the header of bad.pixel'),
    ('NodeID Time_hr Nwt_mm\n', 'bad.pixel has no data rows'),
    ('NodeID Time_hr Nwt_mm\n1 1.0\n', 'Line 2 of bad.pixel has 2 values for 3 columns'),
    ('NodeID Time_hr Nwt_mm\n1 1.0 2.0\n1 2.0 abc\n', 'Line 3 of bad.pixel holds a value that is not a number'),
    ('NodeID Time_hr Nwt_mm Nwt_mm\n1 1.0 2.0 3.0\n', 'The header of bad.pixel names a column twice'),
], ids=['empty', 'no time column', 'no rows', 'short row', 'not a number', 'duplicate column'])
def test_read_node_file_names_the_file_it_cannot_read(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        nts.read_node_file(_write(tmp_path / 'bad.pixel', text))


def test_read_node_file_skips_blank_lines(tmp_path):
    frame = nts.read_node_file(_write(tmp_path / 'a.pixel', PLAIN_PIXEL + '\n\n'))

    assert len(frame) == 2


def test_read_basin_file_reads_the_units_row(tmp_path):
    frame, units = nts.read_basin_file(_write(tmp_path / 'salas0240_00.mrf', MRF))

    assert frame['Time'].tolist() == [1.0, 2.0]
    assert frame['Srf'].tolist() == [0.25, 0.5]
    assert units == {'Time': 'hr', 'Srf': 'm3/s', 'FState': None}


@pytest.mark.parametrize('text, message', [
    ('Srf\tMAP\nm3/s\tmm/hr\n1\t2\n', 'Could not find the Time column in the header of bad.mrf'),
    ('Time\tSrf\nhr\tm3/s\n', 'bad.mrf has no data rows'),
    ('Time\tSrf\nhr\tm3/s\n1.0\n', 'Line 3 of bad.mrf has 1 values for 2 columns'),
], ids=['no time column', 'no rows', 'short row'])
def test_read_basin_file_names_the_file_it_cannot_read(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        nts.read_basin_file(_write(tmp_path / 'bad.mrf', text))


def test_pixel_files_by_node_uses_the_node_in_the_file_not_the_file_name(tmp_path):
    """salas1656.pixel also ends in 56: the file of node 56 is the one whose rows say 56."""
    node_1656 = _write(tmp_path / 'salas1656.pixel', PLAIN_PIXEL)
    node_56 = _write(tmp_path / 'salas56.pixel', PLAIN_PIXEL.replace('    1656 ', '      56 '))

    by_node = nts.pixel_files_by_node([node_1656, node_56])

    assert by_node == {1656: node_1656, 56: node_56}


def test_pixel_files_by_node_needs_the_node_column(tmp_path):
    path = _write(tmp_path / 'salas_Outlet.qout', QOUT)

    with pytest.raises(ValueError, match='Could not find the NodeID column in the header of salas_Outlet.qout'):
        nts.pixel_files_by_node([path])


def test_qout_files_by_point_takes_the_point_from_the_name():
    files = ['/out/hyd/salas_Outlet.qout', '/out/hyd/salas_1148.qout', '/out/hyd/small_basin_0.qout']

    assert nts.qout_files_by_point(files) == {
        'Outlet': '/out/hyd/salas_Outlet.qout', '1148': '/out/hyd/salas_1148.qout', '0': '/out/hyd/small_basin_0.qout'
    }


@pytest.mark.parametrize('relative_path, rows, columns', [
    ('datasets/voronoi/salas0.pixel', None, 49),
    ('czml_converters/simple_files/simple.pixel', 3, 7),
])
def test_read_node_file_reads_the_pixel_fixtures(relative_path, rows, columns):
    frame = nts.read_node_file(FILES / relative_path)

    assert frame.shape[1] == columns and (rows is None or len(frame) == rows)
    assert frame['Time_hr'].is_monotonic_increasing
