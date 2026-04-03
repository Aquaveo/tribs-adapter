import logging

import param

log = logging.getLogger(f'tethys.{__name__}')


class NldasDatasetOptions(param.Parameterized):
    """
    Param form that defines the form in the NLDAS Dataset options step
    """
    def __init__(self, *args, **kwargs):
        # Pop these to avoid warning messages.
        self._request = kwargs.pop('request', None)
        self._session = kwargs.pop('session', None)
        self._resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)
        self.set_nldas_dataset_options()

    def set_param(self, key, val):
        setattr(self.param, key, val)
        # self.param.update({key, val})

    def set_nldas_dataset_options(self):
        available_datasets = []
        datasets = self._resource.datasets
        for dataset in datasets:
            dataset_type = dataset.dataset_type
            # Use only GRIDDED_NETCDF_TIMESERIES type datasets.
            if dataset_type in 'GRIDDED_NETCDF_TIMESERIES':
                available_datasets.append(dataset)

        default = available_datasets
        self.param.add_parameter(
            'nldas_datasets',
            param.ListSelector(
                label='NLDAS Datasets',
                doc='Select one or more dataset to run for this analysis.',
                default=default,
                objects=available_datasets,
                allow_None=False
            )
        )
