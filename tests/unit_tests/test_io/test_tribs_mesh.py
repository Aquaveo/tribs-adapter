import os
from pathlib import Path
import pytest
import tempfile
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
def test_tRIBSMeshViz_to_gltf_no_normals(tmv_factory, files_dir, mesh_basename, get_expected_gltf, assert_gltf_equal):
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg, voronoi_cells=False)  # Fixtures are TIN renderings
    color_ramp_file = os.path.join(files_dir, '..', '..', 'tribs_adapter', 'templates', 'color_ramps', 'RedToBlue.png')
    temp_dir = tempfile.mkdtemp()
    gltf_file_base_name = os.path.join(temp_dir, f'{mesh_basename}')
    gltf_file = f'{gltf_file_base_name}.gltf'
    tmv.to_gltf(gltf_file_base_name, mesh_epsg, color_ramp_file=color_ramp_file, binary=False)
    assert os.path.exists(gltf_file)
    assert_gltf_equal(gltf_file, get_expected_gltf(mesh_basename))


@pytest.mark.parametrize('mesh_basename', gltf_files)
def test_tRIBSMeshViz_to_gltf_normals(tmv_factory, files_dir, mesh_basename, get_expected_gltf, assert_gltf_equal):
    # Test Data
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg, voronoi_cells=False)  # Fixtures are TIN renderings

    color_ramp_file = os.path.join(files_dir, '..', '..', 'tribs_adapter', 'templates', 'color_ramps', 'RedToBlue.png')

    # Compute Normals
    tmv.compute_normals()
    temp_dir = tempfile.mkdtemp()
    gltf_file_base_name = os.path.join(temp_dir, f'{mesh_basename}')
    gltf_file = f'{gltf_file_base_name}.gltf'
    tmv.to_gltf(gltf_file_base_name, mesh_epsg, color_ramp_file=color_ramp_file, binary=False)

    expected_data = {}

    assert tmv.data == expected_data

    assert os.path.exists(gltf_file)
    assert_gltf_equal(gltf_file, get_expected_gltf(mesh_basename))


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

    gltf_z_file = f'{gltf_file_base_name}_salas-0700_00d_Z.glb'
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
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_EvpSoil.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_ID.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Nt.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Rain.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Z.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_ActEvp.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_FlwVlc.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_LFlux.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Nwt.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_RootMoist.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_CAr.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_GFlux.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Mi.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Qpin.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_S.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_CanStorg.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_HFlux.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Mu.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Qpout.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_SoilMoist.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_ET.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Hlev.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Nf.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Qstrm.glb")
    assert os.path.exists(f"{gltf3_file_base_name}_salas-0700_00d_Srf.glb")


def test_given_color_ramp_file(tmv_factory, files_dir, get_expected_gltf, assert_gltf_equal):
    """Test that the color ramp file is used when provided."""
    mesh_basename = 'salas_outputs'
    mesh_epsg = '32613'
    tmv = tmv_factory(mesh_basename, mesh_epsg, voronoi_cells=False)  # Fixture is a TIN rendering

    temp_dir = tempfile.mkdtemp()
    gltf_file_base_name = os.path.join(temp_dir, f'{mesh_basename}')
    gltf_file = f'{gltf_file_base_name}.gltf'

    color_ramp_file = os.path.join(
        files_dir, '..', '..', 'tribs_adapter', 'templates', 'color_ramps', 'PinkToYellow.png'
    )

    tmv.to_gltf(gltf_file_base_name, output_variables=['Z'], color_ramp_file=color_ramp_file, binary=False)

    assert os.path.exists(gltf_file)
    expected = get_expected_gltf(mesh_basename)
    assert_gltf_equal(gltf_file, expected)


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


