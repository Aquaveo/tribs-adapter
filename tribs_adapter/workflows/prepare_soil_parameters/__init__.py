from tribs_adapter.app_users import TribsRoles
from tethysext.atcore.models.resource_workflow_steps import SpatialCondorJobRWS, FormInputRWS, TableInputRWS
from tribs_adapter.workflows.prepare_soil_parameters.read_write_soil_file import read_soil_data_to_df

from ..tribs_workflow import TribsWorkflow
from .jobs import build_rosetta3_jobs_callback, build_generate_tribs_files_callback


class PrepareSoilsWorkflow(TribsWorkflow):
    """
    Prepare soil parameters workflow data model.
    """
    TYPE = 'prepare_soils_workflow'
    DISPLAY_TYPE_SINGULAR = 'Prepare Soils Workflow'
    DISPLAY_TYPE_PLURAL = 'Prepare Soils Workflows'

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

        #     Soil ATCore Workflow Steps:
        # 1. Select Soil Dataset(s) - FormInputRWS
        # -------------------------------------------------------------------------------------------------------------
        select_soil_dataset_input_step = FormInputRWS(
            name='Select Soil Dataset(s)',
            order=10,
            help="1. Select the soil datasets to prepare. Hold shift to select multiple datasets. "
            "2. Enter the base of the output dataset name.",
            options={'param_class': 'tribs_adapter.workflows.prepare_soil_parameters.step_params.SoilDatasetsParam'},
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(select_soil_dataset_input_step)

        # 2. Run Rosetta3 - SpatialCondorJobRWS ( b & c.i-v)
        # -------------------------------------------------------------------------------------------------------------
        run_rosetta3 = SpatialCondorJobRWS(
            name='Run Rosetta3',
            order=20,
            help='Review input and then press the Run button to run the workflow to process the soil data using '
            'Rosetta3 tools. Press Next after the execution completes to continue.',
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': build_rosetta3_jobs_callback,
                'working_message': 'Please wait for the execution to finish running before proceeding.',
                'error_message': 'An error occurred with the run. Please adjust your input and try running again.',
                'pending_message': 'Please run the workflow to continue.'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(run_rosetta3)

        # 3. Enter Texture Parameters - TableInputRWS (needs to be created) (c.v)
        #  Add basically the same widget from 'Define Pre Basin Hydrographs' from AGWA GSSHA or stream gauges
        # 'return periods tab' (latter is probably closer)
        #  Create the basic class in ATCore
        #  Pass in number of columns, and rows.
        # -------------------------------------------------------------------------------------------------------------
        # Enter Saturated Anisotropy Ratio (As), Unsaturated Anisotropy Ratio (Au), Porosity (n),
        # Volumetric Heat Conductivity - J/msK (ks), Soil Head Capacity - J/m3K (Cs)
        enter_texture_parameters = TableInputRWS(
            name='Enter Texture Parameters',
            order=30,
            help="Enter the following parameters for each soil texture.",
            options={
                'dataset_title': 'Soil Texture Parameters',
                'template_dataset': read_soil_data_to_df,
                'read_only_columns': ['Soil Texture Class'],
                'fixed_rows': True
            },
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(enter_texture_parameters)

        # 4. Generate tRIBS Files - SpatialCondorJobRWS - ascii (soi) & sdt
        # -------------------------------------------------------------------------------------------------------------
        generate_tribs_files = SpatialCondorJobRWS(
            name='Save Soil Parameters to Soil Table File',
            order=40,
            help='Execute the update script. '
            'Press Next after the execution completes to continue.',
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': build_generate_tribs_files_callback,
                'working_message': 'Please wait for the execution to finish running before proceeding.',
                'error_message': 'An error occurred with the run. Please adjust your input and try running again.',
                'pending_message': 'Please run the workflow to continue.'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(generate_tribs_files)

        return workflow
