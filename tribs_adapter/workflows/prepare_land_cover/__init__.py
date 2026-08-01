from tribs_adapter.app_users import TribsRoles
from tethysext.atcore.models.resource_workflow_steps import SpatialCondorJobRWS, FormInputRWS, TableInputRWS
from tribs_adapter.workflows.tribs_workflow import TribsWorkflow
from .jobs import extract_class_ids_job_callback, generate_tribs_files_job_callback
from .helpers import read_tree_class_to_df


class PrepareLandCoverWorkflow(TribsWorkflow):
    """
    Prepare land cover workflow data model.
    """
    TYPE = 'prepare_land_cover_workflow'
    DISPLAY_TYPE_SINGULAR = 'Prepare Land Cover Workflow'
    DISPLAY_TYPE_PLURAL = 'Prepare Land Cover Workflows'

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

        # Land Use Workflow Steps:
        # 1. Select Datasets - FormInputRWS
        # -------------------------------------------------------------------------------------------------------------
        select_datasets_step = FormInputRWS(
            name='Select Datasets',
            order=10,
            help="Select the land cover datasets to prepare.",
            options={'param_class': 'tribs_adapter.workflows.prepare_land_cover.step_params.DatasetsParam'},
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(select_datasets_step)

        # 2. Validate and Extract Class IDs - SpatialCondorJobRWS - (a-b)
        # -------------------------------------------------------------------------------------------------------------
        extract_class_ids_step = SpatialCondorJobRWS(
            name='Validate and Extract Class IDs',
            order=20,
            help='Review the input and then press the Run button to run the workflow. '
            'Press Next after the execution completes to continue.',
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': extract_class_ids_job_callback,
                'working_message': 'Please wait for the execution to finish running before proceeding.',
                'error_message': 'An error occurred with the run. Please adjust your input and try running again.',
                'pending_message': 'Please run the workflow to continue.'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(extract_class_ids_step)

        # 3. Enter Land Use Parameters - TableInputRW
        # Free Throughfall Coefficient (P), Canopy Field Capacity (S), Drainage Coefficient (K),
        # Drainage Exponent (b2), Albedo (Al), Vegetation Height (h), Optical Transmission Coefficient (Kt),
        # Canopy-Average Stomatal Resistance (Rs), Vegetation Fraction (V), Leaf Area Index (LAI),
        # Stress Threshold for Soil Evaporation (thetas), Stress Threshold for Plant Transpiration (thetat)
        # -------------------------------------------------------------------------------------------------------------
        enter_landuse_params_step = TableInputRWS(
            name='Enter Land Use Parameters',
            order=30,
            help="Enter the parameters for each vegetation type",
            options={
                'dataset_title': 'Land Use Parameters',
                'template_dataset': read_tree_class_to_df,
                'read_only_columns': ['ID'],
                'fixed_rows': True,
                'column_bounds': {
                    'Free Throughfall Coefficient (P)': {
                        'min': 0.01,
                        'max': 1.0
                    },
                    'Canopy Field Capacity (S) (mm)': {
                        'min': 0.01
                    },
                    'Drainage Coefficient (K) (mm/hr)': {
                        'min': 0.01
                    },
                    'Drainage Exponent (b2) (mm/hr)': {
                        'min': 0.01
                    },
                    'Albedo (Al)': {
                        'min': 0.01,
                        'max': 1.0
                    },
                    'Vegetation Height (h) (m)': {
                        'min': 0.01
                    },
                    'Optical Transmission Coefficient (Kt)': {
                        'min': 0.01,
                        'max': 1.0
                    },
                    'Canopy-Average Stomatal Resistance (Rs) (s/m)': {
                        'min': 0.01
                    },
                    'Vegetation Fraction (V)': {
                        'min': 0.01,
                        'max': 1.0
                    },
                    'Leaf Area Index (LAI)': {
                        'min': 0.01
                    },
                    'Stress Threshold for Soil Evaporation (thetas)': {
                        'min': 0.01
                    },
                    'Stress Threshold for Plant Transpiration (thetat)': {
                        'min': 0.01
                    }
                }
            },
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(enter_landuse_params_step)

        # 4. Generate tRIBS Files - SpatialCondorJobRWS
        # .lu file, .ldt file
        # ---------------------------------------------------------------------------------------------------
        generate_tribs_files_step = SpatialCondorJobRWS(
            name='Generate tRIBS Files',
            order=40,
            help='Review the input and then press the Run button to run the workflow. '
            'Press Next after the execution completes to continue.',
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': generate_tribs_files_job_callback,
                'working_message': 'Please wait for the execution to finish running before proceeding.',
                'error_message': 'An error occurred with the run. Please adjust your input and try running again.',
                'pending_message': 'Please run the workflow to continue.'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(generate_tribs_files_step)

        return workflow
