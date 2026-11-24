from collections import Counter
from datetime import datetime
import json
import os
import pandas as pd
import pytest
from tempfile import TemporaryDirectory

from tribs_adapter.common import czml_converters


def test_get_origin():
    list_of_nodes = [
        [0, 0, 0],
        [0, 1, 0],
        [1, 1, 0],
        [1, 0, 0],
    ]
    origin = czml_converters.get_origin(list_of_nodes)
    assert origin == [0.5, 0.5]


def test_get_extents():
    # 3 tuples making a pentagon
    list_of_nodes = [
        [0, 0, 0],
        [0, 70, 0],
        [60, 90, 0],
        [100, 0, 0],
    ]
    extents = czml_converters.get_extents(list_of_nodes)
    assert extents == [[0, 0], [100, 90]]

    extents = czml_converters.get_extents(list_of_nodes, flat=True)
    assert extents == [0, 0, 100, 90]


def test_get_nodes(simple_nodes_file_path):
    nodes, extent, origin, boundary_nodes, ids = czml_converters.get_nodes(simple_nodes_file_path, 4326)

    expected_nodes = [
        [25, 25, 4200],
        [75, 75, 4200],
        [0, 0, 4500],
        [100, 0, 4500],
        [100, 100, 4500],
        [0, 100, 4500],
    ]
    expected_extent = [[0.0, 0.0], [100.0, 100.0]]
    expected_origin = [50.0, 50.0]
    expected_boundary_nodes = [
        [0, 0, 4500],
        [100, 0, 4500],
        [100, 100, 4500],
        [0, 100, 4500],
    ]
    assert Counter(map(tuple, nodes)) == Counter(map(tuple, expected_nodes)), "The nodes do not have the same contents"
    assert Counter(map(tuple, boundary_nodes)) == Counter(
        map(tuple, expected_boundary_nodes)
    ), "The boundary nodes do not have the same contents"
    assert extent == expected_extent, "The extent does not match"
    assert origin == expected_origin, "The origin does not match"


def test_generate_czml_for_sdf_station(simple_station_file_path, expected_sdf_czml_file_path):
    """Test the generate_czml_for_sdf_station function."""
    # Create a temp directory for the written czml
    with TemporaryDirectory() as temp_dir:
        output_czml_sdf_path = os.path.join(temp_dir, 'czml')
        os.makedirs(output_czml_sdf_path)

        # Read simple mdf file into data frame
        with open(simple_station_file_path, 'r') as f:
            # Read the file into a df using the first line has headers
            df = pd.read_csv(f, header=0, sep=r'\s+')

        czml_converters.generate_czml_for_sdf_station(
            datetime(2024, 6, 1),
            10,
            1,
            output_czml_sdf_path,
            3976912,
            355228,
            1,
            simple_station_file_path,
            variables=['PA', 'RH', 'XC', 'US', 'TA', 'IS', 'IB', 'ID', 'R'],
            data=df,
            srid=32612
        )

        # Check that the file was written
        assert os.path.exists(output_czml_sdf_path)

        # Compare file contents
        assert len(os.listdir(output_czml_sdf_path)) == 9

        with open(os.path.join(output_czml_sdf_path, 'simple_IB.czml'), 'r') as generated_file:
            generated_content = generated_file.read()

        with open(expected_sdf_czml_file_path, 'r') as expected_file:
            expected_content = expected_file.read()
        assert generated_content == expected_content, "The generated CZML file does not match the expected content"


def test_write_geometry_czml_writes_static_features_without_a_clock(tmp_path):
    path = tmp_path / 'layer.czml'
    entities = [
        czml_converters.point_entity('point_7 [abc]', (-110.5, 34.25)),
        czml_converters.polygon_entity('polygon [abc]', [-110.0, 34.0, 0.0, -110.1, 34.0, 0.0, -110.1, 34.1, 0.0]),
    ]

    czml_converters.write_geometry_czml(str(path), 'Node Output', entities)

    document, point, polygon = json.loads(path.read_text())
    assert document == {'id': 'document', 'name': 'Node Output', 'version': '1.0'}  # no clock packet
    assert point['id'] == 'point_7 [abc]'
    assert point['position'] == {'cartographicDegrees': [-110.5, 34.25, 20]}
    assert point['point']['color'] == {'rgba': czml_converters.NO_VALUE_RGBA}
    assert polygon['id'] == 'polygon [abc]'
    assert polygon['polygon']['positions']['cartographicDegrees'] == [
        -110.0, 34.0, 0.0, -110.1, 34.0, 0.0, -110.1, 34.1, 0.0
    ]
    # Nothing in the document depends on time: the features show whatever the clock says
    assert 'availability' not in point and 'availability' not in polygon


def _frame(hours, **columns):
    return pd.DataFrame(dict(Time_hr=hours, **columns))


