#!/opt/tethys-python
"""
********************************************************************************
* Name: run_tribs.py
* Author: nswain
* Created On: December 28, 2023
* Copyright: (c) Aquaveo 2023
********************************************************************************
"""
import datetime
import fnmatch
import os
import shutil
from subprocess import SubprocessError

from tethys_dataset_services.engines.geoserver_engine import GeoServerSpatialDatasetEngine
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tethysext.atcore.utilities import parse_url
from tribs_adapter.resources import Realization
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from tribs_adapter.workflows.utilities import run_tribs


@workflow_step_job
def main(
    resource_db_session, model_db_session, resource, workflow, step, gs_private_url, gs_public_url, resource_class,
    workflow_class, params_json, params_file, cmd_args, extra_args
):
    def _get_entered_scenario(params, params_key, available, name):
        """Used to get the entered scenario from the form values entered.

        Arguments:
            params (dict):  Parameters from the scenario options step, holding the chosen scenario on the form.
            params_key (str):  Key holding the scenario in the params form values.
            available (list):  List of available scenarios of the type to look up.
            name (str):  Name of the dataset type, used in printing debugging statements.

        Returns:
            The Scenario (if found), else None
        """
        entered_scenario = None
        entered_values = params['form-values']['value'][params_key]
        if entered_values:
            entered_name, entered_id = entered_values[0].rsplit(':', 1)  # Form values are <scenario name>:<scenario id>
            for scenario in available:
                # Check if the dataset name matches the first chosen option
                if scenario.name == entered_name and str(scenario.id) == entered_id:
                    entered_scenario = scenario
        print(f'{name}:\n{entered_scenario}')
        if not entered_scenario:
            # Print an error message if we couldn't find a dataset for this type
            error_str = f'Error finding {name}'
            error_str = error_str if not entered_values else error_str + ' ' + entered_values[0]
            print(error_str)
        return entered_scenario

    # ==================================================================================================================
    print("\n\nRun tRIBS workflow...\n\n")

    # 1 - Set up project dir
    print('Setting up project directory...\n')
    project_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'tribs_files')
    if not os.path.isdir(project_dir):
        print(f'Created project directory {project_dir}\n')
        os.makedirs(project_dir)

    # 2 - Extract tRIBS archive, from transfer_input_files
    found_in = False
    shutil.copy2('tRIBSpar', project_dir)
    tribs_input_file = 'tRIBS.in'  # Default input filename
    if os.path.exists(os.path.join(project_dir, 'tRIBS.in')):
        found_in = True
    print('Extracting tRIBS model files for processing...\n')
    shutil.unpack_archive('tRIBS.zip', project_dir, 'zip')
    print("After unzipping, project directory contains:")
    for root, _, files in os.walk('.'):
        level = root.replace(project_dir, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f'{subindent}{f}')
            if fnmatch.fnmatch(f, "*.in") and not found_in:
                # Use the .in file found (without path)
                tribs_input_file = f
                found_in = True

    # 3 - Run tRIBS on the project
    run_start = datetime.datetime.now()
    print(f'Initializing for running tRIBS at {run_start}')
    p = run_tribs(project_dir, tribs_input_file, tribs_executable='tRIBSpar')  # TODO run tribspar here
    if p.returncode != 0:
        raise SubprocessError(f"Error running tRIBS.  Returned non-zero exit status {p.returncode}.\n{p.stderr}")
    run_end = datetime.datetime.now()
    print(f'Completed at {run_end}')
    print(f'Run duration:  {run_end - run_start}\n')

    # 4 - Create Realization  # TODO put in post_process
    # Get the entered scenario
    print('\nGetting Scenario to add Realization...\n')
    scenario_step = workflow.get_step_by_name("Select a Scenario")
    print('\nGetting available scenarios....\n')
    available_scenarios = resource.scenarios
    print(f'Available scenarios = {available_scenarios}')
    params = scenario_step.get_parameters()

    # Get spatial manager for visualization
    url = parse_url(gs_private_url)
    public_url = parse_url(gs_public_url)
    geoserver_engine = GeoServerSpatialDatasetEngine(
        endpoint=url.endpoint,
        username=url.username,
        password=url.password,
        public_endpoint=public_url.endpoint,
    )
    spatial_manager = TribsSpatialManager(geoserver_engine)

    entered_scenario = _get_entered_scenario(params, 'scenarios', available_scenarios, 'scenario')
    print(f'Entered scenario = {entered_scenario.name}:  {entered_scenario}')
    print('Creating Realization....')

    realization = Realization.new(
        session=resource_db_session,
        name=f'{workflow.name}',
        description=f'For scenario {entered_scenario.name}',
        created_by=resource.created_by,
        scenario=entered_scenario,
        model_root=project_dir,
        spatial_manager=spatial_manager,
    )

    # Update the organizations to be the same as the entered scenario
    # (If you don't do this, users can't view it on the Realizations resource page)
    realization.organizations = entered_scenario.organizations

    print(f'Realization created for workflow {workflow.name}, scenario {entered_scenario.name}.')

    print('\n\nScript run_tribs completed with normal execution.\n\n')
