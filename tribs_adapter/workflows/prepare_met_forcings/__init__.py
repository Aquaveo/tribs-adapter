import datetime
import os
from pathlib import Path

from tribs_adapter.app_users import TribsRoles
from tethysext.atcore.models.resource_workflow_steps import FormInputRWS, SpatialCondorJobRWS, SpatialInputRWS

from ..utilities import get_condor_env
from ..tribs_workflow import TribsWorkflow
from .jobs import REQUEST_CPUS_PER_JOB


def parse_iso_datetime(value: str) -> datetime.datetime:
    """
    Parse a date string in ISO format, adding a 'T00' if no time,
    and zero-padding month/day if needed.
    """
    if 'T' in value:
        date, time = value.split('T')
    else:
        date, time = value, '00'

    parts = date.split('-')
    if len(parts) != 3:
        raise ValueError('Date must be in YYYY-MM-DD format (month/day can be 1 or 2 digits)')
    year, month, day = parts
    month = month.zfill(2)
    day = day.zfill(2)

    iso_str = f'{year}-{month}-{day}T{time}'
    return datetime.datetime.fromisoformat(iso_str)


def validate_nldas_dates(start_value, end_value):
    start = parse_iso_datetime(start_value)
    end = parse_iso_datetime(end_value)

    min_start = datetime.datetime(1979, 1, 1, 13)
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    if start < min_start:
        raise ValueError("Start time must be greater than 1979-01-01T13")

    if end > yesterday:
        raise ValueError("End time must be yesterday or earlier")

    if start >= end:
        raise ValueError("Start time must be earlier than end time")


class PrepareMetWorkflow(TribsWorkflow):
    """
    Prepare meteorological forcings workflow data model.
    """
    TYPE = 'prepare_met_workflow'
    DISPLAY_TYPE_SINGULAR = 'Prepare Meteorological Forcings Workflow'
    DISPLAY_TYPE_PLURAL = 'Prepare Meteorological Forcings Workflows'

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
        workflow = cls(name=name, resource_id=resource_id, creator_id=creator_id, lock_when_finished=False)
        job_executables_dir = Path(__file__).parent / 'job_executables'

        # -------------------------------------------------------------------------------------------------------------
        tin_options_step = SpatialInputRWS(
            name='Select Watershed',
            order=10,
            help='Use the Polygon or Box tool to draw watershed boundaries or import a shapefile.',
            options={
                'shapes': ['polygons', 'extents'],
                'singular_name': 'Watershed',
                'plural_name': 'Watersheds',
                'allow_shapefile': True,
                'allow_drawing': True
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(tin_options_step)

        # -------------------------------------------------------------------------------------------------------------
        param_class = 'tribs_adapter.workflows.prepare_met_forcings.nldas_timestep_options.NldasTimestepOptions'
        nldas_options_step = FormInputRWS(
            name='Select NLDAS Timestep Options',
            order=15,
            help='Select options for NLDAS.',
            options={
                'param_class': param_class,
                'form_title': 'NLDAS Timestep Options',
                'renderer': 'django',
                'validators': {('nldas_start_time', 'nldas_end_time'): validate_nldas_dates}
            },
        )
        workflow.steps.append(nldas_options_step)

        # -------------------------------------------------------------------------------------------------------------
        nldas_job = {
            'name': 'nldas_job',
            'condorpy_template_name': 'vanilla_transfer_files',
            'remote_input_files': [os.path.join(job_executables_dir, 'run_nldas.py'), ],
            'attributes': {
                'executable': 'run_nldas.py',
                'transfer_output_files': [],
                'environment': condor_env,
                'request_cpus': REQUEST_CPUS_PER_JOB
            },
        }

        # -------------------------------------------------------------------------------------------------------------
        nldas_execute_step = SpatialCondorJobRWS(
            name='NLDAS Step',
            order=20,
            help='Review input and then press the Run button to run the workflow. ',
            options={
                'scheduler': app.SCHEDULER_NAME,
                'jobs': [nldas_job],
                'working_message': 'Please wait for the execution to finish running before proceeding.',
                'error_message': 'An error occurred with the run. Please adjust your input and try running again.',
                'pending_message': 'Please run the workflow to continue.'
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN]
        )
        workflow.steps.append(nldas_execute_step)

        return workflow