# ----------------------------------------------------------------------------------------------------------------------
# Voronoi cells
# ----------------------------------------------------------------------------------------------------------------------
def _read_gltf_accessors(gltf_file):
    """Decode indices, positions, normals and texture coordinates of a glTF (.glb or .gltf) from tRIBSMeshViz."""
    import pygltflib

    gltf = pygltflib.GLTF2().load(str(gltf_file))
    if str(gltf_file).endswith('.glb'):
        buffer = gltf.binary_blob()
    else:
        buffer = gltf.get_data_from_buffer_uri(gltf.buffers[0].uri)
    dtypes = {5125: np.uint32, 5126: np.float32}
    counts = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3}

    def accessor(index):
        acc = gltf.accessors[index]
        view = gltf.bufferViews[acc.bufferView]
        n = counts[acc.type]
        data = np.frombuffer(
            buffer, dtype=dtypes[acc.componentType], count=acc.count * n, offset=(view.byteOffset or 0)
        )
        return data.reshape(-1, n) if n > 1 else data

    return accessor(0).reshape(-1, 3), accessor(1), accessor(2), accessor(3)


def test_read_voi_file(tmv_factory, gltf_dir):
    """The _voi file next to the mesh is picked up and parsed into one cell per active node."""
    from tribs_adapter.io.tribs_mesh import tRIBSMeshViz

    tmv = tmv_factory('salas_outputs', '32613')
    assert tmv.voi_file == gltf_dir / 'salas_outputs' / 'salas_outputs_voi'

    ids, centers, polygons = tRIBSMeshViz.read_voi_file(tmv.voi_file)
    assert len(ids) == len(centers) == len(polygons) == 1681
    np.testing.assert_array_equal(ids, np.arange(1681))
    # tRIBS node IDs are the row indices of the .nodes file, so the cell centers coincide with the nodes
    np.testing.assert_allclose(centers, tmv.nodes[ids, :2], atol=0.01)
    assert min(len(p) for p in polygons) == 3
    assert max(len(p) for p in polygons) == 12
    assert all(p.shape[1] == 2 for p in polygons)

    # The cells are the ones of the active (interior and stream) nodes only
    active = [i for i, code in enumerate(tmv.boundary_types) if code in ('0', '3')]
    np.testing.assert_array_equal(tmv.voronoi['ids'], active)
    assert len(tmv.voronoi['polygons']) == 1681


def test_read_voi_file_format(tmp_path):
    """Parse the tRIBS _voi format: 'id,x,y' header, 'x,y' vertices, END per polygon, double END at the end."""
    from tribs_adapter.io.tribs_mesh import tRIBSMeshViz

    voi_file = tmp_path / 'test_voi'
    voi_file.write_text(
        "0,10.0,10.0\n5,5\n15,5\n15,15\n5,15\nEND\n"
        "7,30.0,10.0\n25,5\n35,5\n30,15\nEND\n"
        "END\n"
    )
    ids, centers, polygons = tRIBSMeshViz.read_voi_file(voi_file)
    np.testing.assert_array_equal(ids, [0, 7])
    np.testing.assert_array_equal(centers, [[10.0, 10.0], [30.0, 10.0]])
    np.testing.assert_array_equal(polygons[0], [[5, 5], [15, 5], [15, 15], [5, 15]])
    np.testing.assert_array_equal(polygons[1], [[25, 5], [35, 5], [30, 15]])

    # A missing trailing END keeps the last polygon
    voi_file.write_text("3,1.0,1.0\n0,0\n2,0\n1,2\n")
    ids, _, polygons = tRIBSMeshViz.read_voi_file(voi_file)
    np.testing.assert_array_equal(ids, [3])
    assert polygons[0].shape == (3, 2)

    # Vertex before header is an error
    voi_file.write_text("0,0\n1,1\nEND\n")
    with pytest.raises(ValueError):
        tRIBSMeshViz.read_voi_file(voi_file)


