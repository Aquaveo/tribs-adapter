from unittest import mock

import pytest
import pyproj

from tribs_adapter.workflows.utilities import (
    get_gmt_offset, safe_str, get_condor_fdb_root, get_condor_proj_dir, get_geoserver_ports, get_gdal_data_dirs,
    get_condor_env
)


def test_get_gmt_ofset():
    assert get_gmt_offset(0, 0) == 0
    assert get_gmt_offset(90, 0) == 0
    assert get_gmt_offset(0, 180) == 12
    assert (get_gmt_offset(42, -112) == -6.0 or get_gmt_offset(42, -112) == -7.0)


def test_safe_str():
    assert safe_str('abc123') == 'abc123'
    assert safe_str('abc 123') == 'abc_123'
    assert safe_str('abc_123') == 'abc_123'
    assert safe_str('abc!@#123') == 'abc123'
    assert safe_str('  abc 123  ') == 'abc_123'


def test_get_condor_fdb_root():
    with mock.patch.dict('os.environ', {'CONDOR_FDB_ROOT_DIR': '/some/path/condor'}, clear=True):
        assert get_condor_fdb_root(debug=True) == '/some/path/condor'
        assert get_condor_fdb_root(debug=False) == '/some/path/condor'

    with mock.patch.dict('os.environ', {'FDB_ROOT_DIR': '/some/path/nocondor'}, clear=True):
        assert get_condor_fdb_root(debug=True) == '/some/path/nocondor'
        assert get_condor_fdb_root(debug=False) == '/some/path/nocondor'

    with mock.patch.dict(
        'os.environ', {
            'FDB_ROOT_DIR': '/some/path/nocondor',
            'CONDOR_FDB_ROOT_DIR': '/some/path/condor',
        }, clear=True
    ):
        assert get_condor_fdb_root(debug=True) == '/some/path/condor'
        assert get_condor_fdb_root(debug=False) == '/some/path/condor'

    with pytest.raises(RuntimeError) as exc, mock.patch.dict('os.environ', {}, clear=True):
        get_condor_fdb_root(debug=True)
        get_condor_fdb_root(debug=False)

    assert 'CONDOR_FDB_ROOT_DIR and FDB_ROOT_DIR environment variables not set.' in str(exc.value)


def test_get_condor_proj_dir():
    with mock.patch.dict('os.environ', {}, clear=True):
        assert get_condor_proj_dir(debug=True) == {'PROJ_DATA': pyproj.datadir.get_data_dir(), 'PROJ_DEBUG': '3'}
        assert get_condor_proj_dir(debug=False) == {
            'PROJ_DATA': '/var/lib/condor/micromamba/envs/tethys/share/proj',
            'PROJ_DEBUG': '3'
        }

    with mock.patch.dict('os.environ', {'CONDOR_PROJ_LIB': '/some/path/on/condor'}, clear=True):
        assert get_condor_proj_dir(debug=True) == {'PROJ_DATA': '/some/path/on/condor', 'PROJ_DEBUG': '3'}
        assert get_condor_proj_dir(debug=False) == {'PROJ_DATA': '/some/path/on/condor', 'PROJ_DEBUG': '3'}


def test_get_gdal_data_dirs():
    with mock.patch.dict('os.environ', {"CONDA_PREFIX": "/some/path"}, clear=True):
        ret = get_gdal_data_dirs(debug=True)
        assert ret['GDAL_DATA'] == "/some/path/share/gdal"
        assert get_gdal_data_dirs(debug=False) == {
            'GDAL_DATA': '/var/lib/condor/micromamba/envs/tethys/share/gdal',
            'GDAL_DRIVER_PATH': '/var/lib/condor/micromamba/envs/tethys/lib/python3.1/site-packages/osgeo/gdalplugins'
        }

    with mock.patch.dict(
        'os.environ', {
            "CONDA_PREFIX": "/some/path",
            "CONDOR_GDAL_DATA": "/some/path/gdal",
            "CONDOR_GDAL_DRIVER_PATH": "/some/path/gdalplugins"
        },
        clear=True
    ):
        assert get_gdal_data_dirs(debug=True) == {
            'GDAL_DATA': "/some/path/gdal",
            'GDAL_DRIVER_PATH': "/some/path/gdalplugins"
        }
        assert get_gdal_data_dirs(debug=False) == {
            'GDAL_DATA': "/some/path/gdal",
            'GDAL_DRIVER_PATH': "/some/path/gdalplugins"
        }


def test_get_geoserver_ports():
    with mock.patch.dict('os.environ', {}, clear=True):
        assert get_geoserver_ports(debug=True) is None
        assert get_geoserver_ports(debug=False) is None

    with mock.patch.dict('os.environ', {'GEOSERVER_CLUSTER_PORTS': '[8080,8081]'}, clear=True):
        assert get_geoserver_ports(debug=True) == '[8080,8081]'
        assert get_geoserver_ports(debug=False) == '[8080,8081]'


@pytest.mark.skip
def test_get_condor_env_not_debug(mocker):
    # Unable to mock settings...
    mock_settings = mocker.patch('django.conf.settings')
    mock_settings.DEBUG = False
    with mock.patch.dict(
        'os.environ', {
            "CONDA_PREFIX": "/some/path",
            "CONDOR_GDAL_DATA": "/some/path/gdal",
            "CONDOR_GDAL_DRIVER_PATH": "/some/path/gdalplugins",
            "CONDOR_PROJ_LIB": "/some/path/on/condor",
            "CONDOR_FDB_ROOT_DIR": '/some/path/condor',
            "FDB_ROOT_DIR": '/some/path/nocondor',
            'GEOSERVER_CLUSTER_PORTS': '[8080,8081]',
        },
        clear=True
    ):
        assert get_condor_env() == ""


@pytest.mark.skip
def test_get_condor_env_debug(mocker):
    # Unable to mock settings...
    mock_settings = mocker.patch('django.conf.settings')
    mock_settings.DEBUG = True
    with mock.patch.dict(
        'os.environ', {
            "CONDA_PREFIX": "/some/path",
            "CONDOR_GDAL_DATA": "/some/path/gdal",
            "CONDOR_GDAL_DRIVER_PATH": "/some/path/gdalplugins",
            "CONDOR_PROJ_LIB": "/some/path/on/condor",
            "CONDOR_FDB_ROOT_DIR": '/some/path/condor',
            "FDB_ROOT_DIR": '/some/path/nocondor',
            'GEOSERVER_CLUSTER_PORTS': '[8080,8081]',
        },
        clear=True
    ):
        assert get_condor_env() == ""
