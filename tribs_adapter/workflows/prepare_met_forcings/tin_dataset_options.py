import logging

import param

log = logging.getLogger(f'tethys.{__name__}')


class TinDatasetOptions(param.Parameterized):
    """
    Param form that defines the form in the NLDAS TIN Dataset options step
    """
    def __init__(self, *args, **kwargs):
        # Pop these to avoid warning messages.
        self._request = kwargs.pop('request', None)
        self._session = kwargs.pop('session', None)
        self._resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)
        self.set_tin_dataset_options()

    def set_param(self, key, val):
        setattr(self.param, key, val)
        # self.param.update({key, val})

    def set_tin_dataset_options(self):
        available_datasets = []
        datasets = self._resource.datasets
        for dataset in datasets:
            dataset_type = dataset.dataset_type
            if dataset_type in 'TRIBS_TIN':
                available_datasets.append(dataset)

        default = available_datasets
        self.param.add_parameter(
            'tin_datasets',
            param.ListSelector(
                label='TIN Datasets',
                doc='Select one or more dataset to run for this analysis.',
                default=default,
                objects=available_datasets,
                allow_None=False
            )
        )
