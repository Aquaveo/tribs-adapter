import base64
import json
import os
import pytest

from jinja2 import Template
import numpy as np
import pygltflib

from tribs_adapter.io.tribs_mesh import tRIBSMeshViz

# glTF componentType codes -> numpy dtypes
_COMPONENT_DTYPES = {
    5120: np.int8,
    5121: np.uint8,
    5122: np.int16,
    5123: np.uint16,
    5125: np.uint32,
    5126: np.float32,
}

# glTF accessor type -> number of components per element
_TYPE_COUNTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def _decode_buffers(gltf_json):
    """Decode the base64 data-URI buffers of a glTF JSON dict to bytes."""
    return [base64.b64decode(buf['uri'].split(',', 1)[1]) for buf in gltf_json.get('buffers', [])]


def assert_gltf_almost_equal(actual_file, expected_file, atol=1.0):
    """Assert two glTF files are equal, allowing float precision differences.

    The mesh nodes are geocentric coordinates (~6.4e6 m) stored as float32,
    where the representable spacing is up to 0.5 m. Tiny changes in
    numpy/pyproj across environment upgrades shift values by one such step,
    so float accessor data and min/max are compared with a tolerance while
    everything else (structure, indices, embedded images) must match exactly.
    """
    with open(actual_file) as f:
        actual = json.load(f)
    with open(expected_file) as f:
        expected = json.load(f)

    a_bufs = _decode_buffers(actual)
    e_bufs = _decode_buffers(expected)

    a_accessors = actual.get('accessors', [])
    e_accessors = expected.get('accessors', [])
    assert len(a_accessors) == len(e_accessors), 'number of accessors differs'

    float_buffer_views = set()
    for i, (a_acc, e_acc) in enumerate(zip(a_accessors, e_accessors)):
        # min/max (optional per spec) are derived from float data: compare
        # with tolerance when present
        for bound in ('min', 'max'):
            assert (bound in a_acc) == (bound in e_acc), f'accessor {i} {bound} presence differs'
            if bound in a_acc:
                np.testing.assert_allclose(
                    a_acc[bound], e_acc[bound], atol=atol, err_msg=f'accessor {i} {bound}'
                )

        # everything else about the accessor must match exactly
        a_rest = {k: v for k, v in a_acc.items() if k not in ('min', 'max')}
        e_rest = {k: v for k, v in e_acc.items() if k not in ('min', 'max')}
        assert a_rest == e_rest, f'accessor {i} properties differ'

        # compare the underlying binary data
        dtype = _COMPONENT_DTYPES[a_acc['componentType']]
        count = a_acc['count'] * _TYPE_COUNTS[a_acc['type']]
        a_bv = actual['bufferViews'][a_acc['bufferView']]
        e_bv = expected['bufferViews'][e_acc['bufferView']]
        a_data = np.frombuffer(
            a_bufs[a_bv['buffer']], dtype=dtype, count=count,
            offset=a_bv.get('byteOffset', 0) + a_acc.get('byteOffset', 0),
        )
        e_data = np.frombuffer(
            e_bufs[e_bv['buffer']], dtype=dtype, count=count,
            offset=e_bv.get('byteOffset', 0) + e_acc.get('byteOffset', 0),
        )
        if dtype == np.float32:
            np.testing.assert_allclose(a_data, e_data, atol=atol, err_msg=f'accessor {i} data')
            float_buffer_views.add(a_acc['bufferView'])
        else:
            np.testing.assert_array_equal(a_data, e_data, err_msg=f'accessor {i} data')

    # bufferViews not referenced by a float accessor (e.g. embedded images)
    # must match byte-for-byte
    a_bvs = actual.get('bufferViews', [])
    e_bvs = expected.get('bufferViews', [])
    assert len(a_bvs) == len(e_bvs), 'number of bufferViews differs'
    for i, (a_bv, e_bv) in enumerate(zip(a_bvs, e_bvs)):
        if i in float_buffer_views:
            continue
        a_off = a_bv.get('byteOffset', 0)
        e_off = e_bv.get('byteOffset', 0)
        a_bytes = a_bufs[a_bv['buffer']][a_off:a_off + a_bv['byteLength']]
        e_bytes = e_bufs[e_bv['buffer']][e_off:e_off + e_bv['byteLength']]
        assert a_bytes == e_bytes, f'bufferView {i} bytes differ'

    # the rest of the JSON (scenes, meshes, materials, images, etc.) must
    # match exactly; buffers/accessors were compared above
    a_rest = {k: v for k, v in actual.items() if k not in ('buffers', 'accessors')}
    e_rest = {k: v for k, v in expected.items() if k not in ('buffers', 'accessors')}
    assert a_rest == e_rest, 'glTF JSON structure differs'


@pytest.fixture
def assert_gltf_equal():
    return assert_gltf_almost_equal


@pytest.fixture
def input_files_dir(files_dir):
    return files_dir / 'input_files'


@pytest.fixture
def gltf_dir(files_dir):
    return files_dir / 'gltf'


@pytest.fixture
def mesh_basename_factory(gltf_dir):
    def factory(mesh_basename):
        return gltf_dir / mesh_basename / mesh_basename

    return factory


@pytest.fixture
def tmv_factory(mesh_basename_factory, gltf_dir):
    def factory(mesh_basename, mesh_epsg, output_files=None):
        if output_files is not None:
            ofs = [os.path.join(gltf_dir, mesh_basename, of) for of in output_files]
        else:
            ofs = None
        mesh_basename_path = mesh_basename_factory(mesh_basename)
        return tRIBSMeshViz(
            mesh_basename=mesh_basename_path,
            mesh_epsg=mesh_epsg,
            output_files=ofs,
        )

    return factory


@pytest.fixture
def get_expected_gltf(files_dir, tmpdir):
    def factory(mesh_basename):
        # Read the gltf template
        with open(os.path.join(files_dir, 'gltf', mesh_basename, f'{mesh_basename}.gltf')) as f:
            content = f.read()

        # Render the template with the current pygltflib version
        t = Template(content)
        r = t.render({"pygltflib_version": pygltflib.__version__})

        # Write the rendered content to a temporary file for comparison
        expected_file = tmpdir / f'{mesh_basename}_expected.gltf'
        with open(expected_file, 'w') as ef:
            ef.write(r)
        return expected_file

    return factory
