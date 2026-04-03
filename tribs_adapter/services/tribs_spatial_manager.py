"""
********************************************************************************
* Name: tribs_spatial_manager
* Author: glarsen
* Created On: December, 2023
* Copyright: (c) Aquaveo 2023
********************************************************************************
"""
import datetime
import glob
import json
import logging
import mimetypes
import numpy as np
import os
import rasterio
from rasterio import shutil as rio_shutil
import pandas as pd
from pyproj import Transformer
import re
import requests
import tempfile
import zipfile
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from tethysext.atcore.services.base_spatial_manager import reload_config
from tethysext.atcore.services.color_ramps import COLOR_RAMPS
from tethysext.atcore.services.resource_spatial_manager import ResourceSpatialManager

from tribs_adapter.common.dataset_types import DatasetTypes, CompoundDatasetTypes, \
    GltfOutputDatasetTypes, SdfDatasetTypes, WMSDatasetTypes, NoEnvStrDatasetTypes
from tribs_adapter.common.czml_converters import generate_czml_for_pixel_files, generate_czml_for_mrf_and_rft_files, \
    generate_czml_for_qout_files, get_file_variables, get_output_file_variables, get_extents, get_nodes, \
    generate_czml_for_sdf_station, reproject
from tribs_adapter.io.tribs_mesh import tRIBSMeshViz

log = logging.getLogger(__name__)


