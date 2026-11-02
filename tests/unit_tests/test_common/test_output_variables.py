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
    for kind, rows in ov.OUTPUT_VARIABLES.items():
        keys = [alias for row in rows for alias in (row.name, *row.aliases)]
        assert len(keys) == len(set(keys)), f'duplicate name or alias in {kind}'
        for row in rows:
            if row.tier in (ov.Tier.PRIORITY, ov.Tier.SECONDARY):
                assert row.label and row.description, row
            assert isinstance(row.factor, float), row


def test_kind_for_dataset_type():
    assert ov.kind_for_dataset_type(DatasetTypes.TRIBS_OUT_QOUT) == ov.QOUT
    assert ov.kind_for_dataset_type(DatasetTypes.TRIBS_OUT_MRF) == ov.MRF
    assert ov.kind_for_dataset_type(DatasetTypes.TRIBS_OUT_TIME_INTEGRATED) == ov.INTEGRATED
    for other in (DatasetTypes.TRIBS_OUT_STATIONS, DatasetTypes.TRIBS_OUT_PIXEL, DatasetTypes.TRIBS_OUT_RFT,
                  DatasetTypes.TRIBS_TIN, DatasetTypes.TRIBS_SDF_RAIN_GAUGE):
        assert ov.kind_for_dataset_type(other) is None


def test_lookup_by_name_and_alias():
    assert ov.lookup('mrf', 'MDGW').label == 'Depth to Groundwater'
    assert ov.lookup('mrf', 'MGW') is ov.lookup('mrf', 'MDGW')  # older tRIBS builds
    assert ov.lookup('mrf', 'Max').name == 'RainMax'
    assert ov.lookup('mrf', '%Sat').name == 'SatPercent'
    assert ov.lookup('integrated', 'Aspct').name == 'Aspect'
    assert ov.lookup('integrated', 'Z').tier is ov.Tier.PRIORITY
    assert ov.lookup('qout', 'Z') is None  # exact per kind, never fuzzy
    assert ov.lookup('mrf', 'mdgw') is None
    assert ov.lookup(None, 'Z') is None
    assert ov.lookup('mrf', None) is None


def test_split_unit_suffix():
    assert ov.split_unit_suffix('Qstrm_m3-s') == ('Qstrm', 'm3-s')
    assert ov.split_unit_suffix('Nwt_mm') == ('Nwt', 'mm')
    assert ov.split_unit_suffix('Srf_Hour_mm') == ('Srf_Hour', 'mm')
    assert ov.split_unit_suffix('Srf_[]') == ('Srf', '[]')
    assert ov.split_unit_suffix('MAP') == ('MAP', None)
    assert ov.split_unit_suffix('Bedrock_Depth_mm') == ('Bedrock_Depth', 'mm')


def test_describe_known_variables():
    assert ov.describe('mrf', 'MSMRt') == dict(
        label='Root-Zone Soil Moisture', units='% saturation', tier='priority',
        description='Basin-average relative saturation (θ/θs) of the top 1m of soil.', factor=100.0,
    )
    assert ov.describe('mrf', 'MGW')['factor'] == 0.001 and ov.describe('mrf', 'MGW')['units'] == 'm'
    assert ov.describe('mrf', 'AvSnSub')['factor'] == -10.0
    assert ov.describe('integrated', 'peakWE')['units'] == 'mm'
    assert ov.describe('integrated', 'EvpFrct')['units'] is None  # dimensionless
    assert ov.describe('mrf', 'Srf')['tier'] == 'secondary'
    # Hidden/ignored/index rows are described (for completeness) but offered no tier
    assert ov.describe('mrf', 'RainMax')['tier'] is None
    assert ov.describe('qout', 'Time')['tier'] is None


def test_describe_unknown_variables():
    assert ov.describe(None, 'Nwt', unit_token='mm') == dict(
        label='Nwt', units='mm', tier=None, description='', factor=1.0
    )
    assert ov.describe(None, 'Qstrm', unit_token='m3-s')['units'] == 'm³/s'
    assert ov.describe(None, 'Srf', unit_token='[]')['units'] is None
    assert ov.describe(None, 'Odd', unit_token='furlongs')['units'] == 'furlongs'
    assert ov.describe('mrf', 'Hsrf', file_units='m3/s')['units'] == 'm3/s'
    assert ov.describe('mrf', 'Hsrf', file_units='[]')['units'] is None
    assert ov.describe('mrf', 'Hsrf')['units'] is None


def test_visible_variables_orders_priority_then_secondary_then_unknown():
    assert ov.visible_variables('mrf', EXAMPLEBASIN_MRF) == [
        'MAP', 'MSMRt', 'MDGW', 'MET', 'AvSWE', 'AvSnSub', 'AvSnEvap', 'AvInSu',  # priority, file order
        'Srf', 'MSM100', 'MSMU', 'AvMelt', 'SCA',  # secondary, file order
    ]
    old_mrf = 'Time Srf MAP Max Min FState MSM100 MSMRt MSMU MGW MET %Sat %Rain'.split()
    assert ov.visible_variables('mrf', old_mrf) == ['MAP', 'MSMRt', 'MGW', 'MET', 'Srf', 'MSM100', 'MSMU']
    assert ov.visible_variables('qout', ['Qstrm', 'Hlev']) == ['Qstrm']
    assert ov.visible_variables('integrated', ['ID', 'BndCd', 'Z', 'Mystery', 'CAr']) == ['Z', 'CAr', 'Mystery']
    names = ['ID', 'Z', 'S', 'Nwt', 'Mu']
    assert ov.visible_variables(None, names) == names  # no table: everything, untouched
    assert ov.visible_variables('mrf', iter(['MAP'])) == ['MAP']


def test_scale_range():
    assert ov.scale_range(0.1, 0.9, 100) == (10.0, 90.0)
    assert ov.scale_range(0, 2, -10) == (-20, 0)
    assert ov.scale_range(None, 3, 2) == (None, 3)
    assert ov.scale_range(1868.0, 2167.0, 1.0) == (1868.0, 2167.0)


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