def test_voi_file_validation(mesh_basename_factory, tmp_path):
    """A _voi file that does not belong to the mesh is rejected."""
    from tribs_adapter.io.tribs_mesh import tRIBSMeshViz

    mesh_basename = mesh_basename_factory('salas')  # No _voi file in this directory

    # No file next to the mesh: none is used
    assert tRIBSMeshViz(mesh_basename, 32613).voi_file is None

    # Explicit file that does not exist
    with pytest.raises(FileNotFoundError):
        tRIBSMeshViz(mesh_basename, 32613, voi_file=tmp_path / 'nope_voi')

    # Cell center does not coincide with the node with the same ID
    bad_center = tmp_path / 'bad_center_voi'
    bad_center.write_text("0,0.0,0.0\n1,0\n0,1\n-1,0\nEND\nEND\n")
    with pytest.raises(ValueError, match='does not match mesh'):
        tRIBSMeshViz(mesh_basename, 32613, voi_file=bad_center).voronoi

    # Node ID outside of the mesh
    bad_id = tmp_path / 'bad_id_voi'
    bad_id.write_text("999999,0.0,0.0\n1,0\n0,1\n-1,0\nEND\nEND\n")
    with pytest.raises(ValueError, match='outside of the mesh'):
        tRIBSMeshViz(mesh_basename, 32613, voi_file=bad_id).voronoi

    # Empty file
    empty = tmp_path / 'empty_voi'
    empty.write_text("END\n")
    with pytest.raises(ValueError, match='No Voronoi cells'):
        tRIBSMeshViz(mesh_basename, 32613, voi_file=empty).voronoi


def test_compute_voronoi_from_tin(tmv_factory):
    """Cells computed from the TIN reproduce the cells tRIBS wrote to the _voi file."""
    from tribs_adapter.io.tribs_mesh import tRIBSMeshViz

    tmv = tmv_factory('salas_outputs', '32613')
    ids, polygons = tmv.compute_voronoi_from_tin()
    voi_ids, _, voi_polygons = tRIBSMeshViz.read_voi_file(tmv.voi_file)

    np.testing.assert_array_equal(ids, voi_ids)
    matches = 0
    for computed, expected in zip(polygons, voi_polygons):
        if len(computed) != len(expected):
            continue  # tRIBS repairs a few cells with degenerate triangles
        start = np.argmin(np.hypot(*(computed - expected[0]).T))
        if np.allclose(np.roll(computed, -start, axis=0), expected, atol=1e-3):
            matches += 1
    assert matches >= 0.95 * len(ids)

    # Without a _voi file the computed cells are used
    tmv.voi_file = None
    assert len(tmv.voronoi['ids']) == len(ids)


def test_voronoi_gltf_values_join_by_id(tmv_factory):
    """Each Voronoi cell is a fan of triangles with a single color given by the value with the cell's node ID."""
    mesh_basename = 'salas_outputs'
    tmv = tmv_factory(mesh_basename, '32613', output_files=['salas.0700_00d'])
    temp_dir = tempfile.mkdtemp()
    gltf_file_base_name = os.path.join(temp_dir, mesh_basename)
    tmv.to_gltf(gltf_file_base_name, '32613', output_variables=['ID'], generate_legend=True)

    gltf_file = f'{gltf_file_base_name}_salas-0700_00d_ID.glb'
    assert os.path.exists(gltf_file)
    assert os.path.exists(f'{gltf_file_base_name}_salas-0700_00d_ID_legend.png')

    triangles, positions, normals, texcoords = _read_gltf_accessors(gltf_file)
    geometry = tmv._build_voronoi_geometry()
    cell_ids = tmv.voronoi['ids']
    vertex_cell = geometry['vertex_cell']

    # One center vertex + ring per cell, one triangle per ring edge, vertices are not shared between cells
    ring_sizes = np.array([len(p) for p in tmv.voronoi['polygons']])
    assert len(positions) == (ring_sizes + 1).sum()
    assert len(triangles) == ring_sizes.sum()
    assert triangles.max() == len(positions) - 1
    assert len(normals) == len(texcoords) == len(positions)
    np.testing.assert_allclose(np.linalg.norm(normals, axis=1), 1.0, atol=1e-3)

    # All vertices of a cell share the same texture coordinate, i.e. the cell has one uniform color
    for cell_index in range(len(cell_ids)):
        cell_uv = texcoords[vertex_cell == cell_index]
        assert np.ptp(cell_uv, axis=0).max() == 0

    # The variable 'ID' is the node ID itself: normalized value == ID / max(ID), joined by ID not by row position
    first_vertex = np.r_[0, np.cumsum(ring_sizes + 1)[:-1]]
    np.testing.assert_allclose(texcoords[first_vertex, 1], cell_ids / cell_ids.max(), atol=1e-6)
    # Every active node has a value, so nothing is transparent (u == 1)
    assert not (texcoords[:, 0] == 1.0).any()


