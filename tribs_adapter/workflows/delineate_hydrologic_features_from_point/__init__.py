"""
********************************************************************************
* Name: delineate_hydrologic_features_from_point_workflow
* Author: Yue Sun
* Created On: August 15, 2026
* Copyright: (c) Aquaveo 2026
********************************************************************************
"""
import os

from tribs_adapter.app_users import TribsRoles
from tethysext.atcore.models.resource_workflow_steps import SpatialCondorJobRWS
from tethysext.atcore.models.resource_workflow_steps.xms_tool_rws import XMSToolRWS
from tribs_adapter.workflows.tribs_workflow import TribsWorkflow
from tribs_adapter.workflows.utilities import get_condor_env
from tribs_adapter.workflow_steps.select_point_rws import SelectPointRWS


def validate_threshold_area(value):
    if float(value) <= 0:
        raise ValueError('Threshold area must be a positive number in square kilometers.')


class DelineateHydrologicFeaturesFromPointWorkflow(TribsWorkflow):
    """
    Data model for storing information about delineate hydrologic features from point workflows.
    """
    TYPE = 'delineate_hydrologic_features_from_point_workflow'
    DISPLAY_TYPE_SINGULAR = 'Delineate Hydrologic Features From Point Workflow'
    DISPLAY_TYPE_PLURAL = 'Delineate Hydrologic Features From Point Workflows'
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
        condor_env = get_condor_env()

        # Create new workflow instance
        workflow = cls(name=name, resource_id=resource_id, creator_id=creator_id, lock_when_finished=True)

        # Setup Condor Step
        job_executables_dir = os.path.join(os.path.dirname(__file__), 'job_executables')

        xmstool_step = XMSToolRWS(
            name='tRIBS Watershed from Pour Point',
            order=10,
            help='Run the tRIBS Watershed from Pour Point tool from xmsool',
            options={
                'xmstool_class': 'tribs_adapter.workflows.delineate_hydrologic_features_from_point'
                                 '.tools.WatershedFromPourPointWebTool',
                'arg_mapping': {
                    'input_raster': {
                        'resource_attr': 'datasets',
                        'filter_attr': 'dataset_type',
                        'valid_values': [
                            'RASTER_DISC_ASCII', 'RASTER_CONT_ASCII', 'RASTER_DISC_GEOTIFF', 'RASTER_CONT_GEOTIFF'
                        ],
                        'name_attr': 'name',
                    },
                },
                'form_title': 'tRIBS Watershed from Pour Point',
                'renderer': 'django',
                'validators': {
                    'threshold_area_sq_km': validate_threshold_area
                }
            }
        )
        workflow.steps.append(xmstool_step)

        select_point_step = SelectPointRWS(
            name="Select a Pour Point",
            order=20,
            help="Choose a pourpoint to delineate the watershed."
            "The point should be located within the watershed of interest.",
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN],
        )
        workflow.steps.append(select_point_step)

        xmstool_job = {
            'name': 'run_tool',
            'condorpy_template_name': 'vanilla_transfer_files',
            'remote_input_files': [os.path.join(job_executables_dir, 'run_tool.py'), ],
            'attributes': {
                'executable': 'run_tool.py',
                'transfer_output_files': [],
                'transfer_input_files': [],
                'environment': condor_env,
                'request_cpus': cls.REQUEST_CPUS_PER_JOB
            },
            'parents': [],
        }

        generate_datasets_step = SpatialCondorJobRWS(
            name='Run Tool',
            order=30,
            help='Review input and then press the Run button to run the model. '
            'Press Next after the model execution completes to continue.',
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': [xmstool_job],
                'working_message': 'Please wait for the tool to finish running before proceeding.',
                'error_message':
                    'An error occurred with the run. Please adjust your input and try running '
                    'the tool again.',
                'pending_message': 'Please run the tool to continue.'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(generate_datasets_step)

        return workflow
