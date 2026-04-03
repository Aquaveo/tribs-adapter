import pytest


@pytest.fixture
def simple_file_directory(files_dir):
    return files_dir / 'czml_converters' / 'simple_files'


@pytest.fixture
def simple_pixel_file_path(simple_file_directory):
    return simple_file_directory / 'simple.pixel'


@pytest.fixture
def simple_qout_file_path(simple_file_directory):
    return simple_file_directory / 'simple_Outlet.qout'


@pytest.fixture
def simple_mrf_file_path(simple_file_directory):
    return simple_file_directory / 'simple.mrf'


@pytest.fixture
def simple_rft_file_path(simple_file_directory):
    return simple_file_directory / 'simple.rft'


@pytest.fixture
def simple_nodes_file_path(simple_file_directory):
    return simple_file_directory / 'simple.nodes'


@pytest.fixture
def simple_station_file_path(simple_file_directory):
    return simple_file_directory / 'simple.mdf'


@pytest.fixture
def expected_pixel_czml_file_path(simple_file_directory):
    return simple_file_directory / 'simple_pixel_expected.czml'


@pytest.fixture
def expected_qout_czml_file_path(simple_file_directory):
    return simple_file_directory / 'simple_qout_expected.czml'


@pytest.fixture
def expected_mrf_czml_file_path(simple_file_directory):
    return simple_file_directory / 'simple_mrf_expected.czml'


@pytest.fixture
def expected_rft_czml_file_path(simple_file_directory):
    return simple_file_directory / 'simple_rft_expected.czml'


@pytest.fixture
def expected_sdf_czml_file_path(simple_file_directory):
    return simple_file_directory / 'simple_sdf_expected.czml'