def test_voronoi_gltf_missing_values_are_transparent(tmv_factory, gltf_dir):
    """Cells whose node ID has no row in the output file get the transparent texture coordinate."""
    output_file = os.path.join(tempfile.mkdtemp(), 'partial.0000_00d')
    with open(output_file, 'w') as f:
        f.write("ID,Foo\n1,10\n0,20\n999999,30\n")  # Rows out of node order, plus an ID outside of the mesh

    mesh_basename = 'salas_outputs'
    tmv = tmv_factory(mesh_basename, '32613')
    tmv.output_files = [output_file]
    temp_dir = tempfile.mkdtemp()
    gltf_file_base_name = os.path.join(temp_dir, mesh_basename)
    tmv.to_gltf(gltf_file_base_name, '32613', output_variables=['Foo'])

    _, _, _, texcoords = _read_gltf_accessors(f'{gltf_file_base_name}_partial-0000_00d_Foo.glb')
    geometry = tmv._build_voronoi_geometry()
    cell_uv = texcoords[np.r_[0, np.cumsum(np.bincount(geometry['vertex_cell']))[:-1]]]
    np.testing.assert_allclose(cell_uv[0], [0.0, 1.0])  # Node 0 -> 20 (max)
    np.testing.assert_allclose(cell_uv[1], [0.0, 0.0])  # Node 1 -> 10 (min)
    assert (cell_uv[2:] == 1.0).all()  # No value -> transparent (u, v) == (1, 1)


def test_voronoi_cells_disabled_renders_tin(tmv_factory):
    """voronoi_cells=False keeps the previous behavior of putting values on the TIN vertices."""
    from tribs_adapter.io.tribs_mesh import tRIBSMeshViz

    mesh_basename = 'salas_outputs'
    tmv = tmv_factory(mesh_basename, '32613', output_files=['salas.0700_00d'])
    tmv_tin = tRIBSMeshViz(tmv.mesh_basename, '32613', output_files=tmv.output_files, voronoi_cells=False)
    temp_dir = tempfile.mkdtemp()
    gltf_file_base_name = os.path.join(temp_dir, mesh_basename)
    tmv_tin.to_gltf(gltf_file_base_name, '32613', output_variables=['Z'])

    triangles, positions, _, _ = _read_gltf_accessors(f'{gltf_file_base_name}_salas-0700_00d_Z.glb')
    assert len(positions) == len(tmv_tin.nodes)
    np.testing.assert_array_equal(triangles, tmv_tin.triangles)


def test_interpolate_array(tmv_factory):
    tmv = tmv_factory('salas', '32613')
    assert tmv._interpolate_array([1.0, 3.0, None, 2.0]) == [0.0, 1.0, None, 0.5]
    # Constant values map to the bottom of the ramp and keep the missing values
    assert tmv._interpolate_array([5.0, 5.0, None]) == [0.0, 0.0, None]


