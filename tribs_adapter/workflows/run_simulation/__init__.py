from tribs_adapter.app_users import TribsRoles
from tethysext.atcore.models.resource_workflow_steps import FormInputRWS, SpatialCondorJobRWS

from ..tribs_workflow import TribsWorkflow
from .jobs import build_run_jobs_callback, preprocess_parallel_partition_dataset_job_callback
# from .attributes import PointAttributes


class RunSimulationWorkflow(TribsWorkflow):
    """
    Run simulation workflow data model.
    """
    TYPE = 'run_simulation_workflow'
    DISPLAY_TYPE_SINGULAR = 'Run Simulation Workflow'
    DISPLAY_TYPE_PLURAL = 'Run Simulation Workflows'

    __mapper_args__ = {'polymorphic_identity': TYPE}

    @classmethod
    def new(cls, app, name, resource_id, creator_id, geoserver_name, map_manager, spatial_manager, **kwargs):
        """
        Factor class method that creates a new workflow with steps
        Args:
            app(TethysApp): The TethysApp hosting this workflow (e.g. Agwa).
            name(str): Name for this instance of the workflow.
            resource_id(str|uuid): ID of the resource.
            creator_id(str): Username of the user that created the workflow.
            geoserver_name(str): Name of the SpatialDatasetServiceSetting pointing at the GeoServer to use for steps with MapViews.
            map_manager(MapManagerBase): The MapManager to use for the steps with MapViews.
            spatial_manager(SpatialManager): The SpatialManager to use for the steps with MapViews.
            kwargs: additional arguments to use when configuring workflows.

        Returns:
            ResourceWorkflow: the new workflow.
        """  # noqa:E501

        # Create new workflow instance
        workflow = cls(name=name, resource_id=resource_id, creator_id=creator_id, lock_when_finished=False)

        # -------------------------------------------------------------------------------------------------------------
        param_class = 'tribs_adapter.workflows.run_simulation.attributes.ScenarioOptions'
        scenario_options_step = FormInputRWS(
            name='Select a Scenario',
            order=10,
            help='Select a scenario.',
            options={
                'param_class': param_class,
                'form_title': 'Scenario Options',
                'renderer': 'django'
            }
        )
        workflow.steps.append(scenario_options_step)

        # -------------------------------------------------------------------------------------------------------------
        param_class = 'tribs_adapter.workflows.run_simulation.attributes.ParallelPartitionOptions'
        parallel_partition_options_step = FormInputRWS(
            name='Select a Parallel Partitioning Dataset',
            order=15,
            help='Select a Parallel Partitioning Dataset.',
            options={
                'param_class': param_class,
                'form_title': 'Parallel Partitioning Dataset',
                'renderer': 'django'
            }
        )
        workflow.steps.append(parallel_partition_options_step)

        preprocess_dataset_step = SpatialCondorJobRWS(
            name='Preprocess Parallel Partitioning Dataset',
            order=20,
            help='Review input and then press the Run button to run the workflow. ',
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': preprocess_parallel_partition_dataset_job_callback,
                'working_message': 'Please wait for the execution to finish running before proceeding.',
                'error_message': 'An error occurred with the run. Please adjust your input and try running again.',
                'pending_message': 'Please run the workflow to continue.'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(preprocess_dataset_step)

        # -------------------------------------------------------------------------------------------------------------
        run_step = SpatialCondorJobRWS(
            name='Run tRIBS',
            order=30,
            help='Review input and then press the Run button to run the workflow. ',
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': build_run_jobs_callback,
                'working_message': 'Please wait for the execution to finish running before proceeding.',
                'error_message': 'An error occurred with the run. Please adjust your input and try running again.',
                'pending_message': 'Please run the workflow to continue.'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(run_step)

        return workflow