class TribsSpatialManager(ResourceSpatialManager):
    """
    Managers GeoServer Layers for tRIBS Projects.
    """
    WORKSPACE = 'tribs'
    URI = 'http://portal.aquaveo.com/tribs'
    SLD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'sld_templates')
    S_RASTER = 'raster'  # built-in style in geoserver
    S_RASTER_CONT = 'raster_continuous'
    S_RASTER_DISC = 'raster_discrete'
    S_FEATURES_SHP = 'features_shapefile'
    S_FEATURES_SHP_LABELS = 'features_shapefile_labels'
    S_NDVI = 'ndvi'
    S_RASTER_RGB = 'raster_rgb'
    S_VT = 'vegetation_types'
    S_PP = 'parallel_partition'
    DATASET_TYPE_TO_STYLE = {
        DatasetTypes.RASTER_CONT_ASCII: S_RASTER_CONT,
        DatasetTypes.RASTER_CONT_GEOTIFF: S_RASTER_CONT,
        DatasetTypes.RASTER_CONT_ASCII_TIMESERIES: S_RASTER_CONT,
        DatasetTypes.RASTER_CONT_GEOTIFF_TIMESERIES: S_RASTER_CONT,
        DatasetTypes.RASTER_DISC_ASCII: S_RASTER_DISC,
        DatasetTypes.RASTER_DISC_GEOTIFF: S_RASTER_DISC,
        DatasetTypes.RASTER_DISC_ASCII_TIMESERIES: S_RASTER_DISC,
        DatasetTypes.RASTER_DISC_GEOTIFF_TIMESERIES: S_RASTER_DISC,
        DatasetTypes.RASTER_RGB_GEOTIFF: S_RASTER_RGB,
        DatasetTypes.TRIBS_METIS: S_PP
    }
    GDF_FILE_TO_STYLE = {
        'AL': S_RASTER_CONT,
        'TF': S_RASTER_CONT,
        'VH': S_RASTER_CONT,
        'SR': S_RASTER_DISC,
        'VF': S_RASTER_CONT,
        'CC': S_RASTER_CONT,
        'DC': S_RASTER_CONT,
        'DE': S_RASTER_CONT,
        'OT': S_RASTER_CONT,
        'LA': S_RASTER_CONT,
        'CS': S_RASTER_CONT,
        'IC': S_RASTER_CONT,
        'KS': S_RASTER_CONT,
        'TR': S_RASTER_CONT,
        'TS': S_RASTER_CONT,
        'PB': S_RASTER_CONT,
        'PI': S_RASTER_CONT,
        'FD': S_RASTER_CONT,
        'PO': S_RASTER_CONT,
        'As': S_RASTER_CONT,
        'Au': S_RASTER_CONT,
        'n': S_RASTER_CONT,
        'ks': S_RASTER_CONT,
        'Cs': S_RASTER_CONT
    }

    # Override parent class GEOSERVER_CLUSTER_PORTS attribute with local environment var
    try:
        GEOSERVER_CLUSTER_PORTS = json.loads(os.environ.get("GEOSERVER_CLUSTER_PORTS"))
    except (json.JSONDecodeError, TypeError):
        GEOSERVER_CLUSTER_PORTS = [8081, 8082, 8083, 8084]
    log.debug(f"GEOSERVER_CLUSTER_PORTS set to {GEOSERVER_CLUSTER_PORTS}")

    def __init__(self, geoserver_engine, reload_ports=GEOSERVER_CLUSTER_PORTS):
        """
        Constructor

        Args:
            workspace(str): The workspace to use when creating layers and styles.
            geoserver_engine(tethys_dataset_services.GeoServerEngine): Tethys geoserver engine.
        """
        super().__init__(geoserver_engine)
        if reload_ports is not None:
            # Overriding the GEOSERVER_CLUSTER_PORTS attribute above
            # is not sufficient, so we set it on the instance too
            self.GEOSERVER_CLUSTER_PORTS = reload_ports

    def get_extent_for_project(self, project=None, buffer=None):

        default_extent = [-124.67, 25.84, -66.95, 49.38]  # Default for continental USA
        if project is None:
            return default_extent

        project_extent = project.get_attribute('project_extent')
        if project_extent is None:
            corners = [(default_extent[0], default_extent[1]), (default_extent[2], default_extent[3])]
        elif isinstance(project_extent, dict):
            corners = [(default_extent[0], default_extent[1]), (default_extent[2], default_extent[3])]
        else:
            corners = [(project_extent[0], project_extent[1]), (project_extent[2], project_extent[3])]
        # get min_x, min_y, max_x, max_y from corners
        min_x = min([corner[0] for corner in corners])
        min_y = min([corner[1] for corner in corners])
        max_x = max([corner[0] for corner in corners])
        max_y = max([corner[1] for corner in corners])

        if buffer is not None:
            x_dist = max_x - min_x
            y_dist = max_y - min_y
            x_buff = x_dist * buffer
            y_buff = y_dist * buffer

            min_x = min_x - x_buff
            min_y = min_y - y_buff
            max_x = max_x + x_buff
            max_y = max_y + y_buff

        return [min_x, min_y, max_x, max_y]

    def get_extent_for_dataset(self, dataset, buffer_factor=1.00001):
        # Process identifier
        workspace, datastore_name = 'tribs', self.get_unique_item_name(dataset)
        if dataset.dataset_type in [
            DatasetTypes.FEATURES_SHAPEFILE, DatasetTypes.TRIBS_OUT_PIXEL, DatasetTypes.TRIBS_METIS
        ]:
            response_location = 'featureType'
            url = (
                self.gs_engine.endpoint + 'workspaces/' + workspace + '/datastores/' + datastore_name +
                '/featuretypes/' + datastore_name + '.json'
            )
        else:
            response_location = 'coverage'
            url = (self.gs_engine.endpoint + 'workspaces/' + workspace + '/coverages/' + datastore_name + '.json')

        response = requests.get(url, auth=(self.gs_engine.username, self.gs_engine.password))

        if response.status_code != 200:
            msg = "Get Layer Extent Status Code {0}: {1}".format(response.status_code, response.text)
            exception = requests.RequestException(msg, response=response)
            log.error(exception)
            raise exception

        # Get the JSON
        json = response.json()

        # Default bounding box
        bbox = None
        extent = [-128.583984375, 22.1874049914, -64.423828125, 52.1065051908]

        # Extract bounding box
        if 'latLonBoundingBox' in json[response_location]:
            bbox = json[response_location]['latLonBoundingBox']

        if bbox is not None:
            # minx, miny, maxx, maxy
            extent = [
                bbox['minx'] / buffer_factor, bbox['miny'] / buffer_factor, bbox['maxx'] * buffer_factor,
                bbox['maxy'] * buffer_factor
            ]

        # order extent to be min_x min_y max_x max_y
        x1, y1, x2, y2 = extent
        extent = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
        return extent

    @reload_config()
    def create_all_layers(self, project, srid, session, reload_config=True):
        """
        High level method to create all GeoServer layers for a project.

        Args:
            project(gssha_adapter.resources.project.Project): Project instance.
            srid(int): EPSG Spatial Reference ID.
            reload_config(bool): Whether to reload the config after creating the layers.
        """
        # Loop through datasets in project
        for dataset in project.datasets:
            self.create_layer_for_dataset(dataset, srid, session, reload_config)

    @reload_config()
    def create_layer_for_dataset(self, dataset, srid, session, reload_config=True):
        """
        High level method to create all GeoServer layers for a dataset.

        Args:
            dataset(tribs_adapter.resources.dataset.Dataset): Dataset instance.
            srid(int): EPSG Spatial Reference ID.
            reload_config(bool): Whether to reload the config after creating the layers.
        """
        # Get file collection information and file
        viz = None
        fc = dataset.file_collection_client
        files = os.listdir(fc.path)

        s = f"{self.WORKSPACE}:{self.get_unique_item_name(dataset=None, variable=dataset.dataset_type.lower())}"

        if dataset.dataset_type in self.DATASET_TYPE_TO_STYLE:
            style_name = self.DATASET_TYPE_TO_STYLE[dataset.dataset_type]
            s = self.get_unique_item_name(dataset=None, variable=style_name, with_workspace=True)

        if dataset.dataset_type == DatasetTypes.FEATURES_SHAPEFILE:
            fs = [os.path.join(fc.path, f) for f in files if not f.endswith('.json')]
            self.create_feature_shapefile_layer(dataset, srid, fs, reload_config=False)

        elif dataset.dataset_type == DatasetTypes.RASTER_CONT_ASCII \
                or dataset.dataset_type == DatasetTypes.RASTER_DISC_ASCII:
            for _f in files:
                if _f.endswith('.json'):
                    continue
                f = os.path.join(fc.path, _f)
            self.create_raster_ascii_layer(dataset, srid, f, s, reload_config=False)
        elif dataset.dataset_type in [
            DatasetTypes.RASTER_CONT_GEOTIFF, DatasetTypes.RASTER_DISC_GEOTIFF, DatasetTypes.RASTER_RGB_GEOTIFF
        ]:
            f = None
            for _f in files:
                if _f.endswith('.json'):
                    continue
                if _f.endswith('.tif') or _f.endswith('.tiff'):
                    f = os.path.join(fc.path, _f)

            if f is None:
                raise ValueError('Could not find a geotiff (*.tif or *.tiff) file in the dataset file collection.')

            self.create_raster_geotiff_layer(dataset, srid, f, s, reload_config=False)

        elif dataset.dataset_type == DatasetTypes.RASTER_CONT_ASCII_TIMESERIES \
                or dataset.dataset_type == DatasetTypes.RASTER_DISC_ASCII_TIMESERIES:
            fs = [os.path.join(fc.path, f) for f in files if not f.endswith('.json')]
            self.create_raster_timeseries_ascii_layer(dataset, srid, fs, s, reload_config=False)

        elif dataset.dataset_type == DatasetTypes.RASTER_CONT_GEOTIFF_TIMESERIES \
                or dataset.dataset_type == DatasetTypes.RASTER_DISC_GEOTIFF_TIMESERIES:
            fs = [os.path.join(fc.path, f) for f in files if not f.endswith('.json')]
            self.create_raster_timeseries_geotiff_layer(dataset, srid, fs, s, reload_config=False)

        elif dataset.dataset_type == DatasetTypes.TRIBS_TIN:
            gltf_meta = self.create_tribs_tin_layer(dataset, mesh_epsg=srid)
            gltf_files = os.listdir(os.path.join(dataset.file_collection_client.path, 'gltf'))
            viz_urls = [
                os.path.join(str(dataset.file_collection.file_database_id), str(dataset.file_collection.id), 'gltf', f)
                for f in gltf_files if f.endswith('.gltf')
            ]
            legend_urls = [
                os.path.join(str(dataset.file_collection.file_database_id), str(dataset.file_collection.id), 'gltf', f)
                for f in gltf_files if f.endswith('.png')
            ]
            # Override viz with gltf viz
            viz = {
                'type': 'gltf',
                'url': viz_urls,
                'origin': gltf_meta.get('origin'),
                'extent': gltf_meta.get('extents'),
                'legend': legend_urls,
            }

        elif dataset.dataset_type == DatasetTypes.TRIBS_METIS:
            fs = [
                os.path.join(fc.path, f)
                for f in files if os.path.splitext(f)[-1] in ['.cpg', '.prj', '.shp', '.shx', '.dbf']
            ]
            self.create_feature_shapefile_layer(dataset, srid, fs, style=s, reload_config=False)

        elif dataset.dataset_type in GltfOutputDatasetTypes:
            # find the tribs_tin dataset that is linked to this dataset
            from tribs_adapter.resources import Dataset
            linked_realization = dataset.linked_realizations[0]
            output_node_file = linked_realization.input_file.files_and_pathnames.mesh_generation.INPUTDATAFILE
            node_file_dataset = session.query(Dataset).get(str(output_node_file.resource_id))
            gltf_meta = self.create_tribs_tin_layer(node_file_dataset, mesh_epsg=srid, output_dataset=dataset)
            gltf_files = os.listdir(os.path.join(dataset.file_collection_client.path, 'gltf'))
            viz_urls = [
                os.path.join(str(dataset.file_collection.file_database_id), str(dataset.file_collection.id), 'gltf', f)
                for f in gltf_files if f.endswith('.gltf')
            ]
            legend_urls = [
                os.path.join(str(dataset.file_collection.file_database_id), str(dataset.file_collection.id), 'gltf', f)
                for f in gltf_files if f.endswith('.png')
            ]
            # Override viz with gltf viz
            viz = {
                'type': 'gltf',
                'url': viz_urls,
                'origin': gltf_meta.get('origin'),
                'extent': gltf_meta.get('extents'),
                'legend': legend_urls,
            }

        elif dataset.dataset_type in [
            DatasetTypes.TRIBS_OUT_PIXEL,
            DatasetTypes.TRIBS_OUT_MRF,
            DatasetTypes.TRIBS_OUT_RFT,
            DatasetTypes.TRIBS_SDF_HYDROMET_STATION,
            DatasetTypes.TRIBS_SDF_RAIN_GAUGE,
            DatasetTypes.TRIBS_OUT_QOUT,
        ]:
            meta = self.create_tribs_czml_layer(dataset, session, files, srid)
            geom_files = os.listdir(os.path.join(dataset.file_collection_client.path, 'czml'))
            viz_urls = [
                os.path.join(str(dataset.file_collection.file_database_id), str(dataset.file_collection.id), 'czml', f)
                for f in geom_files if f.endswith('.czml')
            ]
            legend_urls = [
                os.path.join(str(dataset.file_collection.file_database_id), str(dataset.file_collection.id), 'czml', f)
                for f in geom_files if f.endswith('.png')
            ]
            viz = {
                'type': 'czml',
                'url': viz_urls,
                'origin': meta.get('origin'),
                'extent': meta.get('extents'),
                'legend': legend_urls,
            }

        elif dataset.dataset_type in CompoundDatasetTypes:
            layers, extent, env_strs = self.create_all_compound_layers(dataset, srid)
            viz = {
                'type': 'compound_wms',
                'layer': layers,
                'url': self.gs_engine.get_wms_endpoint(public=True),
                'extent': extent,
                'legend': [self.get_wms_layer_legend_url(layer) for layer in layers],
                'env_str': env_strs
            }

        # Set viz for WMS layers
        if dataset.dataset_type in WMSDatasetTypes:
            layer = f"{self.WORKSPACE}:{self.get_unique_item_name(dataset=dataset)}"
            viz = {
                'type': 'wms',
                'url': self.gs_engine.get_wms_endpoint(public=True),
                'layer': layer,
                'extent': self.get_extent_for_dataset(dataset),
                'legend': [self.get_wms_layer_legend_url(layer)],
            }
            if dataset.dataset_type not in NoEnvStrDatasetTypes:
                _, [min_val, max_val,
                    nodata_val] = TribsSpatialManager.get_data_for_files([os.path.join(fc.path, f) for f in files],
                                                                         dataset.srid)
                value_precision = max(
                    TribsSpatialManager.decimal_places(min_val), TribsSpatialManager.decimal_places(max_val), 0
                )
                value_precision = min(value_precision, 4)
                color_ramp_divisions = self.generate_custom_color_ramp_divisions(
                    min_val,
                    max_val,
                    no_data_value=nodata_val,
                    first_division=0,
                    num_divisions=11,
                    value_precision=value_precision
                )
                env_str = self.build_param_string(**color_ramp_divisions)
                viz['env_str'] = env_str

        # Add attribute to dataset for viz url
        if viz is not None:
            dataset.set_attribute('viz', viz)
            session.commit()

    @reload_config()
    def delete_all_layers(self, project, reload_config=True):
        """
        High level method to delete all GeoServer layers for a project.

        Args:
            project(gssha_adapter.resources.project.Project): Project instance.
            reload_config(bool): Whether to reload the config after deleting the layers.
        """
        for dataset in project.datasets:
            self.delete_layer_for_dataset(dataset, reload_config=reload_config)

    @reload_config()
    def delete_layer_for_dataset(self, dataset, reload_config=True):
        """
        High level method to delete all GeoServer layers for a dataset.

        Args:
            dataset(tribs_adapter.resources.dataset.Dataset): Dataset instance.
            reload_config(bool): Whether to reload the config after deleting the layers.
        """
        if dataset.dataset_type == DatasetTypes.FEATURES_SHAPEFILE:
            self.delete_feature_shapefile_layer(dataset, reload_config=False)
        elif dataset.dataset_type == DatasetTypes.RASTER_CONT_ASCII \
                or dataset.dataset_type == DatasetTypes.RASTER_DISC_ASCII:
            self.delete_raster_ascii_layer(dataset, reload_config=False)
        elif dataset.dataset_type == DatasetTypes.RASTER_CONT_GEOTIFF \
                or dataset.dataset_type == DatasetTypes.RASTER_DISC_GEOTIFF:
            self.delete_raster_geotiff_layer(dataset, reload_config=False)
        elif dataset.dataset_type == DatasetTypes.RASTER_CONT_ASCII_TIMESERIES \
                or dataset.dataset_type == DatasetTypes.RASTER_DISC_ASCII_TIMESERIES:
            self.delete_raster_timeseries_ascii_layer(dataset, reload_config=False)
        elif dataset.dataset_type == DatasetTypes.RASTER_CONT_GEOTIFF_TIMESERIES \
                or dataset.dataset_type == DatasetTypes.RASTER_DISC_GEOTIFF_TIMESERIES:
            self.delete_raster_timeseries_geotiff_layer(dataset, reload_config=False)
        elif dataset.dataset_type == DatasetTypes.TRIBS_TIN \
                or dataset.dataset_type in GltfOutputDatasetTypes:
            self.delete_tribs_tin_layer(dataset)
        elif dataset.dataset_type in CompoundDatasetTypes:
            self.delete_all_compound_layers(dataset)

    @reload_config()
    def create_all_styles(self, overwrite=False, reload_config=True):
        """
        High level method to create all GeoServer styles for a project.

        Args:
            overwrite(bool): Whether to overwrite existing styles.
            reload_config(bool): Whether to reload the config after creating the styles.
        """
        # Feature Shapefile Styles
        self.create_feature_shapefile_styles(overwrite=overwrite, reload_config=False)

        # Raster Styles
        self.create_raster_cont_styles(overwrite=overwrite, reload_config=False)
        self.create_raster_disc_styles(overwrite=overwrite, reload_config=False)
        self.create_ndvi_style(overwrite=overwrite, reload_config=False)
        self.create_raster_rgb_style(overwrite=overwrite, reload_config=False)
        self.create_vegetation_types_style(overwrite=overwrite, reload_config=False)
        self.create_parallel_partition_style(overwrite=overwrite, reload_config=False)

    @reload_config()
    def delete_all_styles(self, purge=True, reload_config=True):
        """
        High level method to delete all GeoServer styles for a project.
        """
        # Feature Shapefile Styles
        self.delete_feature_shapefile_styles(purge=purge, reload_config=False)

        # Delete Raster Styles
        self.delete_raster_cont_styles(purge=purge, reload_config=False)
        self.delete_raster_disc_styles(purge=purge, reload_config=False)
        self.delete_ndvi_style(purge=purge, reload_config=False)
        self.delete_raster_rgb_style(purge=purge, reload_config=False)
        self.delete_vegetation_types_style(purge=purge, reload_config=False)
        self.delete_parallel_partition_style(purge=purge, reload_config=False)

    @reload_config()
    def create_feature_shapefile_layer(self, dataset, srid, files, style=None, reload_config=True):
        """
        Create a GeoServer feature layer for a project.

        Args:
            dataset(tribs_adapter.resources.dataset.Dataset): Dataset instance containing the shapefile data.
            srid: EPSG Spatial Reference ID (SRID) of the dataset.
            files(list[str]): List of file paths that make up the shapefile (e.g., .shp, .dbf, .shx).
            style(str, optional): Name of the Geoserver layer style to apply to the layer. Defaults to None.
            reload_config(bool): Whether to reload the config after deleting the layers.
        """
        # Ensure required files given
        prj_path = None
        shp_path = None
        idx_path = None
        dbf_path = None
        for f in files:
            if f.endswith('.prj'):
                prj_path = f
            elif f.endswith('.shp'):
                shp_path = f
            elif f.endswith('.shx'):
                idx_path = f
            elif f.endswith('.dbf'):
                dbf_path = f

        if not shp_path or not idx_path or not dbf_path:
            raise ValueError(
                'Shapefile (.shp), index (.shx), and database (.dbf) files '
                'are required to create a Shapefile feature layer.'
            )

        coverage_name = self.get_unique_item_name(dataset=dataset)

        # Zip shape files and projection file together
        _, tmp_zip_path = tempfile.mkstemp(suffix='.zip')

        # If srid is provided, overwrite the prj file with the given srid
        if srid:
            if prj_path is None and shp_path is not None:
                prj_path = shp_path.replace('.shp', '.prj')
                files.append(prj_path)

            with open(prj_path, 'w') as prj_file:
                prj_file.write(self._get_projection_string(dataset.project, srid))

        with zipfile.ZipFile(tmp_zip_path, 'w') as tmp_zip_file:
            for f in files:
                tmp_zip_file.write(f, coverage_name + os.path.splitext(os.path.basename(f))[1])
        response = self.gs_engine.create_shapefile_resource(
            f'{self.WORKSPACE}:{coverage_name}', overwrite=True, shapefile_zip=tmp_zip_path, default_style=style
        )
        if not response['success']:
            raise Exception(response['error'])

    @reload_config()
    def delete_feature_shapefile_layer(self, dataset, reload_config=True):
        """
        Delete a GeoServer feature layer for a project.
        """
        layer_name = self.get_unique_item_name(dataset=dataset)
        self.gs_engine.delete_layer(layer_id=f'{self.WORKSPACE}:{layer_name}', datastore=layer_name, recurse=True)

    @reload_config()
    def create_raster_ascii_layer(
        self,
        dataset,
        srid,
        raster_map_file=None,
        default_style='',
        other_styles=None,
        reload_config=True,
        variable=''
    ):
        """
        Create a GeoServer raster layer for a project.
        """
        # Get Unique Name
        coverage_name = self.get_unique_item_name(dataset=dataset, variable=variable)

        # Get Projection String
        projection_string = self._get_projection_string(dataset.project, srid)

        # Get project file in temp
        _, tmp_prj_path = tempfile.mkstemp(suffix='.prj')
        with open(tmp_prj_path, 'w') as tmp_prj_file:
            tmp_prj_file.write(projection_string)

        # Zip raster file and projection file together
        _, tmp_zip_path = tempfile.mkstemp(suffix='.zip')

        with zipfile.ZipFile(tmp_zip_path, 'w') as tmp_zip_file:
            tmp_zip_file.write(tmp_prj_path, coverage_name + '.prj')
            tmp_zip_file.write(raster_map_file, coverage_name)

        # Create coverage layer
        self.gs_engine.create_coverage_layer(
            layer_id=f'{self.WORKSPACE}:{coverage_name}',
            coverage_type=self.gs_engine.CT_ARC_GRID,
            coverage_file=tmp_zip_path,
            default_style=default_style,
            other_styles=other_styles,
        )

    @reload_config()
    def delete_raster_ascii_layer(self, dataset, reload_config=True):
        """
        Delete a GeoServer raster layer for a project.
        """
        store_name = self.get_unique_item_name(dataset=dataset)
        self.gs_engine.delete_coverage_store(
            store_id=f'{self.WORKSPACE}:{store_name}',
            recurse=True,
        )

    @reload_config()
    def create_raster_geotiff_layer(
        self, dataset, srid, raster_map_file, default_style='', other_styles=None, reload_config=True, variable=''
    ):
        """
        Create a GeoServer raster layer for a project.
        """
        # Get Unique Name
        coverage_name = self.get_unique_item_name(dataset=dataset, variable=variable)

        # Get Projection String
        projection_string = self._get_projection_string(dataset.project, srid)

        # Get project file in temp
        _, tmp_prj_path = tempfile.mkstemp(suffix='.prj')
        with open(tmp_prj_path, 'w') as tmp_prj_file:
            tmp_prj_file.write(projection_string)

        # Zip raster file and projection file together
        _, tmp_zip_path = tempfile.mkstemp(suffix='.zip')

        with zipfile.ZipFile(tmp_zip_path, 'w') as tmp_zip_file:
            tmp_zip_file.write(tmp_prj_path, coverage_name + '.prj')
            tmp_zip_file.write(raster_map_file, coverage_name)

        # Create coverage layer
        self.gs_engine.create_coverage_layer(
            layer_id=f'{self.WORKSPACE}:{coverage_name}',
            coverage_type=self.gs_engine.CT_GEOTIFF,
            coverage_file=tmp_zip_path,
            default_style=default_style,
            other_styles=other_styles,
        )

    @reload_config()
    def delete_raster_geotiff_layer(self, dataset, reload_config=True):
        """
        Delete a GeoServer raster layer for a project.
        """
        store_name = self.get_unique_item_name(dataset=dataset)
        self.gs_engine.delete_coverage_store(
            store_id=f'{self.WORKSPACE}:{store_name}',
            recurse=True,
        )

    @reload_config()
    def create_raster_timeseries_ascii_layer(
        self,
        dataset,
        srid,
        raster_map_files=None,
        default_style='',
        other_styles=None,
        reload_config=True,
        variable=''
    ):
        """
        Create a GeoServer raster layer for a project.
        """
        tiff_files = []
        tempdir = tempfile.mkdtemp()
        for raster_map_file in raster_map_files:
            new_tiff_name = os.path.splitext(os.path.basename(raster_map_file))[0] + '.tiff'
            new_tiff_temp_path = os.path.join(tempdir, new_tiff_name)
            rio_shutil.copy(raster_map_file, new_tiff_temp_path, 'GTiff')
            tiff_files.append(new_tiff_temp_path)

        self.create_raster_timeseries_geotiff_layer(
            dataset, srid, tiff_files, default_style, other_styles, reload_config=False, variable=variable
        )

    @reload_config()
    def delete_raster_timeseries_ascii_layer(self, dataset, reload_config=True):
        """
        Delete a GeoServer raster layer for a project.
        """
        store_name = self.get_unique_item_name(dataset=dataset)
        self.gs_engine.delete_coverage_store(
            store_id=f'{self.WORKSPACE}:{store_name}',
            recurse=True,
        )

    @reload_config()
    def create_raster_timeseries_geotiff_layer(
        self,
        dataset,
        srid,
        raster_map_files=None,
        default_style='',
        other_styles=None,
        reload_config=True,
        variable=''
    ):
        """
        Create a GeoServer raster layer for a project.
        """
        # Get Unique Name
        coverage_name = self.get_unique_item_name(dataset=dataset, variable=variable)

        # Get Projection String
        projection_string = self._get_projection_string(dataset.project, srid)

        # Get project file in temp
        _, tmp_prj_path = tempfile.mkstemp(suffix='.prj')
        with open(tmp_prj_path, 'w') as tmp_prj_file:
            tmp_prj_file.write(projection_string)

        # Zip raster file and projection file together
        _, tmp_zip_path = tempfile.mkstemp(suffix='.zip')

        # Use name of the first file in tiff_files to find the correct regex pattern
        first_file_name = os.path.splitext(raster_map_files[0])[0] if raster_map_files else ''
        pattern_10_digits = re.compile(r'.*([0-9]{10})')
        pattern_8_digits = re.compile(r'.*([0-9]{8})')

        regex_pattern = ''
        if pattern_10_digits.match(first_file_name):
            regex_pattern = '.*([0-9]{10})'
        elif pattern_8_digits.match(first_file_name):
            regex_pattern = '.*([0-9]{8})'
        else:
            raise ValueError("Timeseries file does not conform to time series data pattern. (YYYYMMDDHH or YYYYMMDD)")

        _, regex_time_path = tempfile.mkstemp(suffix='.properties')
        with open(regex_time_path, 'w') as time_regex_file:
            time_regex_file.write(f'regex={regex_pattern},format=yyyyMMddHH')

        _, index_props_path = tempfile.mkstemp(suffix='.properties')
        with open(index_props_path, 'w') as index_props_file:
            index_props_file.write('Schema=*the_geom:Polygon,location:String,ingestion:java.util.Date\n')
            index_props_file.write('PropertyCollectors=TimestampFileNameExtractorSPI[timeregex]\n')
            index_props_file.write('TimeAttribute=ingestion\n')

        with zipfile.ZipFile(tmp_zip_path, 'w') as tmp_zip_file:
            tmp_zip_file.write(tmp_prj_path, coverage_name + '.prj')
            tmp_zip_file.write(regex_time_path, 'timeregex.properties')
            tmp_zip_file.write(index_props_path, 'indexer.properties')
            for raster_map_file in raster_map_files:
                raster_map_file_name = os.path.basename(raster_map_file)
                tmp_zip_file.write(raster_map_file, raster_map_file_name)

        # Create coverage layer
        tries = 0
        successful = False
        exc = None
        while not successful and tries < 3:
            try:
                self.gs_engine.create_coverage_layer(
                    layer_id=f'{self.WORKSPACE}:{coverage_name}',
                    coverage_type=self.gs_engine.CT_IMAGE_MOSAIC,
                    coverage_file=tmp_zip_path,
                    default_style=default_style,
                    other_styles=other_styles,
                )
                # Enable time dimension
                self.gs_engine.enable_time_dimension(coverage_id=f'{self.WORKSPACE}:{coverage_name}', )
                successful = True
            except requests.RequestException as e:
                tries += 1
                exc = e
        if not successful:
            raise exc

    @reload_config()
    def delete_raster_timeseries_geotiff_layer(self, dataset, reload_config=True):
        """
        Delete a GeoServer raster layer for a project.
        """
        store_name = self.get_unique_item_name(dataset=dataset)
        self.gs_engine.delete_coverage_store(
            store_id=f'{self.WORKSPACE}:{store_name}',
            recurse=True,
        )

    def create_tribs_tin_layer(self, dataset, mesh_epsg, output_dataset=None, output_variables=None):
        """
        Create a GeoServer raster layer for a project.

        Args:
            dataset(tribs_adapter.resources.dataset.Dataset): Dataset instance.
            mesh_epsg(int): EPSG code for the mesh.
            output_dataset(tribs_adapter.resources.dataset.Dataset): Output dataset instance.
            output_variables(list): List of output variables to include in the GLTF.
        """
        # Get Path to dataset workspace
        collection_path = dataset.file_collection_client.path
        output_collection_path = None

        # Find the name of the mesh file
        mesh_file = None
        for f in os.listdir(collection_path):
            if f.endswith('.nodes'):
                mesh_file, _ = os.path.splitext(os.path.join(collection_path, f))
                break

        # Make sure there is a mesh file
        if mesh_file is None:
            raise ValueError('No mesh file found in dataset file collection.')

        # Create a temp location for the generated files
        mesh_file_name = os.path.basename(mesh_file)
        tempdir = tempfile.mkdtemp()
        gltf_path = os.path.join(tempdir, 'gltf')
        os.makedirs(gltf_path, exist_ok=True)
        gltf_out_path = os.path.join(gltf_path, f'{str(dataset.id)}-{mesh_file_name}')

        # Get output files if there is an output dataset
        if output_dataset is None:
            output_files = []
        else:
            output_collection_path = output_dataset.file_collection_client.path
            output_files = [
                os.path.join(output_collection_path, f) for f in os.listdir(output_collection_path)
                if not f.endswith('.json') and os.path.isfile(os.path.join(output_collection_path, f))
            ]

        # Create the gltf
        tribs_mesh = tRIBSMeshViz(mesh_file, mesh_epsg=mesh_epsg, output_files=output_files)
        meta = tribs_mesh.to_gltf(
            gltf_out_path, to_epsg=mesh_epsg, output_variables=output_variables, generate_legend=True
        )

        # If we have an output dataset, add the gltf to the output dataset
        dataset_to_add_to = dataset
        collection_path_to_add_to = collection_path
        if output_dataset is not None:
            dataset_to_add_to = output_dataset
            collection_path_to_add_to = output_collection_path

        # remove the gltf if it already exists
        if 'gltf' in os.listdir(collection_path_to_add_to):
            dataset_to_add_to.file_collection_client.delete_item('gltf')

        # Add the gltf to the dataset
        dataset_to_add_to.file_collection_client.add_item(gltf_path)
        return meta

    def create_tribs_czml_layer(self, dataset, session, files, srid):
        """
        Create a Pixel czml file for a dataset.

        Args:
            dataset(tribs_adapter.resources.dataset.Dataset): Dataset instance.
            session(sqlalchemy.orm.Session): SQLAlchemy session.
            files(list): List of files in the dataset file collection.
            srid(int): EPSG code for the mesh.
        """
        from tribs_adapter.resources import Dataset

        extent = None
        origin = None

        # Get Point File Dataset
        if dataset.dataset_type not in SdfDatasetTypes:
            link = dataset.linked_realizations[0]
            start_date = link.input_file.run_parameters.time_variables.STARTDATE
            run_time = link.input_file.run_parameters.time_variables.RUNTIME
            output_interval = link.input_file.run_parameters.time_variables.OPINTRVL
            output_node_file = link.input_file.files_and_pathnames.mesh_generation.INPUTDATAFILE
            node_file_dataset = session.query(Dataset).get(str(output_node_file.resource_id))

            # Get *.points file from point file dataset
            node_file_fc = node_file_dataset.file_collection_client
            node_files = os.listdir(node_file_fc.path)
            node_file = [os.path.join(node_file_fc.path, f) for f in node_files if f.endswith('.nodes')][0]

        # Create a temp dir to write czml files to
        with tempfile.TemporaryDirectory() as tempdir:
            czml_path = os.path.join(tempdir, 'czml')
            os.makedirs(czml_path, exist_ok=True)

            if dataset.dataset_type == DatasetTypes.TRIBS_OUT_PIXEL:
                pixels_files = [
                    os.path.join(dataset.file_collection_client.path, f) for f in files if f.endswith('.pixel')
                ]
                pixel_file_variables = get_file_variables(
                    pixels_files[0]
                )  # All pixel files should have the same variables
                for variable in pixel_file_variables:
                    czml_file_path = os.path.join(czml_path, f'{str(dataset.id)}-{variable}.czml')
                    generate_czml_for_pixel_files(
                        node_file,
                        pixels_files,
                        start_date,
                        run_time,
                        output_interval,
                        czml_file_path,
                        str(dataset.id),
                        variable,
                        srid=srid
                    )
            elif dataset.dataset_type == DatasetTypes.TRIBS_OUT_QOUT:
                qout_files = [
                    os.path.join(dataset.file_collection_client.path, f) for f in files if f.endswith('.qout')
                ]
                qout_variables = get_file_variables(qout_files[0], skip_cols=1)
                for variable in qout_variables:
                    czml_file_path = os.path.join(czml_path, f'{str(dataset.id)}-{variable}.czml')
                    generate_czml_for_qout_files(
                        node_file,
                        qout_files,
                        start_date,
                        run_time,
                        output_interval,
                        czml_file_path,
                        str(dataset.id),
                        variable,
                        srid=srid
                    )
            elif dataset.dataset_type in [DatasetTypes.TRIBS_OUT_MRF, DatasetTypes.TRIBS_OUT_RFT]:
                extension = '.mrf' if dataset.dataset_type == DatasetTypes.TRIBS_OUT_MRF else '.rft'
                out_files = [
                    os.path.join(dataset.file_collection_client.path, f) for f in files if f.endswith(extension)
                ]
                out_variables = get_output_file_variables(out_files[0])
                for variable in out_variables:
                    czml_file_path = os.path.join(czml_path, f'{str(dataset.id)}-{variable}.czml')
                    generate_czml_for_mrf_and_rft_files(
                        node_file,
                        out_files,
                        start_date,
                        run_time,
                        output_interval,
                        czml_file_path,
                        str(dataset.id),
                        variable,
                        srid=srid
                    )
            elif dataset.dataset_type in SdfDatasetTypes:
                # Get the sdf file
                sdf_files = [os.path.join(dataset.file_collection_client.path, f) for f in files if f.endswith('.sdf')]
                if len(sdf_files) == 0:
                    raise ValueError('No SDF file found in dataset file collection.')
                sdf_file = sdf_files[0]

                # Read the sdf file. First line has 2 fields, number of stations, and number of params
                stations = []
                with open(sdf_file, 'r') as f:
                    num_stations, num_params = f.readline().split()
                    num_stations = int(num_stations)
                    num_params = int(num_params)
                    for _ in range(num_stations):
                        # Station name, lat, lon, and elevation
                        station_params = f.readline().split()
                        if len(station_params) != num_params:
                            raise ValueError('Invalid SDF file format.')
                        mdf_file = os.path.basename(station_params[1])
                        lat = None
                        long = None
                        if len(station_params) == 10:
                            lat = station_params[3]
                            long = station_params[5]
                        else:
                            lat = station_params[2]
                            long = station_params[3]
                        stations.append((station_params[0], mdf_file, lat, long, station_params[-3]))
                if len(stations) != num_stations:
                    raise ValueError('Invalid SDF file format.')

                czml_path = os.path.join(tempdir, 'czml')
                nodes = []
                for station in stations:
                    station_file = os.path.join(dataset.file_collection_client.path, station[1])
                    czml_file_path = os.path.join(czml_path, f'{str(dataset.id)}-{station[0]}.czml')
                    df = None
                    with open(station_file, 'r') as f:
                        # Read the file into a df using the first line has headers
                        df = pd.read_csv(f, header=0, sep=r'\s+')
                    if df is None or df.empty:
                        raise ValueError('Could not read the station file.')

                    # Get the list of headers except the first four
                    variables = df.columns[4:]

                    # Get first item from dataframe
                    ts1 = df.iloc[0]
                    ts2 = df.iloc[1]

                    # Get Date from Y M D H from ts1 and ts2
                    ts1_dt = datetime.datetime(int(ts1['Y']), int(ts1['M']), int(ts1['D']), int(ts1['H']))
                    ts2_dt = datetime.datetime(int(ts2['Y']), int(ts2['M']), int(ts2['D']), int(ts2['H']))

                    # calculate interval between ts1 and ts2 in hours
                    interval = (ts2_dt - ts1_dt).seconds / 3600

                    start_date = ts1_dt
                    output_interval = interval

                    generate_czml_for_sdf_station(
                        start_date,
                        station[4],
                        output_interval,
                        czml_path,
                        lat=station[2],
                        long=station[3],
                        id=station[0],
                        station_file=station_file,
                        variables=variables,
                        data=df,
                        srid=srid
                    )

                    nodes.extend(reproject(np.array([n[:3] for n in [(station[3], station[2], 0.0)]]), srid))
                # calculate the center of a list of points
                origin = [sum([n[0] for n in nodes]) / len(nodes), sum([n[1] for n in nodes]) / len(nodes)]
                extent = get_extents(nodes, flat=True)

            else:
                raise ValueError(f"Dataset type {dataset.DatasetType} is not a supported czml dataset type.")

            # remove the czml if it already exists
            if 'czml' in os.listdir(dataset.file_collection_client.path):
                dataset.file_collection_client.delete_item('czml')
            dataset.file_collection_client.add_item(czml_path)

        if extent is None or origin is None:
            _, _extent, _origin, _, _ = get_nodes(node_file, srid, flatten_extents=True)

        if extent is None:
            extent = _extent

        if origin is None:
            origin = _origin

        meta = {
            'origin': origin,
            'extents': extent,
        }

        return meta

    def delete_tribs_tin_layer(self, dataset):
        """
        Delete a GeoServer raster layer for a project.

        Args:
            dataset(tribs_adapter.resources.dataset.Dataset): Dataset instance.
        """
        collection_path = dataset.file_collection_client.path
        if 'gltf' in os.listdir(collection_path):
            dataset.file_collection_client.delete_item('gltf')

    def create_all_compound_layers(self, dataset, srid):
        """
        Create all compound layers for a dataset.

        Args:
            dataset(tribs_adapter.resources.dataset.Dataset): Dataset instance.
            session(sqlalchemy.orm.Session): SQLAlchemy session.
        """
        # Generate different compound dataset layers
        env_strs = None
        if dataset.dataset_type == DatasetTypes.TRIBS_GRID_DATA:
            layers, extent, env_strs = self._create_layers_for_gdf_file_dataset(dataset, srid)
        elif dataset.dataset_type == DatasetTypes.SOILGRID_PHYSICAL_SOIL_DATA:
            layers, extent = self._create_layers_for_soil_grid(dataset, srid)
        else:
            raise ValueError(f"Dataset type {dataset.dataset_type} is not a supported compound dataset type.")
        return layers, extent, env_strs

    def _create_layers_for_soil_grid(self, dataset, srid):
        layers = []
        fc = dataset.file_collection_client
        for file in fc.files:
            if file.endswith('.tif'):  # TODO will the file always endswith tif?
                label = re.search(r"(.+cm)", file).group(1)
                coverage_name = self.get_unique_item_name(dataset=dataset, variable=label)
                layers.append(coverage_name)
                path = os.path.join(fc.path, file)
                self.create_raster_geotiff_layer(dataset, srid, path, default_style=self.S_RASTER, variable=label)

        extent = dataset.get_attribute("extent", None)
        if extent:
            extent = extent["extent"]
        else:
            files = [os.path.join(fc.path, file) for file in fc.files if not file.endswith('.json')]
            extent, _ = TribsSpatialManager.get_data_for_files(files, dataset.srid)

        return layers, extent

    def _create_layers_for_gdf_file_dataset(self, dataset, srid):
        fc = dataset.file_collection_client
        files = os.listdir(fc.path)
        gdf_files = [os.path.join(fc.path, f) for f in files if f.endswith('.gdf')]
        if len(gdf_files) == 0:
            raise ValueError('No GDF file found in dataset file collection.')
        gdf_file = gdf_files[0]
        param_count = 0
        params = []
        layers = []
        env_strs = {}
        with open(gdf_file, 'r') as f:
            # First line param count
            param_count = int(f.readline())
            # Second line lat, lon, gmt
            _ = f.readline()
            # rest of the lines are param, path, ext
            for _ in range(param_count):
                param, path, ext = f.readline().split()
                params.append((param, path, ext))

        # create ascii raster layer for each param
        all_files = []
        for param, rpath, ext in params:
            if rpath == 'NO_DATA':
                continue

            # glob files ending in ext
            if rpath.startswith("../"):
                rpath = rpath.split('/', 2)[2]
            raster_path = os.path.join(fc.path, rpath)
            files = glob.glob(f'{raster_path}*.{ext}')
            coverage_name = self.get_unique_item_name(dataset=dataset, variable=param)
            layers.append(coverage_name)

            if len(files) == 0:
                log.warning(f'Expected file for param "{param}", but it could not be found in dataset file collection.')
                continue

            all_files.extend(files)

            is_tiff = mimetypes.guess_type(files[0])[0] == 'image/tiff'
            style = self.GDF_FILE_TO_STYLE.get(param, self.S_RASTER)
            if style != self.S_RASTER:
                style = f'{self.WORKSPACE}:{style}'
            if len(files) > 1:
                if is_tiff:
                    self.create_raster_timeseries_geotiff_layer(dataset, srid, files, variable=param)
                else:
                    self.create_raster_timeseries_ascii_layer(dataset, srid, files, default_style=style, variable=param)
            else:  # single file
                if is_tiff:
                    self.create_raster_geotiff_layer(dataset, srid, files[0], default_style=style, variable=param)
                else:
                    self.create_raster_ascii_layer(dataset, srid, files[0], default_style=style, variable=param)
            _, [min_val, max_val,
                nodata_val] = TribsSpatialManager.get_data_for_files([os.path.join(fc.path, f) for f in files],
                                                                     dataset.srid)
            value_precision = max(
                TribsSpatialManager.decimal_places(min_val), TribsSpatialManager.decimal_places(max_val), 0
            )
            value_precision = min(value_precision, 4)
            color_ramp_divisions = self.generate_custom_color_ramp_divisions(
                min_val,
                max_val,
                no_data_value=nodata_val,
                first_division=0,
                num_divisions=11 if style == f'{self.WORKSPACE}:{self.S_RASTER_CONT}' else 105,
                value_precision=value_precision
            )
            env_str = self.build_param_string(**color_ramp_divisions)
            env_strs[param] = env_str

        extent, _ = TribsSpatialManager.get_data_for_files(all_files, dataset.srid)
        return layers, extent, env_strs

    @staticmethod
    def get_data_for_files(files, srid):
        """Get the largest extent encompasses all specified files

        Args:
            files (List[str]): A list of file paths.
            srid (int): The srid associated with the files.

        Returns:
            Tuple[List[float], List[float]]:
                A tuple containing:
                - extent: [min_x, min_y, max_x, max_y]
                - stats: [data_min, data_max, no_data]
        """
        x_min, y_min, x_max, y_max = 180, 90, -180, -90  # extent for the dataset
        data_min, data_max = None, None
        transformer = Transformer.from_crs(f"EPSG:{srid}", 'EPSG:4326', always_xy=True)
        for file in files:
            if file.endswith('.json') or file.endswith('.xml') or file.endswith('.tifw'):
                continue

            try:
                with rasterio.open(file) as raster:
                    bounds = raster.bounds
                    left, bottom = transformer.transform(bounds.left, bounds.bottom)
                    right, top = transformer.transform(bounds.right, bounds.top)
                    x_min = min(x_min, left)
                    x_max = max(x_max, right)
                    y_min = min(y_min, bottom)
                    y_max = max(y_max, top)
                    no_data = raster.nodata
                    for i in raster.indexes:
                        stats = raster.statistics(i)
                        if data_min is None:
                            data_min = stats.min
                        if data_max is None:
                            data_max = stats.max
                        data_min = min(data_min, stats.min)
                        data_max = max(data_max, stats.max)
            except rasterio.errors.RasterioIOError:
                log.warning(f'Could not read file {file}.')

        return [x_min, y_min, x_max, y_max], [data_min, data_max, no_data]

    def delete_all_compound_layers(self, dataset):
        """
        Delete all compound layers for a dataset.

        Args:
            dataset(tribs_adapter.resources.dataset.Dataset): Dataset instance.
        """
        viz = dataset.get_attribute('viz')
        layers = viz.get('layer', [])
        for layer in layers:
            self.gs_engine.delete_coverage_store(
                store_id=f'{self.WORKSPACE}:{layer}',
                recurse=True,
            )

    @reload_config()
    def create_feature_shapefile_styles(self, overwrite=False, reload_config=True):
        """
        Create GeoServer feature shapefile styles.
        Args:
            overwrite(bool): Overwrite style if already exists when True. Defaults to False.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        # Create Base Style
        self.gs_engine.create_style(
            style_id=self.get_unique_item_name(
                dataset=None, variable=DatasetTypes.FEATURES_SHAPEFILE.lower(), with_workspace=True
            ),
            sld_template=os.path.join(self.SLD_PATH,
                                      DatasetTypes.FEATURES_SHAPEFILE.lower() + '.sld'),
            sld_context={},
            overwrite=overwrite
        )

        # Create Labels Style
        context = {'is_label_style': True, 'label_property': 'area'}
        self.gs_engine.create_style(
            style_id=self.get_unique_item_name(
                dataset=None,
                variable=DatasetTypes.FEATURES_SHAPEFILE.lower(),
                suffix=self.LABELS_SUFFIX,
                with_workspace=True
            ),
            sld_template=os.path.join(self.SLD_PATH,
                                      DatasetTypes.FEATURES_SHAPEFILE.lower() + '.sld'),
            sld_context=context,
            overwrite=overwrite
        )

    @reload_config()
    def delete_feature_shapefile_styles(self, purge=True, reload_config=True):
        """
        Delete a GeoServer feature shapefile styles.
        """
        self.gs_engine.delete_style(
            style_id=self.get_unique_item_name(
                dataset=None, variable=DatasetTypes.FEATURES_SHAPEFILE.lower(), with_workspace=True
            ),
            purge=purge
        )

    @reload_config()
    def create_raster_cont_styles(self, overwrite=False, reload_config=True):
        """
        Create a GeoServer continuous raster styles.
        Args:
            overwrite(bool): Overwrite style if already exists when True. Defaults to False.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        # Create Base Style

        self.gs_engine.create_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_RASTER_CONT, with_workspace=True),
            sld_template=os.path.join(self.SLD_PATH, f'{self.S_RASTER_CONT}.sld'),
            sld_context={},
            overwrite=overwrite
        )

    @reload_config()
    def create_raster_disc_styles(self, overwrite=False, reload_config=True):
        """
        Create a GeoServer discrete raster styles.
        Args:
            overwrite(bool): Overwrite style if already exists when True. Defaults to False.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        # Create Base Style

        self.gs_engine.create_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_RASTER_DISC, with_workspace=True),
            sld_template=os.path.join(self.SLD_PATH, f'{self.S_RASTER_DISC}.sld'),
            sld_context={},
            overwrite=overwrite
        )

    @reload_config()
    def create_ndvi_style(self, overwrite=False, reload_config=True):
        """
        Create a Geoserver ndvi style

        Args:
            overwrite(bool): Overwrite style if already exists when True. Defaults to False.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        self.gs_engine.create_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_NDVI, with_workspace=True),
            sld_template=os.path.join(self.SLD_PATH, f'{self.S_NDVI}.sld'),
            sld_context={},
            overwrite=overwrite
        )

    @reload_config()
    def create_raster_rgb_style(self, overwrite=False, reload_config=True):
        """
        Create a Geoserver raster rgb style

        Args:
            overwrite(bool): Overwrite style if already exists when True. Defaults to False.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        self.gs_engine.create_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_RASTER_RGB, with_workspace=True),
            sld_template=os.path.join(self.SLD_PATH, f'{self.S_RASTER_RGB}.sld'),
            sld_context={},
            overwrite=overwrite
        )

    @reload_config()
    def create_vegetation_types_style(self, overwrite=False, reload_config=True):
        """
        Create a Geoserver vegetation types style

        Args:
            overwrite(bool): Overwrite style if already exists when True. Defaults to False.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        self.gs_engine.create_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_VT, with_workspace=True),
            sld_template=os.path.join(self.SLD_PATH, f'{self.S_VT}.sld'),
            sld_context={},
            overwrite=overwrite
        )

    @reload_config()
    def create_parallel_partition_style(self, overwrite=False, reload_config=True):
        self.gs_engine.create_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_PP, with_workspace=True),
            sld_template=os.path.join(self.SLD_PATH, f'{self.S_PP}.sld'),
            sld_context={},
            overwrite=overwrite
        )

    @reload_config()
    def delete_raster_cont_styles(self, purge=True, reload_config=True):
        """
        Delete a GeoServer ascii raster styles.
        Args:
            purge(bool): Force remove all resources associated with style.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        # Delete Base Style
        self.gs_engine.delete_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_RASTER_CONT, with_workspace=True),
            purge=purge
        )

    @reload_config()
    def delete_raster_disc_styles(self, purge=True, reload_config=True):
        """
        Delete a GeoServer ascii raster styles.

        Args:
            purge(bool): Force remove all resources associated with style.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        # Delete Base Style
        self.gs_engine.delete_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_RASTER_DISC, with_workspace=True),
            purge=purge
        )

    @reload_config()
    def delete_ndvi_style(self, purge=True, reload_config=True):
        """
        Delete the GeoServer ndvi style.
        Args:
            purge(bool): Force remove all resources associated with style.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        # Delete Base Style
        self.gs_engine.delete_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_NDVI, with_workspace=True), purge=purge
        )

    @reload_config()
    def delete_raster_rgb_style(self, purge=True, reload_config=True):
        """
        Delete the GeoServer raster rgb style.
        Args:
            purge(bool): Force remove all resources associated with style.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        # Delete Base Style
        self.gs_engine.delete_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_RASTER_RGB, with_workspace=True),
            purge=purge
        )

    @reload_config()
    def delete_vegetation_types_style(self, purge=True, reload_config=True):
        """
        Delete the GeoServer vegetation_types style.
        Args:
            purge(bool): Force remove all resources associated with style.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        # Delete Base Style
        self.gs_engine.delete_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_VT, with_workspace=True), purge=purge
        )

    @reload_config()
    def delete_parallel_partition_style(self, purge=True, reload_config=True):
        """
        Delete the GeoServer parallel_partition style.
        Args:
            purge(bool): Force remove all resources associated with style.
            reload_config(bool): Reload the GeoServer node configuration and catalog before returning if True.
        """
        # Delete Base Style
        self.gs_engine.delete_style(
            style_id=self.get_unique_item_name(dataset=None, variable=self.S_PP, with_workspace=True), purge=purge
        )

    def get_unique_item_name(self, dataset, variable='', suffix='', with_workspace=False) -> str:
        """
        Construct the unique name for the specified item

        Args:
            dataset(str): Dataset object.
            variable(str): Variable name.
            suffix(str): Suffix to append to the name.
            project(object): Project instance.
            scenario_id(str): Scenario ID.
            with_workspace(bool): Whether to include the workspace in the name.

        Returns:
            str: Unique name for the item.
        """
        # e.g.: <model_id>_<scenario_id>_<item_name>_<suffix>
        name_parts = []

        if dataset is not None:
            name_parts.append(str(dataset.id).replace('_', '-'))

        if variable:
            name_parts.append(variable)

        # e.g.: 88c1b4ce-7def-43fd-b19f-1fca8fea282d_model_boundary_legend
        if suffix:
            name_parts.append(suffix)

        name = '_'.join(name_parts)

        if with_workspace:
            return f'{self.WORKSPACE}:{name}'

        return name

    def _get_projection_string(self, resource, srid, proj_format=''):
        """
        Get the projection string as either wkt or proj4 format.

        Args:
            resource(Resource): a Resource instance (Project, Dataset, Scenario, Realization).
            srid(int): EPSG spatial reference identifier.
            proj_format(str): project string format (either SpatialManager.PRO_WKT or SpatialManager.PRO_PROJ4).

        Returns:
            str: projection string.
        """
        if not proj_format:
            proj_format = self.PRO_WKT

        if proj_format not in (self.PRO_WKT, self.PRO_PROJ4):
            raise ValueError(
                'Invalid projection format given: {}. Use either SpatialManager.PRO_WKT or '
                'SpatialManager.PRO_PROJ4.'.format(proj_format)
            )

        if srid not in self._projection_string or proj_format not in self._projection_string[srid]:
            db_engine = create_engine(Session.object_session(resource).get_bind().engine.url)
            try:
                if proj_format is self.PRO_WKT:
                    sql = "SELECT srtext AS proj_string FROM spatial_ref_sys WHERE srid = {}".format(srid)
                else:
                    sql = "SELECT proj4text AS proj_string FROM spatial_ref_sys WHERE srid = {}".format(srid)

                ret = db_engine.execute(sql)
                projection_string = ''

                for row in ret:
                    projection_string = row.proj_string
            finally:
                db_engine.dispose()

            if srid not in self._projection_string:
                self._projection_string[srid] = {}

            self._projection_string[srid].update({proj_format: projection_string})

        return self._projection_string[srid][proj_format]

    def get_wms_layer_legend_url(self, layer):
        return f'{self.gs_engine.get_wms_endpoint()}?REQUEST=GetLegendGraphic&VERSION' \
               f'=1.0.0&FORMAT=image/png&WIDTH=20&HEIGHT=20&LAYER={layer}'

    @staticmethod
    def decimal_places(num):
        return len(str(num).split('.')[-1].rstrip('0'))

    @staticmethod
    def generate_custom_color_ramp_divisions(
        min_value,
        max_value,
        num_divisions=10,
        value_precision=2,
        first_division=1,
        top_offset=0,
        bottom_offset=0,
        prefix='val',
        need_color=False,
        color_ramp="",
        color_prefix='color',
        no_data_value=None
    ):
        """
        Generate custom elevation divisions.

        Args:
            min_value(number): minimum value.
            max_value(number): maximum value.
            num_divisison(int): number of divisions.
            value_precision(int): level of precision for legend values.
            first_division(int): first division number (defaults to 1).
            top_offset(number): offset from top of color ramp (defaults to 0).
            bottom_offset(number): offset from bottom of color ramp (defaults to 0).
            prefix(str): name of division variable prefix (i.e.: 'val' for pattern 'val1').
            color_ramp(str): color ramp name in COLOR_RAMPS dict. Options are ['Blue', 'Blue and Red', 'Flower Field', 'Galaxy Berries', 'Heat Map', 'Olive Harmony', 'Mother Earth', 'Rainforest Frogs', 'Retro FLow', 'Sunset Fade']
            color_prefix(str): name of color variable prefix (i.e.: 'color' for pattern 'color1').
            no_data_value (str): set no data value for the color ramp. (defaults to None).
        Returns:
            dict<name, value>: custom divisions
        """  # noqa: E501
        divisions = {}

        # Equation of a Line
        max_div = first_division + num_divisions - 1
        min_div = first_division
        max_val = float(max_value - top_offset)
        min_val = float(min_value + bottom_offset)

        if min_val == max_val:
            max_val = max_val + 1

        y2_minus_y1 = max_val - min_val
        x2_minus_x1 = max_div - min_div
        m = y2_minus_y1 / x2_minus_x1
        b = max_val - (m * max_div)
        divisions['val_no_data'] = no_data_value
        for i in range(min_div, max_div + 1):
            value = round(m * i + b, value_precision)
            divisions[f'{prefix}{i}'] = f"{value}"

            if need_color:
                if color_ramp in COLOR_RAMPS.keys():
                    divisions[f'{color_prefix}{i}'] =\
                        f"{COLOR_RAMPS[color_ramp][(i - first_division) % len(COLOR_RAMPS[color_ramp])]}"
                else:
                    # use default color ramp
                    divisions[f'{color_prefix}{i}'] =\
                        f"{COLOR_RAMPS['Default'][(i - first_division) % len(COLOR_RAMPS['Default'])]}"
        if no_data_value is not None:
            divisions['val_no_data'] = no_data_value
        return divisions

    @staticmethod
    def build_param_string(**kwargs):
        """
        Build a VIEWPARAMS or ENV string with given kwargs (e.g.: 'foo:1;bar:baz')

        Args:
            **kwargs: key-value pairs of paramaters.

        Returns:
            str: parameter string.
        """
        if not kwargs:
            return ''

        joined_pairs = []
        for k, v in kwargs.items():
            joined_pairs.append(':'.join([k, str(v)]))

        param_string = ';'.join(joined_pairs)
        return param_string