def test_generate_legend_for_values(tmv_factory, files_dir, tmp_path, caplog):
    tmv = tmv_factory('salas', '32613')
    color_ramp_file = os.path.join(files_dir, '..', '..', 'tribs_adapter', 'templates', 'color_ramps', 'RedToBlue.png')
    legend_path = tmp_path / 'legend.png'

    with caplog.at_level('WARNING'):
        assert tmv._generate_legend_for_values([None, None], legend_path, color_ramp_file) is False
    assert 'No values to generate a legend' in caplog.text
    assert not legend_path.exists()

    assert tmv._generate_legend_for_values([None, 1.0, 2.0], legend_path, color_ramp_file) is True
    assert legend_path.exists()


def test_voronoi_vertices_lie_on_tin_surface(tmv_factory):
    """Cell vertices are on the TIN surface and neighboring cells share identical vertex elevations (no gaps/spikes)."""
    import matplotlib.tri as mtri

    tmv = tmv_factory('salas_outputs', '32613')
    geometry = tmv._build_voronoi_geometry()
    positions = geometry['positions']
    ring_sizes = np.array([len(p) for p in tmv.voronoi['polygons']])
    centers = np.r_[0, np.cumsum(ring_sizes + 1)[:-1]]
    is_center = np.zeros(len(positions), dtype=bool)
    is_center[centers] = True

    # Cell centers are the nodes themselves
    np.testing.assert_allclose(positions[centers], tmv.nodes[tmv.voronoi['ids']].astype(np.float64), atol=1e-4)

    # Ring vertices interpolate the TIN surface (independent check with matplotlib's linear TIN interpolator)
    ring = positions[~is_center]
    nodes = tmv.nodes.astype(np.float64)
    interpolator = mtri.LinearTriInterpolator(mtri.Triangulation(nodes[:, 0], nodes[:, 1], tmv.triangles), nodes[:, 2])
    expected = interpolator(ring[:, 0], ring[:, 1])
    assert not expected.mask.any()  # all vertices inside the TIN for this mesh
    np.testing.assert_allclose(ring[:, 2], expected.filled(np.nan), atol=1e-3)

    # A vertex shared by neighboring cells has exactly one elevation
    _, inverse = np.unique(np.round(ring[:, :2], 3), axis=0, return_inverse=True)
    inverse = inverse.ravel()
    z_min = np.full(inverse.max() + 1, np.inf)
    z_max = np.full(inverse.max() + 1, -np.inf)
    np.minimum.at(z_min, inverse, ring[:, 2])
    np.maximum.at(z_max, inverse, ring[:, 2])
    assert (z_max - z_min).max() < 1e-6


def test_tin_surface_elevations_outside_tin(tmv_factory):
    """Points outside of the TIN are projected onto the nearest triangle instead of being extrapolated."""
    tmv = tmv_factory('salas', '32613')
    nodes = tmv.nodes.astype(np.float64)
    node = int(np.argmax(nodes[:, 0]))  # Easternmost node: anything further east is outside of the TIN
    far_east = np.array([[nodes[node, 0] + 500.0, nodes[node, 1]]])
    (z,) = tmv._tin_surface_elevations(far_east, np.array([node]))
    assert nodes[:, 2].min() <= z <= nodes[:, 2].max()
    # Identical points always get identical elevations
    z2 = tmv._tin_surface_elevations(np.vstack([far_east, far_east]), np.array([node, node]))
    assert z2[0] == z2[1] == z


