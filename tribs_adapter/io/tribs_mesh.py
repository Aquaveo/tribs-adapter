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
    """tRIBS mesh visualization class for writing tRIBS mesh visualization files (glTF).

    Two kinds of geometry can be written:

    * The TIN itself (``.nodes``/``.z``/``.tri``), colored by node elevation. Used when no output files are given.
    * The Voronoi cells (the tRIBS computational elements) colored by the per-cell values in the ``_00d``/``_00i``
      output files. Each cell is a separate fan of triangles with a single, uniform color so values are never
      interpolated between neighboring cells. Cell polygons are read from the tRIBS ``*_voi`` file when one is
      available and otherwise computed from the TIN (Voronoi vertices are the circumcenters of the triangles that
      surround each node, which is exactly how tRIBS derives them).
    """
    # Boundary codes of the nodes that tRIBS treats as active computational elements (interior and stream nodes).
    # Only these nodes have Voronoi cells and rows in the _00d/_00i output files.
    ACTIVE_BOUNDARY_CODES = ('0', '3')

    # Name of the column that holds the node ID in the _00d/_00i output files. tRIBS assigns node IDs from the
    # row order of the input .nodes file, so an ID is also the row index of the node in ``self.nodes``.
    ID_COLUMN = 'ID'

    # Tolerance (in mesh units, i.e. meters) used to match the node centers in a _voi file with the mesh nodes.
    VOI_CENTER_TOLERANCE = 1.0

    def __init__(
        self,
        mesh_basename: Path | str,
        mesh_epsg: int | str,
        output_files: list[Path | str] = None,
        voi_file: Path | str = None,
        voronoi_cells: bool = True,
    ) -> None:
        """Initialize tRIBSMeshViz object.

        Args:
            mesh_basename: Basename path to mesh file (e.g.: /path/to/basename where /path/to is a dirctory
                containing basename.points, basename.tri, basename.z, and basename.edges).
            mesh_epsg: EPSG code of the coordinate system used by the mesh file (e.g. 26912).
            output_files: List of output files (_00d/_00i) to read and visualize.
            voi_file: Path to the tRIBS ``*_voi`` Voronoi polygon file. Defaults to ``<mesh_basename>_voi`` if that
                file exists. When no file is available the Voronoi cells are computed from the TIN.
            voronoi_cells: Render output variables on the Voronoi cells (True, default) instead of on the TIN.
        """
        if output_files is None:
            output_files = []
        self.mesh_basename = Path(mesh_basename) if isinstance(mesh_basename, str) else mesh_basename
        self.mesh_epsg = int(mesh_epsg) if isinstance(mesh_epsg, str) else mesh_epsg
        self.nodes, self.triangles, self.boundary_types = self._read_mesh_arrays(self.mesh_basename)
        # Fix issue with nodes falling outside the raster bounds and having z values approaching negative infinity,
        # when generating gltf later.
        self.nodes = self._reassign_bad_z_values(self.nodes) if (self.nodes[:, 2] < -1e8).any() else self.nodes
        self.output_files = output_files
        self._data = None  # Lazily loaded by the ``data`` property
        self.normals = None
        self.voronoi_cells = voronoi_cells
        self.voi_file = self._resolve_voi_file(voi_file)
        self._voronoi = None  # Lazily loaded by the ``voronoi`` property
        self._voronoi_geometry = None  # Lazily built by ``_build_voronoi_geometry``

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

    # ------------------------------------------------------------------------------------------------------------------
    # Voronoi cells
    # ------------------------------------------------------------------------------------------------------------------
    @property
    def voronoi(self) -> dict:
        """Voronoi cells of the active mesh nodes.

        Returns:
            Dictionary with ``ids`` (int array of node IDs, one per cell) and ``polygons`` (list of (k, 2) float
            arrays with the x-y vertices of each cell in counter-clockwise order, first vertex not repeated).
        """
        if self._voronoi is None:
            if self.voi_file is not None:
                log.info(f"Reading Voronoi cells from: {self.voi_file}")
                ids, centers, polygons = self.read_voi_file(self.voi_file)
                ids, polygons = self._validate_voi_cells(ids, centers, polygons)
            else:
                log.warning(
                    f"No _voi file found for mesh {self.mesh_basename}. Computing Voronoi cells from the TIN instead."
                )
                ids, polygons = self.compute_voronoi_from_tin()
            self._voronoi = {'ids': ids, 'polygons': polygons}
            log.info(f"Loaded {len(ids)} Voronoi cells.")
        return self._voronoi

    def _resolve_voi_file(self, voi_file: Path | str = None) -> Path | None:
        """Determine which _voi file to use, if any."""
        if voi_file is not None:
            voi_path = Path(voi_file)
            if not voi_path.exists():
                raise FileNotFoundError(f"voi file does not exist: {voi_path}")
            return voi_path
        default_voi_path = Path(f"{str(self.mesh_basename)}_voi")
        if default_voi_path.exists():
            return default_voi_path
        return None

    @staticmethod
    def read_voi_file(voi_path: Path | str) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]]:
        """Parse a tRIBS ``*_voi`` Voronoi polygon file.

        The file is written by tRIBS (``tCOutput::WriteNodeData``) once at the start of a run and contains, for every
        active (non-boundary) node::

            <node id>,<node x>,<node y>
            <vertex x>,<vertex y>      (one line per Voronoi vertex, counter-clockwise, first vertex not repeated)
            ...
            END

        The file is terminated with an additional ``END`` line.

        Args:
            voi_path: Path to the _voi file.

        Returns:
            Node IDs (C,), node centers (C, 2), and list of C polygon vertex arrays (k, 2).
        """
        ids, centers, polygons = [], [], []
        current_id = None
        current_center = None
        current_vertices = []

        with open(voi_path, 'r') as voi_file:
            for line_number, line in enumerate(voi_file, start=1):
                line = line.strip()
                if not line:
                    continue
                if line == 'END':
                    if current_id is None:
                        # Two ENDs in a row: end of file
                        break
                    ids.append(current_id)
                    centers.append(current_center)
                    polygons.append(np.array(current_vertices, dtype=np.float64).reshape(-1, 2))
                    current_id, current_center, current_vertices = None, None, []
                    continue

                parts = line.split(',')
                if len(parts) == 3:
                    current_id = int(float(parts[0]))
                    current_center = (float(parts[1]), float(parts[2]))
                elif len(parts) == 2:
                    if current_id is None:
                        raise ValueError(f"{voi_path}:{line_number}: vertex found before a polygon header line.")
                    current_vertices.append((float(parts[0]), float(parts[1])))
                else:
                    raise ValueError(f"{voi_path}:{line_number}: unexpected line: {line!r}")

        if current_id is not None:
            # File ended without a trailing END: keep the last polygon anyway
            ids.append(current_id)
            centers.append(current_center)
            polygons.append(np.array(current_vertices, dtype=np.float64).reshape(-1, 2))

        return np.array(ids, dtype=np.int64), np.array(centers, dtype=np.float64).reshape(-1, 2), polygons

    def _validate_voi_cells(
        self, ids: np.ndarray, centers: np.ndarray, polygons: list[np.ndarray]
    ) -> tuple[np.ndarray, list[np.ndarray]]:
        """Check that the cells of a _voi file belong to this mesh and drop degenerate cells."""
        if len(ids) == 0:
            raise ValueError(f"No Voronoi cells found in {self.voi_file}.")

        if ids.min() < 0 or ids.max() >= len(self.nodes):
            raise ValueError(
                f"Voronoi file {self.voi_file} references node IDs outside of the mesh "
                f"(IDs {ids.min()}-{ids.max()}, mesh has {len(self.nodes)} nodes)."
            )

        # tRIBS node IDs are the row indices of the .nodes file, so the cell centers must coincide with the nodes.
        center_errors = np.hypot(
            centers[:, 0] - self.nodes[ids, 0].astype(np.float64), centers[:, 1] - self.nodes[ids, 1].astype(np.float64)
        )
        mismatched = int((center_errors > self.VOI_CENTER_TOLERANCE).sum())
        if mismatched:
            raise ValueError(
                f"Voronoi file {self.voi_file} does not match mesh {self.mesh_basename}: {mismatched} of {len(ids)} "
                f"cell centers are more than {self.VOI_CENTER_TOLERANCE} m from the node with the same ID."
            )

        valid_ids, valid_polygons = [], []
        for cell_id, polygon in zip(ids, polygons):
            polygon = self._clean_ring(polygon)
            if polygon is None:
                log.warning(f"Skipping degenerate Voronoi cell for node {cell_id} (fewer than 3 distinct vertices).")
                continue
            valid_ids.append(cell_id)
            valid_polygons.append(polygon)

        return np.array(valid_ids, dtype=np.int64), valid_polygons

    def _active_node_indices(self) -> np.ndarray:
        """Indices of the active (interior and stream) nodes, i.e. the nodes that have Voronoi cells."""
        return np.array(
            [i for i, code in enumerate(self.boundary_types) if code in self.ACTIVE_BOUNDARY_CODES], dtype=np.int64
        )

    @staticmethod
    def _circumcenters(triangle_points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Compute the circumcenters of triangles.

        Args:
            triangle_points: (m, 3, 2) array of triangle vertex coordinates.

        Returns:
            (m, 2) array of circumcenters and (m,) boolean mask of the non-degenerate triangles.
        """
        a, b, c = triangle_points[:, 0], triangle_points[:, 1], triangle_points[:, 2]
        d = 2.0 * (a[:, 0] * (b[:, 1] - c[:, 1]) + b[:, 0] * (c[:, 1] - a[:, 1]) + c[:, 0] * (a[:, 1] - b[:, 1]))
        valid = np.abs(d) > 1e-12
        d_safe = np.where(valid, d, 1.0)
        a2 = (a ** 2).sum(axis=1)
        b2 = (b ** 2).sum(axis=1)
        c2 = (c ** 2).sum(axis=1)
        ux = (a2 * (b[:, 1] - c[:, 1]) + b2 * (c[:, 1] - a[:, 1]) + c2 * (a[:, 1] - b[:, 1])) / d_safe
        uy = (a2 * (c[:, 0] - b[:, 0]) + b2 * (a[:, 0] - c[:, 0]) + c2 * (b[:, 0] - a[:, 0])) / d_safe
        centers = np.column_stack((ux, uy))
        centers[~valid] = np.nan
        return centers, valid

    def _node_triangles(self) -> list[list[int]]:
        """List of the indices of the triangles incident to each node."""
        node_triangles = [[] for _ in range(len(self.nodes))]
        for triangle_index, triangle in enumerate(self.triangles):
            for vertex in triangle:
                node_triangles[int(vertex)].append(triangle_index)
        return node_triangles

    @staticmethod
    def _clean_ring(ring: np.ndarray, tolerance: float = 1e-6) -> np.ndarray | None:
        """Remove consecutive duplicate vertices from a ring and make it counter-clockwise.

        Returns:
            Cleaned (k, 2) ring or None if fewer than 3 distinct vertices remain.
        """
        ring = np.asarray(ring, dtype=np.float64).reshape(-1, 2)
        if len(ring) == 0:
            return None
        distinct = np.hypot(*(ring - np.roll(ring, 1, axis=0)).T) > tolerance
        ring = ring[distinct]
        if len(ring) < 3:
            return None
        signed_area = 0.5 * np.sum(ring[:, 0] * np.roll(ring[:, 1], -1) - np.roll(ring[:, 0], -1) * ring[:, 1])
        if signed_area < 0:
            ring = ring[::-1]
        return ring

    def compute_voronoi_from_tin(self) -> tuple[np.ndarray, list[np.ndarray]]:
        """Compute the Voronoi cell of every active node from the TIN.

        The vertices of the Voronoi cell of a node are the circumcenters of the triangles that share that node,
        ordered counter-clockwise around the node. This mirrors how tRIBS builds the cells that it writes to the
        ``*_voi`` file (tRIBS additionally repairs a small number of cells with degenerate triangles).

        Returns:
            Node IDs (C,) and list of C polygon vertex arrays (k, 2).
        """
        xy = self.nodes[:, :2].astype(np.float64)
        centers, valid = self._circumcenters(xy[self.triangles])
        node_triangles = self._node_triangles()

        ids, polygons, skipped = [], [], []
        for node_index in self._active_node_indices():
            incident = [t for t in node_triangles[node_index] if valid[t]]
            vertices = centers[incident]
            angles = np.arctan2(vertices[:, 1] - xy[node_index, 1], vertices[:, 0] - xy[node_index, 0])
            ring = self._clean_ring(vertices[np.argsort(angles)]) if len(incident) >= 3 else None
            if ring is None:
                skipped.append(int(node_index))
                continue
            ids.append(node_index)
            polygons.append(ring)

        if skipped:
            # Typically active nodes sitting on the hull of the TIN or next to zero-area triangles
            listed = f"{skipped[:20]}{'...' if len(skipped) > 20 else ''}"
            log.warning(
                f"Skipped {len(skipped)} of {len(skipped) + len(ids)} active nodes without a well-defined Voronoi "
                f"cell (fewer than 3 distinct circumcenters). Node IDs: {listed}"
            )

        return np.array(ids, dtype=np.int64), polygons

    def _build_voronoi_geometry(self) -> dict:
        """Triangulate the Voronoi cells into a renderable surface.

        Every cell becomes a triangle fan around its node. Vertices are NOT shared between cells so that each cell
        can carry a single, uniform color. Cell vertices are placed on the TIN surface (elevation interpolated inside
        the TIN triangle that contains the vertex), and vertices shared by neighboring cells get exactly the same
        elevation, so the surface stays continuous across cell boundaries. The cell center gets the node elevation.

        Returns:
            Dictionary with ``positions`` (V, 3) float64 array in mesh coordinates, ``triangles`` (F, 3) uint32 array,
            and ``vertex_cell`` (V,) array with the index (into ``self.voronoi['ids']``) of the cell of each vertex.
        """
        if self._voronoi_geometry is not None:
            return self._voronoi_geometry

        separator()
        log.debug("Building Voronoi cell geometry...")
        nodes = self.nodes.astype(np.float64)
        cell_ids = self.voronoi['ids']
        polygons = self.voronoi['polygons']

        # Elevation of every ring vertex from the TIN surface (computed once for all cells so shared vertices match)
        ring_points = np.concatenate(polygons, axis=0)
        ring_nodes = np.repeat(cell_ids, [len(p) for p in polygons])
        ring_elevations = self._tin_surface_elevations(ring_points, ring_nodes)

        positions, faces, vertex_cell = [], [], []
        vertex_offset = 0
        ring_offset = 0
        for cell_index, (node_index, ring) in enumerate(zip(cell_ids, polygons)):
            node = nodes[node_index]
            k = len(ring)
            ring_z = ring_elevations[ring_offset:ring_offset + k]
            ring_offset += k

            positions.append(node[None, :])
            positions.append(np.column_stack((ring, ring_z)))
            center = vertex_offset
            first = vertex_offset + 1
            j = np.arange(k)
            faces.append(np.column_stack((np.full(k, center), first + j, first + (j + 1) % k)))
            vertex_cell.append(np.full(k + 1, cell_index))
            vertex_offset += k + 1

        self._voronoi_geometry = {
            'positions': np.concatenate(positions, axis=0),
            'triangles': np.concatenate(faces, axis=0).astype(np.uint32),
            'vertex_cell': np.concatenate(vertex_cell, axis=0),
        }
        log.debug(
            f"Voronoi geometry: {len(cell_ids)} cells, {len(self._voronoi_geometry['positions'])} vertices, "
            f"{len(self._voronoi_geometry['triangles'])} triangles."
        )
        return self._voronoi_geometry

    def _tin_surface_elevations(self, points: np.ndarray, seed_nodes: np.ndarray) -> np.ndarray:
        """Elevation of x-y points on the TIN surface.

        Each point is located in the TIN triangle that contains it and its elevation is interpolated linearly
        (barycentric weights) from the triangle's nodes. The search is limited to the triangles around the given
        seed node of each point (the node of the Voronoi cell the point belongs to), first its immediate triangles,
        then their neighbors. A point that lies in none of them (outside the TIN, or a repaired Voronoi vertex) is
        projected onto the nearest candidate triangle so its elevation stays within the range of the surrounding
        nodes instead of being extrapolated. Points with identical coordinates get identical elevations.

        Args:
            points: (M, 2) x-y coordinates.
            seed_nodes: (M,) index of a mesh node close to each point.

        Returns:
            (M,) elevations.
        """
        nodes = self.nodes.astype(np.float64)
        triangles = self.triangles.astype(np.int64)
        node_triangles = self._node_triangles()

        # Collapse identical points so neighboring cells share vertex elevations exactly
        unique_points, inverse = np.unique(np.round(points, 4), axis=0, return_inverse=True)
        inverse = inverse.ravel()
        sharing_nodes = [set() for _ in range(len(unique_points))]
        for unique_index, node_index in zip(inverse, seed_nodes):
            sharing_nodes[unique_index].add(int(node_index))

        def one_ring(node_set):
            return {t for n in node_set for t in node_triangles[n]}

        def two_ring(node_set):
            ring = one_ring(node_set)
            return ring | one_ring({int(m) for t in ring for m in triangles[t]})

        def locate(point_indices, candidates_for):
            """Best (least outside) candidate triangle for each point: returns (point index, triangle, weights)."""
            pair_points, pair_triangles = [], []
            for u in point_indices:
                candidates = candidates_for(sharing_nodes[u])
                pair_points.extend([u] * len(candidates))
                pair_triangles.extend(candidates)
            if not pair_points:
                return np.array([], dtype=np.int64), np.array([], dtype=np.int64), np.empty((0, 3))
            pair_points = np.array(pair_points, dtype=np.int64)
            pair_triangles = np.array(pair_triangles, dtype=np.int64)
            p = unique_points[pair_points]
            a, b, c = (nodes[triangles[pair_triangles, i], :2] for i in range(3))
            det = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])
            valid = np.abs(det) > 1e-12
            det = np.where(valid, det, 1.0)
            w1 = ((b[:, 0] - p[:, 0]) * (c[:, 1] - p[:, 1]) - (c[:, 0] - p[:, 0]) * (b[:, 1] - p[:, 1])) / det
            w2 = ((c[:, 0] - p[:, 0]) * (a[:, 1] - p[:, 1]) - (a[:, 0] - p[:, 0]) * (c[:, 1] - p[:, 1])) / det
            weights = np.column_stack((w1, w2, 1.0 - w1 - w2))
            outside = np.where(valid, -weights.min(axis=1), np.inf)  # <= 0 when the point is inside the triangle
            order = np.lexsort((outside, pair_points))
            first = np.r_[True, pair_points[order][1:] != pair_points[order][:-1]]
            best = order[first]
            best = best[np.isfinite(outside[best])]
            return pair_points[best], pair_triangles[best], weights[best]

        elevations = np.full(len(unique_points), np.nan)
        contained = np.zeros(len(unique_points), dtype=bool)

        def assign(point_indices, tri_indices, weights, only_contained):
            inside = weights.min(axis=1) >= -1e-9
            keep = inside if only_contained else np.ones(len(point_indices), dtype=bool)
            w = np.clip(weights[keep], 0.0, 1.0)  # Projection onto the triangle for points outside of it
            w /= w.sum(axis=1, keepdims=True)
            elevations[point_indices[keep]] = (nodes[triangles[tri_indices[keep]], 2] * w).sum(axis=1)
            contained[point_indices[keep][inside[keep]]] = True

        all_points = np.arange(len(unique_points))
        assign(*locate(all_points, one_ring), only_contained=True)
        remaining = all_points[~contained]
        if len(remaining):
            assign(*locate(remaining, two_ring), only_contained=False)
        missing = np.isnan(elevations)
        if missing.any():
            # No usable triangle around the point at all: fall back to the elevation of the cell's node
            for u in np.flatnonzero(missing):
                elevations[u] = nodes[next(iter(sharing_nodes[u])), 2]
        log.debug(
            f"TIN surface elevations: {len(unique_points)} unique points, {int((~contained).sum())} outside of the "
            f"TIN projected onto the nearest triangle."
        )
        return elevations[inverse]

    def _compute_vertex_normals(self, positions: np.ndarray, triangles: np.ndarray) -> np.ndarray:
        """Compute area-weighted vertex normals for an arbitrary triangle mesh in the given coordinate frame."""
        tris = positions[triangles]
        face_normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]).astype(np.float32)
        normals = np.zeros(positions.shape, dtype=np.float32)
        for corner in range(3):
            np.add.at(normals, triangles[:, corner], face_normals)
        return self._normalize_v3(normals)

    def _cell_values(self, output_file: Path | str, output_variable: str) -> list | None:
        """Look up the value of an output variable for every Voronoi cell, joined by node ID.

        Returns:
            List with one value (or None when the cell has no value) per cell in ``self.voronoi['ids']``, or None if
            the variable is not present in the output file.
        """
        file_data = self.data[output_file]
        if output_variable not in file_data:
            log.warning(f"Output variable {output_variable} not found in {output_file}.")
            return None

        values = np.asarray(file_data[output_variable], dtype=np.float64)
        if self.ID_COLUMN in file_data:
            row_ids = np.asarray(file_data[self.ID_COLUMN]).astype(np.int64)
        else:
            log.warning(
                f"Output file {output_file} has no {self.ID_COLUMN} column. Assuming rows are ordered by node ID."
            )
            row_ids = np.arange(len(values), dtype=np.int64)

        # Map node ID -> value (NaN for nodes without a row)
        value_by_node = np.full(len(self.nodes), np.nan, dtype=np.float64)
        in_range = (row_ids >= 0) & (row_ids < len(self.nodes))
        if not in_range.all():
            log.warning(
                f"Ignoring {int((~in_range).sum())} rows of {output_file} with node IDs outside of the mesh."
            )
        value_by_node[row_ids[in_range]] = values[in_range]

        cell_values = value_by_node[self.voronoi['ids']]
        return [None if np.isnan(v) else float(v) for v in cell_values]

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

        # Output variables are rendered on the Voronoi cells; the bare mesh is rendered as the TIN.
        use_voronoi_cells = self.voronoi_cells and len(self.output_files) > 0

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

        if use_voronoi_cells:
            geometry = self._build_voronoi_geometry()
            _, localized_cells = self._localize_crs(to_epsg=to_epsg, points=geometry['positions'])
            localized_cells = self._to_nue(localized_cells, z_offset=z_offset)
            cell_normals = self._compute_vertex_normals(localized_cells, geometry['triangles'])

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
                self._generate_legend_for_values(variable_data, legend_path, color_ramp_file)
        else:
            for output_file in self.output_files:  # Get the file basename and clean out special characters
                basefile_name = os.path.basename(output_file).replace('.', '-')
                file_variables = output_variables if output_variables is not None else self.data[output_file].keys()
                for variable in file_variables:
                    gltf_file_path = Path(f'{gltf_path}_{basefile_name}_{variable}.gltf')
                    if use_voronoi_cells:
                        gltf, variable_data = self._build_voronoi_gltf(
                            localized_cells, cell_normals, output_file, variable, color_ramp_file=color_ramp_file
                        )
                    else:
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
                            self._generate_legend_for_values(variable_data, legend_path, color_ramp_file)

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

    def _localize_crs(self, to_epsg: int = 4326, points: np.ndarray = None) -> tuple[list, np.ndarray]:
        """Localize coordinates to an origin at the center of the mesh.

        Args:
            to_epsg: EPSG code of the target coordinate system. Defaults to WGS84 (EPSG:4326).
            points: (n, 3) array of points (in mesh coordinates) to localize. Defaults to the mesh nodes. The origin
                is always the center of the mesh nodes so that all geometry of a mesh shares the same origin.

        Returns:
            Origin location in WGS84 lon-lat coordinates.
            Localized points array (float32).
        """
        separator()
        log.debug("Normalizing nodes...")
        xstat = np.mean(self.nodes[:, 0])
        ystat = np.mean(self.nodes[:, 1])
        zstat = np.mean(self.nodes[:, 2])
        log.debug(f"Mean X, Y, Z: {xstat}, {ystat}, {zstat}")
        origin_location = [xstat, ystat, zstat]
        points = self.nodes if points is None else points
        l_nodes = (points - origin_location).astype(np.float32)
        log.debug("Pre Localization Summary:")
        self._summarize_array(points)
        log.debug("Post Localization Summary:")
        self._summarize_array(l_nodes)
        assert l_nodes.shape == points.shape, "Localized nodes array has incorrect shape."
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

    def _values_to_texcoords(self, values) -> np.ndarray:
        """Convert raw values (None for no value) to texture coordinates into the color ramp image.

        The color ramps are 256x256 images whose colors vary along the v (row) axis in the u=0 column and are fully
        transparent in the u=1 column, so a value maps to (0, normalized value) and "no value" maps to (1, 1).
        """
        normalized = self._interpolate_array(values)
        return np.array([[0.0, x] if x is not None else [1.0, 1.0] for x in normalized], dtype=np.float32)

    def _build_gltf(
        self,
        nodes: np.ndarray,
        output_file: Path | str = None,
        output_variable: str = None,
        color_ramp_file: Path | str = None,  # Must be 256x256
    ) -> pygltflib.GLTF2:
        """Build glTF mesh of the TIN from the nodes and triangles arrays, colored by a node value.

        Values are attached to the TIN vertices (and hence interpolated across triangles by the renderer). Without an
        output file the active nodes are colored by elevation.
        """
        separator()
        log.debug("Building glTF (TIN)...")

        # Get Variables from data
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
                self.nodes[i][2] if x in self.ACTIVE_BOUNDARY_CODES else None for i, x in enumerate(self.boundary_types)
            ])

        variable_data = self._values_to_texcoords(raw_variable_data)
        gltf = self._assemble_gltf(nodes, self.triangles, self.normals, variable_data, color_ramp_file)
        return gltf, raw_variable_data

    def _build_voronoi_gltf(
        self,
        positions: np.ndarray,
        normals: np.ndarray,
        output_file: Path | str,
        output_variable: str,
        color_ramp_file: Path | str = None,  # Must be 256x256
    ) -> tuple[pygltflib.GLTF2 | None, list | None]:
        """Build glTF mesh of the Voronoi cells, each cell uniformly colored by its value of an output variable.

        Args:
            positions: Localized (NUE) vertex positions from ``_build_voronoi_geometry``.
            normals: Vertex normals matching ``positions``.
            output_file: Output file (_00d/_00i) to take the values from.
            output_variable: Column of the output file to visualize.
            color_ramp_file: Path to the 256x256 color ramp image.

        Returns:
            glTF object and the list of raw cell values (None for cells without a value), or (None, None) if the
            variable is not in the output file.
        """
        separator()
        log.debug("Building glTF (Voronoi cells)...")
        cell_values = self._cell_values(output_file, output_variable)
        if cell_values is None:
            return None, None

        geometry = self._build_voronoi_geometry()
        cell_texcoords = self._values_to_texcoords(cell_values)
        vertex_texcoords = cell_texcoords[geometry['vertex_cell']]
        gltf = self._assemble_gltf(positions, geometry['triangles'], normals, vertex_texcoords, color_ramp_file)
        return gltf, cell_values

    def _assemble_gltf(
        self,
        nodes: np.ndarray,
        triangles: np.ndarray,
        normals: np.ndarray,
        variable_data: np.ndarray,
        color_ramp_file: Path | str = None,  # Must be 256x256
    ) -> pygltflib.GLTF2:
        """Assemble a glTF from vertex positions, triangle indices, vertex normals and vertex texture coordinates.

        Args:
            nodes: (V, 3) float32 vertex positions (localized, NUE axis order).
            triangles: (F, 3) uint32 triangle vertex indices.
            normals: (V, 3) float32 vertex normals.
            variable_data: (V, 2) float32 texture coordinates into the color ramp image.
            color_ramp_file: Path to the 256x256 color ramp image.
        """
        assert nodes.dtype == np.float32, "Vertex positions must be float32."
        assert len(normals) == len(nodes), "Normals and vertex positions have different lengths."
        assert len(variable_data) == len(nodes), "Texture coordinates and vertex positions have different lengths."
        triangles = np.ascontiguousarray(triangles, dtype=np.uint32)
        triangles_binary_blob = triangles.flatten().tobytes()
        nodes_binary_blob = np.ascontiguousarray(nodes).tobytes()
        normals_binary_blob = np.ascontiguousarray(normals, dtype=np.float32).tobytes()
        variable_data_blob = np.ascontiguousarray(variable_data, dtype=np.float32).tobytes()
        textures = []
        samplers = []
        images = []

        # Create accessors
        accessors = [
            pygltflib.Accessor(
                bufferView=0,
                componentType=pygltflib.UNSIGNED_INT,
                count=triangles.size,
                type=pygltflib.SCALAR,
                max=[int(triangles.max())],
                min=[int(triangles.min())],
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
                count=len(normals),
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
        return gltf

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
        arr = np.where(arr == None, np.nan, arr).astype(np.float64)  # NOQA: E711 - arr is None does not work here.
        min_val = np.nanmin(arr)
        max_val = np.nanmax(arr)

        range_val = max_val - min_val
        if range_val == 0:  # Prevent division by zero: constant values all map to the bottom of the ramp
            result = np.zeros_like(arr, dtype=np.float64)
            result[np.isnan(arr)] = np.nan
        else:
            result = (arr - min_val) / range_val
        result = [x if not np.isnan(x) else None for x in result]  # Replace NaN values with None in the final array
        return result

    def _generate_legend_for_values(self, values, legend_path, image_path) -> bool:
        """Generate a legend spanning the range of the given values (ignoring None values).

        Returns:
            True if a legend was written, False if there were no values to build a legend from.
        """
        valid_values = [x for x in values if x is not None]
        if not valid_values:
            log.warning(f"No values to generate a legend from. Skipping legend: {legend_path}")
            return False
        log.debug(f"Generating legend: {legend_path}")
        self._generate_legend(min(valid_values), max(valid_values), legend_path, image_path)
        return True

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
    tribs_mesh = tRIBSMeshViz(
        args.mesh, args.srid, args.output_files, voi_file=args.voi, voronoi_cells=not args.tin
    )
    tribs_mesh.to_gltf(args.gltf, output_variables=args.variables, generate_legend=args.legend)


def parse_args():  # pragma: no cover
    parser = argparse.ArgumentParser(description='Convert a tRIBS mesh to glTF for visualization in Cesium.')
    parser.add_argument('mesh', type=str, help='Basename path to mesh file (e.g.: /path/to/basename).')
    parser.add_argument('gltf', help='Path to glTF file that will be written (e.g.: /path/to/out).')
    parser.add_argument('srid', type=int, help='EPSG code of the coordinate system used by the mesh file (e.g. 26912).')
    parser.add_argument('-d', '--debug', default=False, action='store_true', help='Enable debug logging.')
    parser.add_argument('--voi', default=None, help='Path to the tRIBS _voi file (defaults to <mesh>_voi if present).')
    parser.add_argument(
        '--tin', default=False, action='store_true',
        help='Render output variables on the TIN instead of on the Voronoi cells.'
    )
    parser.add_argument(
        '-v', '--variables', nargs='*', default=None, help='Output variables to visualize (default: all).'
    )
    parser.add_argument('--legend', default=False, action='store_true', help='Also write legend images.')
    parser.add_argument('output_files', nargs='*', help='Output files (_00d/_00i) to read and visualize.')
    return parser.parse_args()


if __name__ == '__main__':  # pragma: no cover
    args = parse_args()
    logging.basicConfig(level=logging.INFO if not args.debug else logging.DEBUG, format='%(levelname)s: %(message)s')
    main(args)
