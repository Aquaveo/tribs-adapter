import os
from pathlib import Path
import pytest
import tempfile
import filecmp
import numpy as np

gltf_files = [
    'salas',
    'ms2_s1z1_notree',
    'ms2_s1z1_tree',
]


@pytest.mark.parametrize('mesh_basename', gltf_files)
def test_tRIBSMeshViz_init(tmv_factory, mesh_basename):
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg)

    assert isinstance(tmv.mesh_basename, Path)
    assert tmv.mesh_epsg == int(mesh_epsg)
    assert tmv.normals is None

    # Verify nodes and triangle arrays
    expected_path = tmv.mesh_basename.with_suffix('.init.npz')
    # Uncomment next line to update the mesh_basename_path.npz files
    # np.savez_compressed(expected_path, nodes=tmv.nodes, triangles=tmv.triangles)
    expected = np.load(expected_path)
    np.testing.assert_array_equal(tmv.nodes, expected['nodes'])
    np.testing.assert_array_equal(tmv.triangles, expected['triangles'])


@pytest.mark.parametrize('mesh_basename', gltf_files)
def test_tRIBSMeshViz_compute_normals(tmv_factory, files_dir, mesh_basename):
    mesh_basename = 'salas'
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg)

    assert tmv.normals is None
    tmv.compute_normals()

    # Verify nodes and triangle arrays
    expected_path = os.path.join(
        files_dir, 'unit_tests', 'test_io', mesh_basename, tmv.mesh_basename.with_suffix('.normals.npz')
    )
    # Uncomment next line to update the mesh_basename_path.npz files
    # np.savez_compressed(expected_path, nodes=tmv.nodes, triangles=tmv.triangles, normals=tmv.normals)
    expected = np.load(expected_path, allow_pickle=True)
    np.testing.assert_array_equal(tmv.normals, expected['normals'])


@pytest.mark.parametrize('mesh_basename', gltf_files)
def test_tRIBSMeshViz_to_gltf_no_normals(tmv_factory, files_dir, mesh_basename, get_expected_gltf):
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg)
    color_ramp_file = os.path.join(files_dir, '..', '..', 'tribs_adapter', 'templates', 'color_ramps', 'RedToBlue.png')
    temp_dir = tempfile.mkdtemp()
    gltf_file_base_name = os.path.join(temp_dir, f'{mesh_basename}')
    gltf_file = f'{gltf_file_base_name}.gltf'
    tmv.to_gltf(gltf_file_base_name, mesh_epsg, color_ramp_file=color_ramp_file)

    assert os.path.exists(gltf_file)
    assert filecmp.cmp(gltf_file, get_expected_gltf(mesh_basename), shallow=False)


@pytest.mark.parametrize('mesh_basename', gltf_files)
def test_tRIBSMeshViz_to_gltf_normals(tmv_factory, files_dir, mesh_basename, get_expected_gltf):
    # Test Data
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg)

    color_ramp_file = os.path.join(files_dir, '..', '..', 'tribs_adapter', 'templates', 'color_ramps', 'RedToBlue.png')

    # Compute Normals
    tmv.compute_normals()
    temp_dir = tempfile.mkdtemp()
    gltf_file_base_name = os.path.join(temp_dir, f'{mesh_basename}')
    gltf_file = f'{gltf_file_base_name}.gltf'
    tmv.to_gltf(gltf_file_base_name, mesh_epsg, color_ramp_file=color_ramp_file)

    expected_data = {}

    assert tmv.data == expected_data

    assert os.path.exists(gltf_file)
    assert filecmp.cmp(gltf_file, get_expected_gltf(mesh_basename), shallow=False)


def test_parse_output_data(tmv_factory):
    """Test that the output data is parsed correctly."""
    mesh_basename = 'salas'
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg)

    tmv._parse_output_data()


def test_reproject_nodes(tmv_factory):
    """Test that the nodes are reprojected to the correct EPSG."""
    mesh_basename = 'salas'
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg)

    nodes = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]])

    # Test reproject_nodes
    reprojected_nodes, to_epsg = tmv._reproject_nodes(nodes, from_epsg=4326)
    assert to_epsg == 4978
    expected_nodes = np.array([[6378137, 0, 0], [6377165.5, 111313.836, 0], [6376201, 111297, 110568.77],
                               [6377172, 0, 110568.77]],
                              dtype=np.float32)
    np.testing.assert_array_equal(reprojected_nodes, expected_nodes)