def test_glb_output(tmv_factory, files_dir):
    """Binary glTF is the default: one .glb per variable with the color ramp stored in the binary buffer."""
    import pygltflib

    mesh_basename = 'salas_outputs'
    tmv = tmv_factory(mesh_basename, '32613', output_files=['salas.0700_00d'])
    temp_dir = tempfile.mkdtemp()
    base = os.path.join(temp_dir, mesh_basename)
    tmv.to_gltf(base, '32613', output_variables=['S'], generate_legend=True)
    tmv.to_gltf(base, '32613', output_variables=['S'], binary=False)
    glb_file = f'{base}_salas-0700_00d_S.glb'
    gltf_file = f'{base}_salas-0700_00d_S.gltf'
    assert os.path.exists(glb_file) and os.path.exists(gltf_file)
    assert os.path.exists(f'{base}_salas-0700_00d_S_legend.png')

    with open(glb_file, 'rb') as f:
        assert f.read(4) == b'glTF'
    glb = pygltflib.GLTF2().load(glb_file)
    assert glb.buffers[0].uri is None
    assert glb.images[0].uri is None and glb.images[0].mimeType == 'image/png'
    image_view = glb.bufferViews[glb.images[0].bufferView]
    assert image_view.byteOffset % 4 == 0
    with open(os.path.join(files_dir, '..', '..', 'tribs_adapter', 'templates', 'color_ramps', 'TopoAtlasShader.png'),
              'rb') as f:
        ramp = f.read()
    assert glb.binary_blob()[image_view.byteOffset:image_view.byteOffset + image_view.byteLength] == ramp
    assert glb.buffers[0].byteLength == len(glb.binary_blob())
    # The .glb is smaller than the base64 .gltf, and carries the same geometry and values
    assert os.path.getsize(glb_file) < 0.8 * os.path.getsize(gltf_file)
    for a, b in zip(_read_gltf_accessors(glb_file), _read_gltf_accessors(gltf_file)):
        np.testing.assert_array_equal(a, b)


def test_bare_mesh_renders_voronoi_cells_by_elevation(tmv_factory):
    """A TIN dataset without simulation output is rendered as Voronoi cells colored by node elevation."""
    mesh_basename = 'salas_outputs'
    tmv = tmv_factory(mesh_basename, '32613')
    temp_dir = tempfile.mkdtemp()
    base = os.path.join(temp_dir, mesh_basename)
    meta = tmv.to_gltf(base, '32613', generate_legend=True)
    glb_file = f'{base}.glb'
    assert os.path.exists(glb_file) and os.path.exists(f'{base}_legend.png')
    assert len(meta['gltfs']) == 1

    triangles, positions, _, texcoords = _read_gltf_accessors(glb_file)
    geometry = tmv._build_voronoi_geometry()
    assert len(positions) == len(geometry['positions'])
    assert len(triangles) == len(geometry['triangles'])

    # One uniform color per cell, ordered by the cell node's elevation
    cell_ids = tmv.voronoi['ids']
    ring_sizes = np.array([len(p) for p in tmv.voronoi['polygons']])
    first_vertex = np.r_[0, np.cumsum(ring_sizes + 1)[:-1]]
    z = tmv.nodes[cell_ids, 2].astype(np.float64)
    expected = (z - z.min()) / (z.max() - z.min())
    np.testing.assert_allclose(texcoords[first_vertex, 1], expected, atol=1e-6)
    assert not (texcoords[:, 0] == 1.0).any()


def _write_mesh(directory, name, nodes, triangles):
    """Write minimal tRIBS .nodes/.z/.tri files. nodes: (x, y, z, boundary code); triangles: vertex index triples."""
    base = os.path.join(directory, name)
    with open(f'{base}.nodes', 'w') as f:
        f.write(f' 0.000000\n{len(nodes)}\n')
        for x, y, _, code in nodes:
            f.write(f'{x} {y} 0 {code}\n')
    with open(f'{base}.z', 'w') as f:
        f.write(f' 0.000000\n{len(nodes)}\n')
        for _, _, z, _ in nodes:
            f.write(f'{z}\n')
    with open(f'{base}.tri', 'w') as f:
        f.write(f' 0.000000\n{len(triangles)}\n')
        for a, b, c in triangles:
            f.write(f'{a} {b} {c} -1 -1 -1 0 0 0\n')
    return base
