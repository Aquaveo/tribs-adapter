import argparse
import base64
import csv
import logging
import os
from pathlib import Path

import numpy as np
import pygltflib
from pyproj import Transformer, CRS
from PIL import Image

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

log = logging.getLogger(__name__)


class tRIBSMeshViz:
    """tRIBS mesh visualization class for writing tRIBS mesh visualization files (glTF)."""
    def __init__(self, mesh_basename: Path | str, mesh_epsg: int | str, output_files: list[Path | str] = None) -> None:
        """Initialize tRIBSMeshViz object.

        Args:
            mesh_basename: Basename path to mesh file (e.g.: /path/to/basename where /path/to is a dirctory
                containing basename.points, basename.tri, basename.z, and basename.edges).
            mesh_epsg: EPSG code of the coordinate system used by the mesh file (e.g. 26912).
            output_files: List of output files to read and visualize.
        """
        if output_files is None:
            output_files = []
        self.mesh_basename = Path(mesh_basename) if isinstance(mesh_basename, str) else mesh_basename
        self.mesh_epsg = int(mesh_epsg) if isinstance(mesh_epsg, str) else mesh_epsg
        self.nodes, self.triangles, self.boundary_types = self._read_mesh_arrays(self.mesh_basename)
        # Fix issue with nodes falling outside the raster bounds and having z values approaching negative infinity,
        # when generating gltf later.
        self.nodes = self._reassign_bad_z_values(self.nodes) if (self.nodes[:, 2] < -1e8).any() else self.nodes
        # TODO: Read data arrays from output files (e.g.: _00d and _00i files)
        self.output_files = output_files
        self._data = None  # self._parse_output_data()  # TODO: implement
        self.normals = None

    @property
    def data(self) -> dict:
        """Get data arrays."""
        if self._data is None:
            self._data = {}
            log.debug("Data is being loaded.")
            self._parse_output_data()
        return self._data

    def compute_normals(self) -> np.ndarray:
        """Compute normals for the given nodes and triangles arrays.

        Returns:
            Array of normals for each node.
        """
        separator()
        log.debug("Computing normals...")
        # Credits: https://sites.google.com/site/dlampetest/python/calculating-normals-of-a-triangle-mesh-using-numpy
        self.normals = np.zeros(self.nodes.shape, dtype=self.nodes.dtype)
        tris = self.nodes[self.triangles]
        n = np.cross(tris[::, 1] - tris[::, 0], tris[::, 1] - tris[::, 2])  # TODO: order of subtraction?
        self._normalize_v3(n)
        self.normals[self.triangles[:, 0]] += n
        self.normals[self.triangles[:, 1]] += n
        self.normals[self.triangles[:, 2]] += n
        self._normalize_v3(self.normals)
        log.debug("Normals Summary:")
        self._summarize_array(self.normals)

    def to_gltf(
        self,
        gltf_path: Path | str,
        to_epsg: int = 4326,
        z_offset: float = 0.0,
        output_variables=None,
        color_ramp_file=None,
        generate_legend=False,
    ) -> dict:
        """Write mesh to glTF file.

        Args:
            gltf_path: Path to glTF file that will be written (e.g.: /path/to/out).
            to_epsg: EPSG code of the coordinate system used by the glTF file (e.g. 4326).
            z_offset: Offset to add to z values. Defaults to 0.
            output_variables: List of output variables to visualize. Defaults to None.
            color_ramp_file: Path to color ramp file. Defaults to None.
            generate_legend: Generate a legend for the glTF file. Defaults to False.

        Returns:
            Dictionary with metadata about the generated glTF files.
        """
        self.data  # Ensure data is loaded
        generated_gltfs = []

        to_epsg = int(to_epsg) if isinstance(to_epsg, str) else to_epsg

        # computer normals
        if self.normals is None:
            self.compute_normals()

        assert self.normals is not None, "Normals have not been computed."

        model_center, crs_center = self._compute_centers()
        min_x, min_y, _, max_x, max_y, _ = self._compute_model_bounds()
        # expand bounding box by 10%
        percentage = 0.25
        min_x -= (max_x - min_x) * percentage
        min_y -= (max_y - min_y) * percentage
        max_x += (max_x - min_x) * percentage
        max_y += (max_y - min_y) * percentage
        model_extents = [min_x, min_y, max_x, max_y]
        origin_location, localized_nodes = self._localize_crs(to_epsg=to_epsg)
        localized_nodes = self._to_nue(localized_nodes, z_offset=z_offset)

        if color_ramp_file is None:
            file_name = 'TopoAtlasShader'
            color_ramp_file = os.path.join(
                os.path.dirname(__file__), '..', 'templates', 'color_ramps', f'{file_name}.png'
            )

        log.debug("Saving glTF file...")
        if len(self.output_files) == 0:
            gltf, variable_data = self._build_gltf(localized_nodes, color_ramp_file=color_ramp_file)
            gltf = self._set_materials(gltf)
            gltf.save(str(f'{gltf_path}.gltf'))
            generated_gltfs.append(gltf)
            if generate_legend:
                if '.gltf' in str(gltf_path):
                    legend_path = str(gltf_path).replace('.gltf', '_legend.png')
                else:
                    legend_path = f'{gltf_path}_legend.png'
                log.debug(f"Generating legend: {legend_path}")
                self._generate_legend(
                    min([x for x in variable_data if x is not None]), max([x for x in variable_data if x is not None]),
                    legend_path, color_ramp_file
                )
        else:
            for output_file in self.output_files:  # Get the file basename and clean out special characters
                basefile_name = os.path.basename(output_file).replace('.', '-')
                if output_variables is None:
                    output_variables = self.data[output_file].keys()
                for variable in output_variables:
                    gltf_file_path = Path(f'{gltf_path}_{basefile_name}_{variable}.gltf')
                    gltf, variable_data = self._build_gltf(
                        localized_nodes, output_file, variable, color_ramp_file=color_ramp_file
                    )
                    if gltf is not None:
                        gltf = self._set_materials(gltf)
                        separator()
                        log.debug("Saving glTF file...")
                        gltf.save(str(gltf_file_path))
                        generated_gltfs.append(gltf)
                        if generate_legend:
                            legend_path = str(gltf_file_path).replace('.gltf', '_legend.png')
                            log.debug(f"Generating legend: {legend_path}")
                            self._generate_legend(
                                min([x for x in variable_data if x is not None]),
                                max([x for x in variable_data if x is not None]), legend_path, color_ramp_file
                            )

        separator()
        log.info(f"Successfully created glTF: {str(gltf_path)}")
        log.debug(f"Pre-localization Location: {origin_location}")
        log.debug(f"Real-world Model Center Location: {model_center}")
        log.debug(f"Real-world CRS Center Location: {crs_center}")
        meta = dict(
            gltfs=generated_gltfs,
            origin=model_center,
            extents=model_extents,
        )
        return meta

    def _get_array_min_max(self, array: np.ndarray) -> tuple:
        """Get min and max values of an array."""
        min_x, max_x = array[:, 0].min(), array[:, 0].max()
        min_y, max_y = array[:, 1].min(), array[:, 1].max()
        min_z, max_z = array[:, 2].min(), array[:, 2].max()
        return min_x, max_x, min_y, max_y, min_z, max_z

    def _summarize_array(self, array: np.ndarray) -> None:
        """Print summary of given array."""
        log.debug(f"Shape: {array.shape}")
        log.debug(f"Dtype: {array.dtype}")
        min_x, max_x, min_y, max_y, min_z, max_z = self._get_array_min_max(array)
        log.debug(f"X: min={min_x}, max={max_x}")
        log.debug(f"Y: min={min_y}, max={max_y}")
        log.debug(f"Z: min={min_z}, max={max_z}")

    def _read_mesh_arrays(self, mesh_basename: Path) -> tuple:
        """Read mesh files and return nodes and triangles arrays."""
        log.info(f"Reading tRIBS mesh files for: {mesh_basename}...")
        nodes_path = Path(f"{str(mesh_basename)}.nodes")
        z_path = Path(f"{str(mesh_basename)}.z")
        tri_path = Path(f"{str(mesh_basename)}.tri")

        assert nodes_path.exists, f"nodes file does not exist: {nodes_path}"
        assert z_path.exists, f"z file does not exist: {z_path}"
        assert tri_path.exists, f"tri file does not exist: {tri_path}"

        log.info(f"Found the tRIBS mesh files: {nodes_path}, {z_path}, {tri_path}")

        with open(nodes_path, "r") as nodes_file, open(z_path, "r") as z_file:
            # Skip header row
            next(nodes_file)
            next(z_file)

            # Read count row
            nodes_count = int(nodes_file.readline().strip())
            z_count = int(z_file.readline().strip())
            assert nodes_count == z_count, "nodes and z files have different counts."

            # Read nodes
            nodes_list = []
            boundary_types = []
            for node_row, z_row in zip(nodes_file, z_file):
                x, y, _edge_id, _boundary = node_row.split()  # TODO: create edge_id and boundary arrays
                z = z_row.strip()
                boundary_types.append(_boundary)
                nodes_list.append([float(x), float(y), float(z)])

            assert len(nodes_list) == nodes_count, "nodes file has incorrect count."

            # Create nodes array
            nodes = np.array(nodes_list, dtype=np.float32)

        # Read triangles
        with open(tri_path, 'r') as tri_file:
            # Skip header row
            next(tri_file)

            # Read count row
            tri_list = []
            tri_count = int(tri_file.readline().strip())

            # Read triangles
            for tri_row in tri_file:
                v1, v2, v3, _n1, _n2, _n3, _e1, _e2, _e3 = tri_row.split()  # TODO: create n and e arrays
                tri_offset = 0
                tri_list.append([int(v1) - tri_offset, int(v2) - tri_offset, int(v3) - tri_offset])

            assert len(tri_list) == tri_count, "tri file has incorrect count."

            # Create triangles array
            triangles = np.array(tri_list, dtype=np.uint32)

        return nodes, triangles, boundary_types

    def _parse_output_data(self) -> tuple:
        """Read output files and return data arrays."""
        separator()
        for output_basename in self.output_files:
            log.info(f"Reading output files for: {output_basename}...")
            self.data[output_basename] = {}
            with open(output_basename) as output_file:
                log.info(f"Reading output file: {output_basename}...")
                reader = csv.reader(output_file)
                header = next(reader)
                colmap = dict(zip(header, range(len(header))))
            file_data = np.array(np.loadtxt(output_basename, delimiter=",", skiprows=1))
            for header, col in colmap.items():
                self.data[output_basename][header] = file_data[:, col]

    def _normalize_v3(self, vector: np.ndarray) -> np.ndarray:
        """Normalize a numpy array of 3 component vectors shape=(n,3)."""
        lens = np.sqrt(vector[:, 0]**2 + vector[:, 1]**2 + vector[:, 2]**2)
        vector[:, 0] = np.divide(vector[:, 0], lens, out=np.zeros_like(vector[:, 0]), where=lens != 0)
        vector[:, 1] = np.divide(vector[:, 1], lens, out=np.zeros_like(vector[:, 1]), where=lens != 0)
        vector[:, 2] = np.divide(vector[:, 2], lens, out=np.zeros_like(vector[:, 2]), where=lens != 0)
        return vector

    def _reproject_nodes(self, nodes: np.ndarray, from_epsg: int, to_epsg: int = 4978) -> np.ndarray:
        """Reporject nodes from from_epsg to to_epsg.

            Args:
                nodes: Array of 3D node coordinates.
                from_epsg: EPSG code of the source coordinate system.
                to_epsg: EPSG code of the target coordinate system. Defaults to ECEF (EPSG:4978).

            Returns:
                Array of reprojected 3D node coordinates.
        """
        from_crs = CRS.from_epsg(from_epsg).to_3d()
        to_crs = CRS.from_epsg(to_epsg).to_3d()
        separator()
        log.debug(f"Transforming nodes from EPSG:{from_epsg} to EPSG:{to_epsg}...")
        log.debug(f"FROM CRS: {repr(from_crs)}")
        log.debug(f"TO CRS: {repr(to_crs)}")
        transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        fx, fy, fz = transformer.transform(nodes[:, 0], nodes[:, 1], nodes[:, 2])
        t_nodes = np.dstack((fx, fy, fz))[0].astype(np.float32)

        log.debug("Pre Transformation Summary:")
        log.debug(f"CRS: {from_crs.name}")
        self._summarize_array(nodes)
        log.debug("Post Transformation Summary:")
        log.debug(f"CRS: {to_crs.name}")
        self._summarize_array(t_nodes)
        assert t_nodes.shape == nodes.shape, "Transformed nodes array has incorrect shape."
        assert t_nodes.dtype == np.float32, "Transformed nodes array has incorrect dtype."
        return t_nodes, to_epsg

    def _localize_crs(self, to_epsg: int = 4326) -> tuple[list, np.ndarray]:
        """Localize node coordinates to an origin at the center of the mesh.

        Args:
            to_epsg: EPSG code of the target coordinate system. Defaults to WGS84 (EPSG:4326).

        Returns:
            Origin location in WGS84 lon-lat coordinates.
            Localized nodes array.
        """
        separator()
        log.debug("Normalizing nodes...")
        xstat = np.mean(self.nodes[:, 0])
        ystat = np.mean(self.nodes[:, 1])
        zstat = np.mean(self.nodes[:, 2])
        log.debug(f"Mean X, Y, Z: {xstat}, {ystat}, {zstat}")
        origin_location = [xstat, ystat, zstat]
        l_nodes = self.nodes - origin_location
        log.debug("Pre Localization Summary:")
        self._summarize_array(self.nodes)
        log.debug("Post Localization Summary:")
        self._summarize_array(l_nodes)
        assert l_nodes.shape == self.nodes.shape, "Localized nodes array has incorrect shape."
        from_crs = CRS.from_epsg(self.mesh_epsg).to_3d()
        to_crs = CRS.from_epsg(to_epsg).to_3d()
        transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        origin_location = list(transformer.transform(origin_location[0], origin_location[1], origin_location[2]))
        return origin_location, l_nodes

    def _to_nue(self, nodes: np.ndarray, z_offset: float = 0) -> np.ndarray:
        """Rearrange axes to be compatible with Cesium North Up East tangent plane transformation.

        Args:
            nodes: Array of 3D node coordinates.
            z_offset: Offset to add to z values. Defaults to 0.
        """
        separator()
        log.debug("Converting to NUE coordinates...")
        self._summarize_array(nodes)
        x = nodes[:, 0]
        y = nodes[:, 1]
        z = nodes[:, 2] + z_offset
        nue_nodes = np.dstack((z, x, y))[0]
        self._summarize_array(nue_nodes)
        assert nue_nodes.shape == nodes.shape, "NUE nodes array has incorrect shape."
        assert nue_nodes.dtype == np.float32, "NUE nodes array has incorrect dtype."
        return nue_nodes

    def _compute_model_bounds(self, to_epsg: int = 4326) -> tuple:
        """Compute the bounding box of the model in WGS84 coordinates.

        Args:
            to_epsg: EPSG code of the target coordinate system. Defaults to WGS84 (EPSG:4326).

        Returns:
            Bounding box of the model in WGS84 coordinates.
        """
        separator()
        log.debug("Computing model bounds...")
        min_x, max_x, min_y, max_y, min_z, max_z = self._get_array_min_max(self.nodes)
        from_crs = CRS.from_epsg(self.mesh_epsg).to_3d()
        to_crs = CRS.from_epsg(to_epsg).to_3d()
        transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        min_x, min_y, min_z = transformer.transform(min_x, min_y, min_z)
        max_x, max_y, max_z = transformer.transform(max_x, max_y, max_z)
        log.debug(f"Model Bounds (UTM): [{min_x}, {min_y}, {min_z}] - [{max_x}, {max_y}, {max_z}]")

        arr = [min_x, min_y, min_z, max_x, max_y, max_z]
        if float('inf') in arr or float('-inf') in arr:
            raise ValueError(
                f"Projection Error: Could not transform coordinates from EPSG:{self.mesh_epsg} (given) to "
                f"EPSG:{to_epsg}. Try using a projection that is compatible with EPSG:{to_epsg}."
            )

        return min_x, min_y, min_z, max_x, max_y, max_z

    def _compute_centers(self, to_epsg: int = 4326) -> tuple:
        """Compute center of nodes array and center of SRID in WGS84 coordinates.

        Args:
            to_epsg: EPSG code of the target coordinate system. Defaults to WGS84 (EPSG:4326).

        Returns:
            Center of mesh nodes array in to_srid coordinates.
            Center of SRID in to_srid coordinates.
        """
        separator()
        log.debug("Computing centers...")
        from_crs = CRS.from_epsg(self.mesh_epsg).to_3d()
        to_crs = CRS.from_epsg(to_epsg).to_3d()
        transformer = Transformer.from_crs(from_crs, to_crs, always_xy=True)
        # Compute Center of Nodes
        ncx = np.mean(self.nodes[:, 0])
        ncy = np.mean(self.nodes[:, 1])
        ncz = np.mean(self.nodes[:, 2])
        log.debug(f"Center of Nodes (UTM): [{ncx}, {ncy}, {ncz}]")
        ncx, ncy, ncz = transformer.transform(ncx, ncy, ncz)
        log.debug(f"Center of Nodes (WGS84): [{ncx}, {ncy}, {ncz}]")

        if float('inf') in [ncx, ncy, ncz] or float('-inf') in [ncx, ncy, ncz]:
            raise ValueError(
                f"Projection Error: Could not transform coordinates from EPSG:{self.mesh_epsg} (given) to "
                f"EPSG:{to_epsg}. Try using a projection that is compatible with EPSG:{to_epsg}."
            )

        # Compute Origin of Given Coordinate System
        scx, scy, scz = transformer.transform(0, 0, 0)
        log.debug(f"Origin of CRS (WGS84): [{scx}, {scy}, {scz}]")

        if float('inf') in [scx, scy, scz] or float('-inf') in [scx, scy, scz]:
            raise ValueError(
                f"Projection Error: Could not transform coordinates from EPSG:{self.mesh_epsg} (given) to "
                f"EPSG:{to_epsg}. Try using a projection that is compatible with EPSG:{to_epsg}."
            )

        return [ncx, ncy, ncz], [scx, scy, scz]

    def _build_gltf(
        self,
        nodes: np.ndarray,
        output_file: Path | str = None,
        output_variable: str = None,
        color_ramp_file: Path | str = None,  # Must be 256x256
    ) -> pygltflib.GLTF2:
        """Build glTF mesh from nodes and triangles arrays."""
        separator()
        log.debug("Building glTF...")
        triangles_binary_blob = self.triangles.flatten().tobytes()
        nodes_binary_blob = nodes.tobytes()
        normals_binary_blob = self.normals.tobytes()
        textures = []
        samplers = []
        images = []

        # Get Variables from data
        mesh_atts = None
        raw_variable_data = []
        if output_file is not None:
            file_data = self.data[output_file]
            if output_variable not in file_data:
                log.warning(f"Output variable {output_variable} not found in {output_file}.")
                return None, None
            raw_variable_data = np.array(
                file_data[output_variable].tolist() +
                [None for _ in range(len(nodes) - len(file_data[output_variable]))]
            )[:len(nodes)]
        else:
            raw_variable_data = np.array([
                self.nodes[i][2] if x == '0' or x == '3' else None for i, x in enumerate(self.boundary_types)
            ])

        variable_data = self._interpolate_array(raw_variable_data)
        variable_data = np.array([[0.0, x] if x is not None else [1.0, 1.0] for x in variable_data], dtype=np.float32)
        variable_data_blob = variable_data.tobytes()

        # Create accessors
        accessors = [
            pygltflib.Accessor(
                bufferView=0,
                componentType=pygltflib.UNSIGNED_INT,
                count=self.triangles.size,
                # type=pygltflib.VEC3,
                type=pygltflib.SCALAR,
                max=[int(self.triangles.max())],
                min=[int(self.triangles.min())],
            ),
            pygltflib.Accessor(
                bufferView=1,
                componentType=pygltflib.FLOAT,
                count=len(nodes),
                type=pygltflib.VEC3,
                max=nodes.max(axis=0).tolist(),
                min=nodes.min(axis=0).tolist(),
            ),
            pygltflib.Accessor(
                bufferView=2,
                componentType=pygltflib.FLOAT,
                count=len(self.normals),
                type=pygltflib.VEC3,
            ),
            pygltflib.Accessor(
                bufferView=3,
                componentType=pygltflib.FLOAT,
                count=len(variable_data),
                type=pygltflib.VEC2,
            ),
        ]

        # Create buffer views
        buffer_views = [
                pygltflib.BufferView(  # Flattened triangles array
                    buffer=0,
                    byteLength=len(triangles_binary_blob),
                    target=pygltflib.ELEMENT_ARRAY_BUFFER,
                ),
                pygltflib.BufferView(  # Node Locations
                    buffer=0,
                    byteOffset=len(triangles_binary_blob),
                    byteLength=len(nodes_binary_blob),
                    target=pygltflib.ARRAY_BUFFER,
                ),
                pygltflib.BufferView(  # Normals
                    buffer=0,
                    byteOffset=len(triangles_binary_blob) + len(nodes_binary_blob),
                    byteLength=len(normals_binary_blob),
                    target=pygltflib.ARRAY_BUFFER,
                ),
                pygltflib.BufferView(  # Texcoord Values
                    buffer=0,
                    byteOffset=len(triangles_binary_blob) + len(nodes_binary_blob) + len(normals_binary_blob),
                    byteLength=len(variable_data_blob),
                    target=pygltflib.ARRAY_BUFFER,
                )
            ]

        buffer_byte_length = len(triangles_binary_blob) + len(nodes_binary_blob) \
            + len(normals_binary_blob) + len(variable_data_blob)
        buffer_binary_blob = triangles_binary_blob + nodes_binary_blob + normals_binary_blob + variable_data_blob

        samplers.append(pygltflib.Sampler(
            wrapS=pygltflib.CLAMP_TO_EDGE,
            wrapT=pygltflib.CLAMP_TO_EDGE,
        ))

        # Get Image
        if color_ramp_file is None:
            file_name = 'TopoAtlasShader'
            color_ramp_file = os.path.join(
                os.path.dirname(__file__), '..', 'templates', 'color_ramps', f'{file_name}.png'
            )
        with open(color_ramp_file, 'rb') as f:
            image_data = f.read()
            images.append(
                pygltflib.Image(uri=f'data:image/png;base64,{base64.b64encode(image_data).decode("utf-8")}', )
            )
        textures.append(pygltflib.Texture(
            sampler=0,
            source=0,
        ))

        # Create Mesh
        mesh_atts = pygltflib.Attributes(POSITION=1, NORMAL=2, TEXCOORD_0=3)
        meshes = [
            pygltflib.Mesh(
                primitives=[
                    pygltflib.Primitive(
                        attributes=mesh_atts,
                        indices=0,
                        material=0,
                        mode=pygltflib.TRIANGLES,
                    )
                ]
            )
        ]

        # Create buffers
        buffers = [pygltflib.Buffer(byteLength=buffer_byte_length)]

        gltf = pygltflib.GLTF2(
            scene=0,
            scenes=[pygltflib.Scene(nodes=[0])],
            nodes=[pygltflib.Node(mesh=0)],
            meshes=meshes,
            accessors=accessors,
            bufferViews=buffer_views,
            buffers=buffers,
            samplers=samplers,
            images=images,
            textures=textures,
        )
        gltf.set_binary_blob(buffer_binary_blob)
        gltf.convert_buffers(pygltflib.BufferFormat.DATAURI)
        return gltf, raw_variable_data

    def _set_materials(self, gltf: pygltflib.GLTF2) -> None:
        """Set materials for the glTF mesh."""
        separator()
        log.debug("Setting materials...")
        log.debug(f"Materials before: {gltf.materials}")
        gltf.materials = [
            pygltflib.Material(
                name="tRIBS Base Material",
                doubleSided=True,
                alphaMode="MASK",
                pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                    baseColorFactor=[1.0, 1.0, 1.0, 1.0],
                    baseColorTexture=pygltflib.TextureInfo(index=0, texCoord=0),
                    metallicFactor=0.0,
                    roughnessFactor=1.0,
                ),
                emissiveFactor=[0.0, 0.0, 0.0],
            ),
        ]
        log.debug(f"Materials after: {gltf.materials}")
        return gltf

    def _interpolate_array(self, arr):
        """Interpolate array values."""
        arr = np.array(arr)
        arr = np.where(arr == None, np.nan, arr)  # NOQA: E711 - arr is None does not work here.
        min_val = np.nanmin(arr)
        max_val = np.nanmax(arr)

        range_val = max_val - min_val
        if range_val == 0:  # Prevent division by zero
            return np.zeros_like(arr)
        result = (arr - min_val) / range_val
        result = [x if not np.isnan(x) else None for x in result]  # Replace NaN values with None in the final array
        return result

    def _generate_legend(self, min_val, max_val, legend_path, image_path):
        # Open the image
        image = Image.open(image_path).rotate(90)
        gradient = np.array(image)

        if max_val - min_val == 0:
            max_val += 1

        # Create a figure and axis to plot the gradient
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.imshow(gradient, aspect='auto')

        # Set the ticks and labels
        ticks = np.linspace(0, 1, 5)
        tick_labels = np.linspace(min_val, max_val, 5)
        ax.set_xticks(ticks * (gradient.shape[1] - 1))
        ax.set_xticklabels([f'{label:.2f}' for label in tick_labels])
        ax.set_yticks([])

        # Save the figure as a PNG file
        plt.savefig(legend_path, bbox_inches='tight')
        plt.close()

    def _reassign_bad_z_values(self, nodes: np.array) -> np.array:
        """
        Reassigns Z values that are approaching NODATA values to the closest
        node in the array that does not have a Z value approaching NODATA.

        Bad Z values are defined as those less than -1e8, which is a common
        value used to indicate no data in tRIBS meshes.

        Args:
            nodes (np.array): NumPy array of nodes where the third column is
                the elevation.

        Returns:
            np.array: The modified NumPy array of nodes with updated elevations.
        """
        if nodes.shape[1] < 3:
            log.warning("Input array must have 3 columns (x, y, z). Returning original nodes.")
            return nodes

        updated_nodes_array = nodes.copy()  # Work on a copy to preserve original nodes

        bad_z_indices = np.where(updated_nodes_array[:, 2] < -1e8)[0]
        good_z_indices = np.where(updated_nodes_array[:, 2] >= -1e8)[0]

        if len(good_z_indices) == 0:
            log.warning("Warning: No points with valid Z values found. Returning original nodes.")
            return nodes

        for bad_index in bad_z_indices:
            target_point = updated_nodes_array[bad_index, :2]  # Get x, y of the bad point

            # Calculate squared Euclidean distances to all good points
            distances_sq = np.sum((updated_nodes_array[good_z_indices, :2] - target_point)**2, axis=1)

            # Find the index of the closest positive Z point nwithin the good indices
            closest_good_index_in_subset = np.argmin(distances_sq)

            # Get the actual index in the original array
            closest_good_index = good_z_indices[closest_good_index_in_subset]

            # Assign the Z value
            updated_nodes_array[bad_index, 2] = updated_nodes_array[closest_good_index, 2]

        return updated_nodes_array


