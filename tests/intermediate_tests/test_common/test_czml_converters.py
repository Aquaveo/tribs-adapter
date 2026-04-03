from collections import Counter
from datetime import datetime
import os
import pandas as pd
from tempfile import TemporaryDirectory

from tribs_adapter.common import czml_converters


def test_get_pizel_file_variables(simple_pixel_file_path):
    pixel_file_variables = czml_converters.get_file_variables(simple_pixel_file_path)
    assert pixel_file_variables == [
        'Nwt_mm',
        'Nf_mm',
        'Nt_mm',
        'Mu_mm',
        'Mi_mm',
    ]


def test_get_output_file_variables(simple_rft_file_path, simple_mrf_file_path):
    rft_file_variables = czml_converters.get_output_file_variables(simple_rft_file_path)
    assert rft_file_variables == ['Hsrf', 'Sbsrf', 'Psrf', 'Satsrf']

    mrf_file_variables = czml_converters.get_output_file_variables(simple_mrf_file_path)
    assert mrf_file_variables == [
        'Srf',
        'MAP',
        'RainMax',
        'RainMin',
        'FState',
        'MSM100',
        'MSMRt',
        'MSMU',
        'MDGW',
    ]


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


def test_generate_czml_pixel_files(simple_nodes_file_path, simple_pixel_file_path, expected_pixel_czml_file_path):
    # Create a temp directory for the written czml
    with TemporaryDirectory() as temp_dir:
        output_czml_path = os.path.join(temp_dir, 'test_output.czml')
        czml_converters.generate_czml_for_pixel_files(
            simple_nodes_file_path, [simple_pixel_file_path],
            datetime(2020, 1, 1),
            1,
            3,
            output_czml_path,
            variable='Nwt_mm',
            dataset_id='test_dataset1234',
            srid=4326
        )

        # Check that the file was written
        assert os.path.exists(output_czml_path)

        # Compare file contents
        with open(output_czml_path, 'r') as generated_file:
            generated_content = generated_file.read()

        with open(expected_pixel_czml_file_path, 'r') as expected_file:
            expected_content = expected_file.read()

        assert generated_content == expected_content, "The generated CZML file does not match the expected content"


def test_generate_czml_for_qout_files(simple_nodes_file_path, simple_qout_file_path, expected_qout_czml_file_path):
    # Create a temp directory for the written czml
    with TemporaryDirectory() as temp_dir:
        output_czml_path = os.path.join(temp_dir, 'test_output.czml')
        czml_converters.generate_czml_for_qout_files(
            simple_nodes_file_path, [simple_qout_file_path],
            datetime(2020, 1, 1),
            1,
            3,
            output_czml_path,
            variable='Hlev_m',
            dataset_id='test_dataset1234',
            srid=4326
        )

        # Check that the file was written
        assert os.path.exists(output_czml_path)

        # Compare file contents
        with open(output_czml_path, 'r') as generated_file:
            generated_content = generated_file.read()

        with open(expected_qout_czml_file_path, 'r') as expected_file:
            expected_content = expected_file.read()

        assert generated_content == expected_content, "The generated CZML file does not match the expected content"


def test_generate_czml_for_mrf_and_rft_files(
    simple_nodes_file_path, simple_mrf_file_path, simple_rft_file_path, expected_mrf_czml_file_path,
    expected_rft_czml_file_path
):
    # Create a temp directory for the written czml
    with TemporaryDirectory() as temp_dir:
        output_czml_mrf_path = os.path.join(temp_dir, 'test_output_mrf.czml')
        czml_converters.generate_czml_for_mrf_and_rft_files(
            simple_nodes_file_path, [simple_mrf_file_path],
            datetime(2020, 1, 1),
            1,
            3,
            output_czml_mrf_path,
            variable='Srf',
            dataset_id='test_dataset1234',
            srid=4326
        )

        # Check that the file was written
        assert os.path.exists(output_czml_mrf_path)

        # Compare file contents
        with open(output_czml_mrf_path, 'r') as generated_file:
            generated_content = generated_file.read()

        with open(expected_mrf_czml_file_path, 'r') as expected_file:
            expected_content = expected_file.read()

        assert generated_content == expected_content, "The generated CZML file does not match the expected content"

        output_czml_rft_path = os.path.join(temp_dir, 'test_output_rft.czml')
        czml_converters.generate_czml_for_mrf_and_rft_files(
            simple_nodes_file_path, [simple_rft_file_path],
            datetime(2020, 1, 1),
            1,
            3,
            output_czml_rft_path,
            variable='Hsrf',
            dataset_id='test_dataset1234',
            srid=4326
        )

        # Check that the file was written
        assert os.path.exists(output_czml_rft_path)

        # Compare file contents
        with open(output_czml_rft_path, 'r') as generated_file:
            generated_content = generated_file.read()

        with open(expected_rft_czml_file_path, 'r') as expected_file:
            expected_content = expected_file.read()

        assert generated_content == expected_content, "The generated CZML file does not match the expected content"


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
