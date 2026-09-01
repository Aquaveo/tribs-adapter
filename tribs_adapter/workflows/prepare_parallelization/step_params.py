import logging
import param
from tribs_adapter.common.dataset_types import DatasetTypes
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow

log = logging.getLogger(f'tethys.{__name__}')


class DatasetParam(param.Parameterized):
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
        tin_options = [
            f'{dataset.name}:{dataset.id}'
            for dataset in self._resource.datasets if dataset.dataset_type is DatasetTypes.TRIBS_TIN
        ]
        self.param.add_parameter(
            'tin_dataset',
            param.Selector(
                label='TIN Dataset',
                doc='Select a TIN dataset to use for parallel partitioning.',
                objects=tin_options,
                check_on_set=True,
                allow_None=False,
                precedence=1
            )
        )
        stream_options = ['None']
        stream_options.extend([
            f'{dataset.name}:{dataset.id}'
            for dataset in self._resource.datasets if dataset.dataset_type is DatasetTypes.FEATURES_SHAPEFILE
        ])
        self.param.add_parameter(
            'stream_dataset',
            param.Selector(
                label='Stream Dataset (optional)',
                doc='Select a stream dataset to overlay on the partition graph for additional context.',
                objects=stream_options,
                check_on_set=True,
                allow_None=True,
                precedence=2
            )
        )


class ModelSetupParam(param.Parameterized):
    """
    Param form that defines the form in the Model Setup step
    """
    def __init__(self, *args, **kwargs):
        # Pop these to avoid warning messages.
        self._request = kwargs.pop('request', None)
        self._session = kwargs.pop('session', None)
        self._resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)
        self.set_data_options()

    def set_data_options(self):
        mode_options = ['Surface', 'Surface-Subsurface']
        self.param.add_parameter(
            'mode',
            param.Selector(
                label='Mode',
                doc='Select the parallel partitioning approach.',
                objects=mode_options,
                default=mode_options[0],
                precedence=1,
                check_on_set=True,
                allow_None=False
            )
        )

        workflow_id = self._request.path.split('/step')[0].split('/')[-1]
        workflow = self._session.query(ResourceWorkflow).get(workflow_id)
        num_reach = int(workflow.get_attribute('preprocess_tin_output').get('num_reach'))
        num_processor_min = min(num_reach, 2)
        num_processor_max = min(num_reach, 256)
        self.param.add_parameter(
            'num_processor',
            param.Integer(
                default=num_processor_min,
                bounds=(num_processor_min, num_processor_max),
                label=(
                    "Number of Processors " +
                    (f"(Input a number between {num_processor_min} and {num_processor_max})" if num_reach != 1 else "")
                ),
                doc=(
                    "⚠ The model cannot run because this dataset contains only one reach. "
                    "Please select a different dataset and try again."
                    if num_reach == 1 else f"Input a number between {num_processor_min} and {num_processor_max}"
                ),
                precedence=2,
                allow_None=False,
                readonly=True if num_reach == 1 else False,
            )
        )
