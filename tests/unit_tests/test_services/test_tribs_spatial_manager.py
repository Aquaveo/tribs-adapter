import os

from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager


def _touch(path):
    with open(path, 'w') as f:
        f.write('')
    return str(path)


def test_is_tribs_variable_output_file(tmp_path):
    assert TribsSpatialManager._is_tribs_variable_output_file(_touch(tmp_path / 'salas.0000_00d'))
    assert TribsSpatialManager._is_tribs_variable_output_file(_touch(tmp_path / 'salas.0700_00i'))
    # Companion files that are not spatial variable output
    companions = ['__meta__.json', 'salas_voi', 'salas_area', 'salas_reach', 'salas_width',
                  'x.gltf', 'x.glb', 'x_legend.png']
    for name in companions:
        assert not TribsSpatialManager._is_tribs_variable_output_file(_touch(tmp_path / name)), name
    # Directories
    os.mkdir(tmp_path / 'gltf')
    assert not TribsSpatialManager._is_tribs_variable_output_file(str(tmp_path / 'gltf'))


def test_find_voi_file(tmp_path):
    mesh_dir = tmp_path / 'mesh'
    output_dir = tmp_path / 'output'
    mesh_dir.mkdir()
    output_dir.mkdir()
    mesh_file = str(mesh_dir / 'salas')

    # Nothing available
    assert TribsSpatialManager._find_voi_file(mesh_file) is None
    assert TribsSpatialManager._find_voi_file(mesh_file, str(output_dir)) is None

    # In the output dataset collection (written by tRIBS with the _00d/_00i files)
    output_voi = _touch(output_dir / 'scenario_voi')
    assert TribsSpatialManager._find_voi_file(mesh_file, str(output_dir)) == output_voi

    # Next to the mesh files takes precedence
    mesh_voi = _touch(mesh_dir / 'salas_voi')
    assert TribsSpatialManager._find_voi_file(mesh_file, str(output_dir)) == mesh_voi
    assert TribsSpatialManager._find_voi_file(mesh_file) == mesh_voi


def test_parse_cluster_ports():
    parse = TribsSpatialManager._parse_cluster_ports
    assert parse('[8080]') == [8080]
    assert parse('[8081, 8082]') == [8081, 8082]
    assert parse('"[8080]"') == [8080]  # extra level of quoting left by an env loader
    assert parse('8080') == [8080]
    assert parse(None) == [8081, 8082, 8083, 8084]
    assert parse('not json') == [8081, 8082, 8083, 8084]
    assert parse('["a"]') == [8081, 8082, 8083, 8084]
