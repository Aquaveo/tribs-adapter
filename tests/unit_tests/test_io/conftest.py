import os
import pytest

from jinja2 import Template
import pygltflib

from tribs_adapter.io.tribs_mesh import tRIBSMeshViz


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
