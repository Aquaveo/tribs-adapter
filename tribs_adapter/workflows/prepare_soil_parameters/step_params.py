import logging

import param

from tribs_adapter.common.dataset_types import DatasetTypes

log = logging.getLogger(f'tethys.{__name__}')


class SoilDatasetsParam(param.Parameterized):
    """
    Param form that defines the form in the Routing Options step
    """
    def __init__(self, *args, **kwargs):
        # Pop these to avoid warning messages.
        self._request = kwargs.pop('request', None)
        self._session = kwargs.pop('session', None)
        self._resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)
        self.set_data_options()

    def set_data_options(self):
        options = [
            f'{dataset.name}:{dataset.id}'
            for dataset in self._resource.datasets if dataset.dataset_type in DatasetTypes.SOILGRID_PHYSICAL_SOIL_DATA
        ]
        default = []
        self.param.add_parameter(
            'raster_datasets',
            param.ListSelector(
                label='Soil Input Datasets',
                doc='Select one Soil Input dataset to run Rosetta3 on.',
                default=default,
                precedence=1,
                objects=options,
                allow_None=False
            )
        )
        self.param.add_parameter(
            'output_name',
            param.String(
                default="Soil Output",
                label="Output Dataset Name Base",
                doc="The base of output datasets names",
                precedence=2,
                allow_None=False
            )
        )