def test_write_value_layer_writes_one_values_file_per_variable(tmp_path):
    frames = {
        'point_1 [abc]': _frame([1.0, 2.0, 3.0], Nwt_mm=[10.0, 20.0, 30.0], Srf_mm=[0.0, 0.0, 0.0]),
        'point_2 [abc]': _frame([1.0, 2.0, 3.0], Nwt_mm=[5.0, 15.0, 45.0], Srf_mm=[0.0, 0.0, 0.0]),
    }
    variables = [dict(name='Nwt_mm', label='Nwt', units='mm', factor=1.0), dict(name='Srf_mm', factor=1.0)]

    written = czml_converters.write_value_layer(str(tmp_path), frames, 'Time_hr', variables, datetime(2004, 6, 1))

    nwt, srf = written
    assert (nwt['name'], nwt['label'], nwt['units']) == ('Nwt_mm', 'Nwt', 'mm')  # passed through
    assert (nwt['min'], nwt['max']) == (5.0, 45.0)  # over every feature and time
    # The times are those of the rows: the first row is hour 1, not the start of the run
    assert (nwt['start'], nwt['end'], nwt['step_hours']) == ('2004-06-01T01:00:00Z', '2004-06-01T03:00:00Z', 1.0)
    assert nwt['values'] == os.path.join('values', '000_Nwt_mm.json')
    assert srf['values'] == os.path.join('values', '001_Srf_mm.json')
    assert (srf['min'], srf['max']) == (0.0, 0.0)
    assert json.loads((tmp_path / nwt['values']).read_text()) == {
        'variable': 'Nwt_mm',
        'start': '2004-06-01T00:00:00Z',  # the hours count from the start of the run
        'hours': [1.0, 2.0, 3.0],
        'ids': ['point_1 [abc]', 'point_2 [abc]'],
        'values': [[10.0, 20.0, 30.0], [5.0, 15.0, 45.0]],
    }


def test_write_value_layer_converts_to_display_units(tmp_path):
    frames = {'polygon [abc]': pd.DataFrame(dict(Time=[1.0, 2.0], MDGW=[1000.0, 3000.0], MSMRt=[0.25, 0.5]))}
    variables = [dict(name='MDGW', factor=-0.001), dict(name='MSMRt', factor=100.0)]

    mdgw, msmrt = czml_converters.write_value_layer(str(tmp_path), frames, 'Time', variables, datetime(2004, 6, 1))

    # A negative factor does not swap the range, and the values file holds what the legend shows
    assert (mdgw['min'], mdgw['max']) == (-3.0, -1.0)
    assert json.loads((tmp_path / mdgw['values']).read_text())['values'] == [[-1.0, -3.0]]
    assert (msmrt['min'], msmrt['max']) == (25.0, 50.0)


def test_write_value_layer_lines_features_up_on_the_hours_of_their_rows(tmp_path):
    frames = {
        'point_1 [abc]': _frame([0.5, 1.0, 1.5], Q=[1.0, 2.0, 3.0]),
        'point_2 [abc]': _frame([1.0, 2.0], Q=[7.0, float('nan')]),  # other hours, and a missing value
    }

    (q,) = czml_converters.write_value_layer(
        str(tmp_path), frames, 'Time_hr', [dict(name='Q', factor=1.0)], datetime(2004, 6, 1)
    )

    values = json.loads((tmp_path / q['values']).read_text())
    assert values['hours'] == [0.5, 1.0, 1.5, 2.0]
    assert values['values'] == [[1.0, 2.0, 3.0, None], [None, 7.0, None, None]]
    assert (q['min'], q['max']) == (1.0, 7.0)


def test_write_value_layer_limits_the_clock_steps_of_finely_stepped_output(tmp_path):
    hours = [0.0625 * i for i in range(1, 3841)]  # qout: every 3.75 minutes for 240 hours
    frames = {'point_Outlet [abc]': _frame(hours, Q=[0.0] * len(hours))}

    (q,) = czml_converters.write_value_layer(
        str(tmp_path), frames, 'Time_hr', [dict(name='Q', factor=1.0)], datetime(2004, 6, 1)
    )

    assert q['step_hours'] == pytest.approx((240.0 - 0.0625) / czml_converters.MAX_CLOCK_STEPS)
    assert len(json.loads((tmp_path / q['values']).read_text())['hours']) == 3840  # the values keep every row


def test_write_value_layer_without_a_start_date_has_no_time_axis(tmp_path):
    frames = {'point_1 [abc]': _frame([1.0, 2.0], Q=[1.0, 2.0])}

    (q,) = czml_converters.write_value_layer(str(tmp_path), frames, 'Time_hr', [dict(name='Q')], 'not a date')

    assert (q['start'], q['end'], q['step_hours']) == (None, None, None)
    assert json.loads((tmp_path / q['values']).read_text())['start'] is None
    assert (q['min'], q['max']) == (1.0, 2.0)


def test_write_value_layer_names_files_safely_and_reports_a_variable_without_values(tmp_path):
    frames = {'point_1 [abc]': _frame([1.0], **{'Recharge_mm-hr': [float('nan')], 'SoilMoist_[]': [0.5]})}
    variables = [dict(name='Recharge_mm-hr'), dict(name='SoilMoist_[]'), dict(name='NotInTheFile')]

    recharge, moisture, missing = czml_converters.write_value_layer(
        str(tmp_path), frames, 'Time_hr', variables, datetime(2004, 6, 1)
    )

    assert moisture['values'] == os.path.join('values', '001_SoilMoist___.json')
    assert (recharge['min'], recharge['max']) == (None, None)
    assert (missing['min'], missing['max']) == (None, None)
    assert json.loads((tmp_path / missing['values']).read_text())['values'] == [[None]]
    assert moisture['step_hours'] is None  # a single time
