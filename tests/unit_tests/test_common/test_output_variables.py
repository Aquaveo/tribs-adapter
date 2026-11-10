"""Tests for the output variable table (tribs_adapter/common/output_variables.py)."""
import csv
from pathlib import Path

import pytest

from tribs_adapter.common import output_variables as ov
from tribs_adapter.common.czml_converters import get_file_variables, get_output_file_variables
from tribs_adapter.common.dataset_types import DatasetTypes

FILES = Path(__file__).resolve().parent.parent.parent / 'files'

EXAMPLEBASIN_MRF = (
    'Time Srf MAP RainMax RainMin FState MSM100 MSMRt MSMU MDGW MET SatPercent RainPercent AvSWE AvMelt AvSnSub '
    'AvSnEvap AvSTC AvDUInt AvSLHF AvSSHF AvSPHF AvSGHF AvSRLI AvSRLO AvSRSI AvInSn AvInSu AvInUn SCA'
).split()


def test_tables_cover_the_sheet():
    assert {kind: len(rows) for kind, rows in ov.OUTPUT_VARIABLES.items()} == {'qout': 3, 'mrf': 32, 'integrated': 75}


@pytest.mark.parametrize('kind', list(ov.OUTPUT_VARIABLES))
def test_table_rows_are_well_formed(kind):
    rows = ov.OUTPUT_VARIABLES[kind]
    keys = [alias for row in rows for alias in (row.name, *row.aliases)]
    assert len(keys) == len(set(keys)), f'duplicate name or alias in {kind}'
    offered = [row for row in rows if row.tier in (ov.Tier.PRIORITY, ov.Tier.SECONDARY)]
    assert [row.name for row in offered if not (row.label and row.description)] == []  # offered rows are documented
    assert [row.name for row in rows if not isinstance(row.factor, float)] == []


@pytest.mark.parametrize('dataset_type, kind', [
    (DatasetTypes.TRIBS_OUT_QOUT, ov.QOUT),
    (DatasetTypes.TRIBS_OUT_MRF, ov.MRF),
    (DatasetTypes.TRIBS_OUT_TIME_INTEGRATED, ov.INTEGRATED),
    (DatasetTypes.TRIBS_OUT_STATIONS, None),
    (DatasetTypes.TRIBS_OUT_PIXEL, None),
    (DatasetTypes.TRIBS_OUT_RFT, None),
    (DatasetTypes.TRIBS_TIN, None),
    (DatasetTypes.TRIBS_SDF_RAIN_GAUGE, None),
])
def test_kind_for_dataset_type(dataset_type, kind):
    assert ov.kind_for_dataset_type(dataset_type) == kind


@pytest.mark.parametrize('kind, name, expected_name', [
    ('mrf', 'MDGW', 'MDGW'),
    ('mrf', 'MGW', 'MDGW'),  # older tRIBS builds
    ('mrf', 'Max', 'RainMax'),
    ('mrf', '%Sat', 'SatPercent'),
    ('integrated', 'Aspct', 'Aspect'),
    ('qout', 'Z', None),  # exact per kind, never fuzzy
    ('mrf', 'mdgw', None),
    (None, 'Z', None),
    ('mrf', None, None),
])
def test_lookup_by_name_and_alias(kind, name, expected_name):
    row = ov.lookup(kind, name)
    assert (row.name if row is not None else None) == expected_name


def test_lookup_returns_the_table_row():
    assert ov.lookup('mrf', 'MDGW').label == 'Depth to Groundwater'
    assert ov.lookup('mrf', 'MGW') is ov.lookup('mrf', 'MDGW')
    assert ov.lookup('integrated', 'Z').tier is ov.Tier.PRIORITY


@pytest.mark.parametrize('layer_name, expected', [
    ('Qstrm_m3-s', ('Qstrm', 'm3-s')),
    ('Nwt_mm', ('Nwt', 'mm')),
    ('Srf_Hour_mm', ('Srf_Hour', 'mm')),
    ('Srf_[]', ('Srf', '[]')),
    ('MAP', ('MAP', None)),
    ('Bedrock_Depth_mm', ('Bedrock_Depth', 'mm')),
])
def test_split_unit_suffix(layer_name, expected):
    assert ov.split_unit_suffix(layer_name) == expected


def test_describe_returns_every_field():
    assert ov.describe('mrf', 'MSMRt') == dict(
        label='Root-Zone Soil Moisture', units='% saturation', tier='priority',
        description='Basin-average relative saturation (θ/θs) of the top 1m of soil.', factor=100.0,
    )
    assert ov.describe(None, 'Nwt', unit_token='mm') == dict(
        label='Nwt', units='mm', tier=None, description='', factor=1.0
    )


