import logging
import param
from tribs_adapter.common.dataset_types import DatasetTypes, GisDatasetTypes


log = logging.getLogger(f'tethys.{__name__}')


class DatasetsParam(param.Parameterized):
    """
    Param form that defines the form in the Select Datasets step
    """
    def __init__(self, *args, **kwargs):
        # Pop these to avoid warning messages.
        self._request = kwargs.pop('request', None)
        self._session = kwargs.pop('session', None)
        self._resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)
        self.set_data_options()

    def set_data_options(self):
        geotiff_types = [DatasetTypes.RASTER_CONT_GEOTIFF, DatasetTypes.RASTER_DISC_GEOTIFF]
        raster_options = [
            f'{dataset.name}:{dataset.id}'
            for dataset in self._resource.datasets if dataset.dataset_type in geotiff_types
        ]
        self.param.add_parameter(
            'lu_dataset',
            param.Selector(
                label='Look Up (LU) Raster (GeoTIFF)',
                doc='Select the LU Raster (GeoTIFF) to prepare.',
                objects=raster_options,
                check_on_set=True,
                allow_None=False
            )
        )
        shapefile_options = [
            f'{dataset.name}:{dataset.id}'
            for dataset in self._resource.datasets if dataset.dataset_type in GisDatasetTypes
        ]
        self.param.add_parameter(
            'watershed_boundary_dataset',
            param.Selector(
                label='Watershed Boundary (Shapefile)',
                doc='Select the Watershed Boundary (Shapefile) to prepare.',
                objects=shapefile_options,
                check_on_set=True,
                allow_None=False
            )
        )
        self.param.add_parameter(
            'output_name',
            param.String(
                default="Landcover",
                label="Output Dataset Name Base",
                doc="The base of output datasets names",
                allow_None=False
            )
        )
