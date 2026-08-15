from tribs_adapter.workflows.tribs_workflow import TribsWorkflow
from tethysext.atcore.models.resource_workflow_steps import (
    FormInputRWS, SpatialCondorJobRWS, ResultsResourceWorkflowStep
)
from tethysext.atcore.models.resource_workflow_results import (
    PlotWorkflowResult, SpatialWorkflowResult, ReportWorkflowResult
)
from tribs_adapter.app_users import TribsRoles

from .jobs import preprocess_tin_job_callback, run_metis_job_callback


class PrepareParallelizationWorkflow(TribsWorkflow):
    """
    Prepare parallelization workflow.
    """
    TYPE = 'prepare_parallelization_workflow'
    DISPLAY_TYPE_SINGULAR = 'Prepare Parallelization Workflow'
    DISPLAY_TYPE_PLURAL = 'Prepare Parallelization Workflows'
    REQUEST_CPUS_PER_JOB = 1

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

        # Workflow Steps:
        # 1. Select a TIN Dataset
        select_tin_step = FormInputRWS(
            name='Select Datasets',
            order=10,
            help="Select a TIN dataset and a Stream dataset (optional).",
            options={'param_class': 'prepare_parallelization.step_params.DatasetParam'},
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(select_tin_step)

        # 2. Check how many reaches are in the TIN dataset
        proprocess_tin_step = SpatialCondorJobRWS(
            name='Preprocess TIN',
            order=20,
            help='Review the input and then press the Run button to preprocess the TIN dataset. '
            'Press Next after the execution completes to continue.',
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': preprocess_tin_job_callback,
                'working_message': 'Please wait for the execution to finish running before proceeding.',
                'error_message': 'An error occurred with the run. Please adjust your input and try running again.',
                'pending_message': 'Please run the workflow to continue.'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(proprocess_tin_step)

        # 3. Model Setup - FormInputRWS
        # Select the partition mode (SF, SSF), num of processors (min 1?, max 100?)
        # -------------------------------------------------------------------------------------------------------------
        model_setup_step = FormInputRWS(
            name='Configure Parallelization Options',
            order=30,
            help="Choose a parallelization approach and the number of processors to use in the parallel run of tRIBS.",
            options={'param_class': 'prepare_parallelization.step_params.ModelSetupParam'},
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(model_setup_step)

        # 4. Run METIS - SpatialCondorJobRWS
        # -------------------------------------------------------------------------------------------------------------
        run_metis_step = SpatialCondorJobRWS(
            name='Run METIS',
            order=40,
            help='Review the input and then press the Run button to run METIS. '
            'Press Next after the execution completes to continue.',
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': run_metis_job_callback,
                'working_message': 'Please wait for the execution to finish running before proceeding.',
                'error_message': 'An error occurred with the run. Please adjust your input and try running again.',
                'pending_message': 'Please run the workflow to continue.'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(run_metis_step)

        # 5. Visualization - ResourceWorkflowResult
        # Show the partition graph and plots (Np vs. p) as a result
        # Save the visualization as a new dataset
        # -------------------------------------------------------------------------------------------------------------
        visualization_step = ResultsResourceWorkflowStep(
            name='Partitioning Results',
            order=50,
            help='Evaluate the efficiency of the parallel partitioning.',
            options={},
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(visualization_step)

        run_metis_step.result = visualization_step

        plot_view = PlotWorkflowResult(
            name='Points per Processor Graph',
            codename='output_plot',
            description='Plot of the number of processing nodes assigned to each processor.',
            order=10,
            options={
                'plot_type': 'bar',
                'axis_labels': ['Processor ID', 'the Number of Points']
            },
        )

        map_view = SpatialWorkflowResult(
            name='Partitioning Map',
            codename='output_map',
            description='Map of the tRIBS Voronoi elements symbolized by the processor to which they are assigned.',
            order=20,
            options={
                'layer_group_title': 'Partitioning Map',
                'layer_group_control': 'checkbox'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager
        )

        summary_view = ReportWorkflowResult(
            name='Summary',
            codename='summary',
            description='Summary of all parallel partitioning results.',
            order=30,
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager
        )

        visualization_step.results.extend([plot_view, map_view, summary_view])

        return workflow