def separator() -> None:
    """Log separator."""
    log.debug("=" * 100)


def main(args):  # pragma: no cover
    tribs_mesh = tRIBSMeshViz(args.mesh, args.srid, args.output_files)
    tribs_mesh.to_gltf(args.gltf, output_variables=['Z', 'S', 'Rain'])  # Example of using with variables
    # tribs_mesh.to_gltf(args.gltf)


def parse_args():  # pragma: no cover
    parser = argparse.ArgumentParser(description='Convert a tRIBS mesh to glTF for visualization in Cesium.')
    parser.add_argument('mesh', type=str, help='Basename path to mesh file (e.g.: /path/to/basename).')
    parser.add_argument('gltf', help='Path to glTF file that will be written (e.g.: /path/to/out).')
    parser.add_argument('srid', type=int, help='EPSG code of the coordinate system used by the mesh file (e.g. 26912).')
    parser.add_argument('-d', '--debug', default=False, action='store_true', help='Enable debug logging.')
    parser.add_argument('output_files', nargs='*', help='Output files to read and visualize.')
    return parser.parse_args()


if __name__ == '__main__':  # pragma: no cover
    args = parse_args()
    logging.basicConfig(level=logging.INFO if not args.debug else logging.DEBUG, format='%(levelname)s: %(message)s')
    main(args)
