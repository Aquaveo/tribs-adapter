import os
import pytest

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
    def factory(mesh_basename, mesh_epsg, output_files=None, **kwargs):
        if output_files is not None:
            ofs = [os.path.join(gltf_dir, mesh_basename, of) for of in output_files]
        else:
            ofs = None
        mesh_basename_path = mesh_basename_factory(mesh_basename)
        return tRIBSMeshViz(
            mesh_basename=mesh_basename_path,
            mesh_epsg=mesh_epsg,
            output_files=ofs,
            **kwargs,
        )

    return factory