def test_output_files(tmv_factory):
    """Test that the output files are used when provided."""
    mesh_basename = 'salas_outputs'
    mesh_epsg = '32613'
    tm = tmv_factory(mesh_basename, mesh_epsg, output_files=['salas.0700_00d'])
    temp_dir = tempfile.mkdtemp()
    gltf_file_base_name = os.path.join(temp_dir, f'{mesh_basename}')
    tm.to_gltf(gltf_file_base_name, mesh_epsg, output_variables=['Z'])

    gltf_z_file = f'{gltf_file_base_name}_salas-0700_00d_Z.gltf'
    assert os.path.exists(gltf_z_file)
    assert len(os.listdir(temp_dir)) == 1

    temp_dir_2 = tempfile.mkdtemp()
    gltf2_file_base_name = os.path.join(temp_dir_2, f'{mesh_basename}')

    tm.to_gltf(gltf2_file_base_name, output_variables=['BadVar'])
    assert len(os.listdir(temp_dir_2)) == 0

    temp_dir_3 = tempfile.mkdtemp()
    gltf3_file_base_name = os.path.join(temp_dir_3, f'{mesh_basename}')

    tm.to_gltf(gltf3_file_base_name)
    assert len(os.listdir(temp_dir_3)) == 25
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_EvpSoil.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_ID.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Nt.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Rain.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Z.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_ActEvp.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_FlwVlc.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_LFlux.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Nwt.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_RootMoist.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_CAr.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_GFlux.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Mi.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Qpin.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_S.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_CanStorg.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_HFlux.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Mu.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Qpout.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_SoilMoist.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_ET.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Hlev.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Nf.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Qstrm.gltf")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Srf.gltf")


def test_given_color_ramp_file(tmv_factory, files_dir, get_expected_gltf):
    """Test that the color ramp file is used when provided."""
    mesh_basename = 'salas_outputs'
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg)

    temp_dir = tempfile.mkdtemp()
    gltf_file_base_name = os.path.join(temp_dir, f'{mesh_basename}')
    gltf_file = f'{gltf_file_base_name}.gltf'

    color_ramp_file = os.path.join(
        files_dir, '..', '..', 'tribs_adapter', 'templates', 'color_ramps', 'PinkToYellow.png'
    )

    tmv.to_gltf(gltf_file_base_name, output_variables=['Z'], color_ramp_file=color_ramp_file)

    assert os.path.exists(gltf_file)
    expected = get_expected_gltf(mesh_basename)
    assert filecmp.cmp(gltf_file, expected, shallow=False)


def test_reassign_bad_z_values(tmv_factory, caplog):
    """Test that the bad Z values are reassigned correctly."""
    mesh_basename = 'salas'
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg)

    # Simple test case, with all good values equal to 0:
    # Create a nodes array with some bad Z values
    nodes = np.array([[0, 0, -1e10], [1, 0, 0], [1, 1, -1e10], [0, 1, 0]], dtype=np.float32)
    # Reassign bad Z values
    reassigned = tmv._reassign_bad_z_values(nodes)
    # Check that the bad Z values have been replaced with 0
    expected_nodes = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]], dtype=np.float32)
    np.testing.assert_array_equal(reassigned, expected_nodes)

    # More complex test case, with points far away from each other, and differing Z values:
    # Create a nodes array with some bad Z values
    nodes = np.array([[0, 0, -1e10], [200000, 200000, -1e10], [10000, 10000, 99999], [100, 100, 100]], dtype=np.float32)
    # Reassign bad Z values
    reassigned = tmv._reassign_bad_z_values(nodes)
    # Check that the bad Z value has been replaced with 100 or 99999, depending on the closer good node
    expected_nodes = np.array([[0, 0, 100], [200000, 200000, 99999], [10000, 10000, 99999], [100, 100, 100]],
                              dtype=np.float32)
    np.testing.assert_array_equal(reassigned, expected_nodes)

    # Check for bad input (bad array shape, just X and Y values, no Z):
    bad_shape_nodes = np.array([[0, 0], [1, 1]], dtype=np.float32)
    with caplog.at_level('WARNING'):
        tmv._reassign_bad_z_values(bad_shape_nodes)
    assert 'Input array must have 3 columns' in caplog.text

    # Check for all bad Z values (every node has values near NODATA):
    all_bad_nodes = np.array([[0, 0, -1e10], [1, 1, -1e10]], dtype=np.float32)
    with caplog.at_level('WARNING'):
        tmv._reassign_bad_z_values(all_bad_nodes)
    assert 'Warning: No points with valid Z values found' in caplog.text
