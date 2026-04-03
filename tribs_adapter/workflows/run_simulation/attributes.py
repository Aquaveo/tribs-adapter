import logging
import param

from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.resources.dataset import Dataset
from tethysext.atcore.models.app_users.resource_workflow import ResourceWorkflow

log = logging.getLogger(f'tethys.{__name__}')


class PointAttributes(param.Parameterized):
    point_name = param.String(
        label="Name",
        doc="Name of point that will be used to reference it in results.",
        allow_None=False,  #: Required
    )


class ScenarioOptions(param.Parameterized):
    """
    Param form that defines the form in the Scenario Options dataset step
    """
    def __init__(self, *args, **kwargs):
        # Pop these to avoid warning messages.
        self._request = kwargs.pop('request', None)
        self._session = kwargs.pop('session', None)
        self._resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)
        self.set_scenario_options()

    def set_param(self, key, val):
        setattr(self.param, key, val)
        # self.param.update({key, val})

    def set_scenario_options(self):
        available_scenarios = self._resource.scenarios
        options = [f'{scenario.name}:{scenario.id}' for scenario in available_scenarios]  # Format with (name:id)

        default = options
        self.param.add_parameter(
            'scenarios',
            param.ListSelector(
                label='Scenario (choose one)',
                doc='Select scenario to run.',
                default=default,
                objects=options,
                allow_None=False
            )
        )


class ParallelPartitionOptions(param.Parameterized):
    """
    Param form that defines the form in the Select a Parallel Partitioning Dataset step
    """
    def __init__(self, *args, **kwargs):
        # Pop these to avoid warning messages.
        self._request = kwargs.pop('request', None)
        self._session = kwargs.pop('session', None)
        self._resource = kwargs.pop('resource', None)
        super().__init__(*args, **kwargs)
        self.set_dataset_options()

    def set_param(self, key, val):
        setattr(self.param, key, val)

    def set_dataset_options(self):
        workflow_id = self._request.path.split('/step')[0].split('/')[-1]
        workflow = self._session.query(ResourceWorkflow).get(workflow_id)
        # find the scenario
        processing_step = workflow.get_step_by_name('Select a Scenario')
        scenario = processing_step.get_parameter('form-values')['scenarios'][0]
        scenario_id = scenario.split(':')[1]
        scenario = None
        for _scenario in self._resource.scenarios:
            if str(_scenario.id) == scenario_id:
                scenario = _scenario
        if not scenario:
            raise RuntimeError(f"Scenario with id {scenario_id} not found.")
        # find the TIN dataset id used in the scenario
        tin_dataset = scenario.input_file.get_value('INPUTDATAFILE')
        target_tin_dataset_id = str(tin_dataset.resource_id)
        # filter metis datasets for the TIN dataset
        dataset_options = [
            f'{dataset.name}:{dataset.id}'
            for dataset in self._resource.datasets if dataset.dataset_type is DatasetTypes.TRIBS_METIS
        ]
        filtered_dataset_options = []
        for dataset_option in dataset_options:
            _name, id = dataset_option.split(':')
            dataset = self._session.query(Dataset).get(id)
            tin_dataset_attr = dataset.get_attribute('TIN Dataset')
            if tin_dataset_attr:
                tin_dataset_id = tin_dataset_attr.get('id')
                if tin_dataset_id == target_tin_dataset_id:
                    filtered_dataset_options.append(dataset_option)

        self.param.add_parameter(
            'parallel_partitioning_dataset',
            param.Selector(
                label='Parallel Partitioning Dataset',
                doc='Select a parallel partitioning dataset.',
                objects=filtered_dataset_options,
                check_on_set=True,
                allow_None=False,
                precedence=1
            )
        )