@pytest.mark.parametrize('kind, name, field, expected', [
    ('mrf', 'MGW', 'factor', 0.001),
    ('mrf', 'MGW', 'units', 'm'),
    ('mrf', 'AvSnSub', 'factor', -10.0),
    ('integrated', 'peakWE', 'units', 'mm'),
    ('integrated', 'EvpFrct', 'units', None),  # dimensionless
    ('mrf', 'Srf', 'tier', 'secondary'),
    # Hidden/ignored/index rows are described (for completeness) but offered no tier
    ('mrf', 'RainMax', 'tier', None),
    ('qout', 'Time', 'tier', None),
])
def test_describe_known_variables(kind, name, field, expected):
    assert ov.describe(kind, name)[field] == expected


@pytest.mark.parametrize('kind, name, kwargs, units', [
    (None, 'Qstrm', dict(unit_token='m3-s'), 'm³/s'),
    (None, 'Srf', dict(unit_token='[]'), None),
    (None, 'Odd', dict(unit_token='furlongs'), 'furlongs'),
    ('mrf', 'Hsrf', dict(file_units='m3/s'), 'm3/s'),
    ('mrf', 'Hsrf', dict(file_units='[]'), None),
    ('mrf', 'Hsrf', {}, None),
])
def test_describe_unknown_variables_take_the_units_from_the_file(kind, name, kwargs, units):
    assert ov.describe(kind, name, **kwargs)['units'] == units


OLD_MRF = 'Time Srf MAP Max Min FState MSM100 MSMRt MSMU MGW MET %Sat %Rain'.split()


@pytest.mark.parametrize('kind, names, expected', [
    ('mrf', EXAMPLEBASIN_MRF, [
        'MAP', 'MSMRt', 'MDGW', 'MET', 'AvSWE', 'AvSnSub', 'AvSnEvap', 'AvInSu',  # priority, file order
        'Srf', 'MSM100', 'MSMU', 'AvMelt', 'SCA',  # secondary, file order
    ]),
    ('mrf', OLD_MRF, ['MAP', 'MSMRt', 'MGW', 'MET', 'Srf', 'MSM100', 'MSMU']),
    ('qout', ['Qstrm', 'Hlev'], ['Qstrm']),
    ('integrated', ['ID', 'BndCd', 'Z', 'Mystery', 'CAr'], ['Z', 'CAr', 'Mystery']),
    (None, ['ID', 'Z', 'S', 'Nwt', 'Mu'], ['ID', 'Z', 'S', 'Nwt', 'Mu']),  # no table: everything, untouched
])
def test_visible_variables_orders_priority_then_secondary_then_unknown(kind, names, expected):
    assert ov.visible_variables(kind, names) == expected


def test_visible_variables_accepts_any_iterable():
    assert ov.visible_variables('mrf', iter(['MAP'])) == ['MAP']


@pytest.mark.parametrize('low, high, factor, expected', [
    (0.1, 0.9, 100, (10.0, 90.0)),
    (0, 2, -10, (-20, 0)),
    (None, 3, 2, (None, 3)),
    (1868.0, 2167.0, 1.0, (1868.0, 2167.0)),
])
def test_scale_range(low, high, factor, expected):
    assert ov.scale_range(low, high, factor) == expected


@pytest.mark.parametrize('kind, relative_path', [
    ('mrf', 'models/examplebasin/Output/Fall1996/hyd/examplebasin0010_00.mrf'),
    ('mrf', 'datasets/hyd/salas0700_00.mrf'),
    ('mrf', 'czml_converters/simple_files/simple.mrf'),
])
def test_every_mrf_fixture_column_is_in_the_table(kind, relative_path):
    names = get_output_file_variables(FILES / relative_path)
    unknown = [n for n in names if ov.lookup(kind, n) is None]
    assert unknown == [], f'{relative_path}: {unknown}'
    assert ov.visible_variables(kind, names)  # something is offered


@pytest.mark.parametrize('relative_path', [
    'datasets/hyd/salas_Outlet.qout',
    'czml_converters/simple_files/simple_Outlet.qout',
])
def test_every_qout_fixture_column_is_in_the_table(relative_path):
    layer_names = get_file_variables(FILES / relative_path, skip_cols=1)
    bases = [ov.split_unit_suffix(n)[0] for n in layer_names]
    assert [b for b in bases if ov.lookup('qout', b) is None] == []
    assert ov.visible_variables('qout', bases) == ['Qstrm']


@pytest.mark.parametrize('relative_path', [
    'spatial_manager/layers/time_integrated/examplebasin.0010_00i',
    'datasets/voronoi/salas.0000_00i',
])
def test_every_integrated_fixture_column_is_in_the_table(relative_path):
    with open(FILES / relative_path) as f:
        names = [c.strip() for c in next(csv.reader(f)) if c.strip()]
    unknown = [n for n in names if ov.lookup('integrated', n) is None]
    assert unknown == [], f'{relative_path}: {unknown}'
    offered = ov.visible_variables('integrated', names)
    assert offered[0] == 'Z' and 'BndCd' not in offered and 'ID' not in offered
