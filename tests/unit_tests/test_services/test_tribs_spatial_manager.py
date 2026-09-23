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
    for name in ['__meta__.json', 'salas_voi', 'salas_area', 'salas_reach', 'salas_width', 'x.gltf', 'x_legend.png']:
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
