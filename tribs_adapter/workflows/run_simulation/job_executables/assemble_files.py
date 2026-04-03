#!/opt/tethys-python
"""
********************************************************************************
* Name: assemble_files.py
* Author: nswain
* Created On: December 28, 2023
* Copyright: (c) Aquaveo 2023
********************************************************************************
"""
import os
import re
import shutil
import tempfile
from datetime import datetime
import pandas as pd

from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tribs_adapter.io.input_file import FileDatabasePathCollection
from tribs_adapter.resources import Dataset
from tribs_adapter.workflows.utilities import safe_str


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

    def _clean_up_sdf_files(file_directory):
        """Clean up paths to mdf weather and rainfall files in sdf station files.

        Arguments:
            file_directory (str): The root directory containing the files.
        """
        for root, _, files in os.walk(file_directory):
            for file in files:
                if file.endswith(".sdf"):
                    # Read in the sdf file
                    with open(os.path.join(root, file), 'r') as f:
                        filedata = f.read()
                    matches = re.findall(r'(\ .*?\.mdf+)', filedata)
                    prefix = ''
                    if root.endswith('Weather'):
                        prefix = 'Weather'
                    elif root.endswith('Rain'):
                        prefix = 'Rain'
                    for match in matches:
                        last_index = match.rfind('/')
                        replacement = ''
                        if prefix:
                            if last_index != -1:
                                # Old path had a leading slash
                                replacement = ' ' + prefix + match[last_index:]
                            else:
                                # Old path didn't have a leading slash
                                replacement = ' ' + prefix + '/' + match[1:]
                            if replacement:
                                # Replace the old path with the new one
                                filedata = filedata.replace(match, replacement)
                    # Replace the sdf file
                    with open(os.path.join(root, file), 'w') as f:
                        f.write(filedata)

    def _update_scenario_startdate_and_runtime(session, scenario):
        """Updates the STARTDATE and RUNTIME parameter in the scenario input file
        based on the start/end date of GAUGESTATIONS and HYDROMETSTATIONS datasets.

        Args:
            scenario (Scenario): The scenario to update.
        """
        def _read_startdate_and_enddate(card):
            """Reads the start date and end date from the given card's mdf files.

            Args:
                card (str): The card name to read from.

            Returns:
                set(datetime, datetime): The start date and end date of the given card's mdf files.
            """

            data = scenario.input_file.get_value(card)
            dataset = session.query(Dataset).get(data.resource_id)
            if not dataset:
                return None

            client = dataset.file_collection_client
            startdate, enddate = None, None
            for file in client.files:
                # Read the mdf files to get the start date
                if file.endswith('.mdf'):
                    df = pd.read_csv(os.path.join(client.path, file), delim_whitespace=True)
                    first_date = datetime(df['Y'][0], df['M'][0], df['D'][0], df['H'][0])
                    lastrow_idx = df.shape[0] - 1
                    last_date = datetime(
                        df['Y'][lastrow_idx], df['M'][lastrow_idx], df['D'][lastrow_idx], df['H'][lastrow_idx]
                    )
                    if startdate is None:
                        startdate = first_date
                    elif first_date != startdate:
                        raise ValueError(f"ERROR: Inconsistent start dates found within the {card} dataset files.")
                    if enddate is None:
                        enddate = last_date
                    elif last_date != enddate:
                        raise ValueError(f"ERROR: Inconsistent end dates found within the {card} dataset files.")

            if not startdate:
                raise ValueError(f"ERROR: Could not determine start date from {card} dataset files.")

            if not enddate:
                raise ValueError(f"ERROR: Could not determine end date from {card} dataset files.")

            return startdate, enddate

        rain_startdate, rain_enddate = _read_startdate_and_enddate('GAUGESTATIONS')
        weather_startdate, weather_enddate = _read_startdate_and_enddate('HYDROMETSTATIONS')

        if rain_startdate != weather_startdate:
            raise ValueError("ERROR: Start dates for precipitation and weather datasets do not match.")

        scenario.input_file = scenario.input_file.set_value('STARTDATE', rain_startdate)

        rain_duration = (rain_enddate - rain_startdate).total_seconds() / 3600
        weather_duration = (weather_enddate - weather_startdate).total_seconds() / 3600
        runtime = scenario.input_file.get_value('RUNTIME')
        runtime = min(rain_duration, weather_duration, runtime)
        scenario.input_file = scenario.input_file.set_value('RUNTIME', runtime)

        session.commit()

    def _update_scenario_parallel_settings(session, scenario, pp_dataset_id):
        """Modifies the scenario for parallel behind the scenes, adding the graph file and output cards as well.

        Adds the "PARALLELMODE" card if necessary.
        Adds the "GRAPHOPTION" and "GRAPHFILE" if necessary.
        Adds the "OUTFILENAME" and "OUTHYDROFILENAME" if necessary.

        Args:
            session (Session): The db session.
            scenario (Scenario): The scenario being set up to run.
            pp_dataset_id (str): The parallel partitioning dataset id.
        """
        # Force to be parallel mode, and set default for GRAPHOPTION
        scenario.input_file = scenario.input_file.set_value('PARALLELMODE', 1)
        scenario.input_file = scenario.input_file.set_value('GRAPHOPTION', 0)

        # Get the METIS dataset, look for the .reach file, and update GRAPHOPTION and GRAPHFILE if found
        pp_dataset = session.query(Dataset).get(pp_dataset_id)
        if not pp_dataset:
            raise RuntimeError(f"Dataset with id {pp_dataset_id} not found.")
        pp_client = pp_dataset.file_collection_client
        for file in pp_client.files:
            if file.endswith(".reach"):
                scenario.input_file = scenario.input_file.set_value('GRAPHOPTION', 1)
                scenario.input_file = scenario.input_file.set_value('GRAPHFILE', f'Output/Mesh/{file}')

        # Get the output cards, and enter a value
        outfilename = FileDatabasePathCollection(
            file_database_paths=[], path=f'Output/voronoi/{safe_str(scenario.name)}'
        )
        outhydrofilename = FileDatabasePathCollection(
            file_database_paths=[], path=f'Output/hyd/{safe_str(scenario.name)}'
        )
        scenario.input_file = scenario.input_file.set_value('OUTFILENAME', outfilename)
        scenario.input_file = scenario.input_file.set_value('OUTHYDROFILENAME', outhydrofilename)

        # Commit to save any changes
        session.commit()

    # ==================================================================================================================
    print("\n\nRun Assemble Files...\n\n")
    tf_files_dir = tempfile.TemporaryDirectory(prefix='srp_assemble_')
    print(f'Storing files temporarily in:  {tf_files_dir.name}')

    # 1 - Get the available scenarios
    scenario_step = workflow.get_step_by_name("Select a Scenario")
    print('\nGetting available scenarios....\n')
    available_scenarios = resource.scenarios
    print(f'Available scenarios = {available_scenarios}')

    # 2 - Get the entered scenario
    print('\nGettig Scenario to process...\n')
    params = scenario_step.get_parameters()
    entered_scenario = _get_entered_scenario(params, 'scenarios', available_scenarios, 'scenario')
    print(f'Entered scenario = {entered_scenario.name}:  {entered_scenario}')

    # 3 - Modify the scenario STARTDATE, RUNTIME, and parallel settings
    pp_step = workflow.get_step_by_name("Select a Parallel Partitioning Dataset")
    pp_dataset = pp_step.get_parameter('form-values')['parallel_partitioning_dataset']
    pp_dataset_id = pp_dataset.split(':')[1]

    _update_scenario_startdate_and_runtime(resource_db_session, entered_scenario)
    _update_scenario_parallel_settings(resource_db_session, entered_scenario, pp_dataset_id)

    # 4 - Write scenario data
    if entered_scenario:
        entered_scenario.export(tf_files_dir.name)

        # Make the output directories if they don't exist
        if not os.path.exists(os.path.join(tf_files_dir.name, 'Output')):
            os.mkdir(os.path.join(tf_files_dir.name, 'Output'))
        if not os.path.exists(os.path.join(tf_files_dir.name, 'Output', 'voronoi')):
            os.mkdir(os.path.join(tf_files_dir.name, 'Output', 'voronoi'))
        if not os.path.exists(os.path.join(tf_files_dir.name, 'Output', 'hyd')):
            os.mkdir(os.path.join(tf_files_dir.name, 'Output', 'hyd'))
    else:
        msg = 'ERROR:  No scenario found.  Quitting.'
        print(msg)
        raise RuntimeError(msg)

    # 5 - Clean up any SDF files, pointing to MDF files
    print('\nCleaning up tRIBSmodel input files...\n')
    _clean_up_sdf_files(tf_files_dir.name)

    # 6 - Look for some common issues
    # RAINSOURCE:
    rainsource = entered_scenario.input_file.get_value('RAINSOURCE')
    if rainsource in [1, 2]:
        rainfile = entered_scenario.input_file.get_value('RAINFILE')
        if rainfile == '' or rainfile is None:
            raise ValueError("ERROR:  parameter RAINFILE has not been entered.")
        rainextension = entered_scenario.input_file.get_value('RAINSOURCE')
        if rainextension == '' or rainextension is None:
            raise ValueError("ERROR:  parameter RAINEXTENSION has not been entered.")
    # OPTBEDROCK
    optbedrock = entered_scenario.input_file.get_value('OPTBEDROCK')
    if optbedrock == 0:
        depthtobedrock = entered_scenario.input_file.get_value('DEPTHTOBEDROCK')
        if depthtobedrock == '' or depthtobedrock is None:
            raise ValueError("ERROR:  parameter DEPTHTOBEDROCK has not been entered.  Required for OPTBEDROCK = 0")
    elif optbedrock == 1:
        bedrockfile = entered_scenario.input_file.get_value('BEDROCKFILE')
        if bedrockfile == '' or bedrockfile is None:
            raise ValueError("ERROR:  parameter BEDROCKFILE has not been entered.  Required for OPTBEDROCK = 1")
    # OPTMESHINPUT
    optmeshinput = entered_scenario.input_file.get_value('OPTMESHINPUT')
    if optmeshinput == 2:
        pointfilename = entered_scenario.input_file.get_value('POINTFILENAME')
        if pointfilename == '' or pointfilename is None:
            raise ValueError("ERROR:  parameter POINTFILENAME has not been entered.  Required for OPTMESHINPUT = 2.")
    # OPTLANDUSE
    optlanduse = entered_scenario.input_file.get_value('OPTLANDUSE')
    if optlanduse == 1:
        lugrid = entered_scenario.input_file.get_value('LUGRID')
        if lugrid == '' or lugrid is None:
            raise ValueError("ERROR:  parameter LUGRID has not been entered.  Required for OPTLANDUSE = 1.")
    # OPTSOILTYPE
    optsoiltype = entered_scenario.input_file.get_value('OPTSOILTYPE')
    if optsoiltype == 1:
        scgrid = entered_scenario.input_file.get_value('SCGRID')
        if scgrid == '' or scgrid is None:
            raise ValueError("ERROR:  parameter SCGRID has not been entered.  Required for OPTSOILTYPE = 1.")

    # 7 - Zip up files
    print('\nArchiving tRIBS model input files...\n')
    output_archive = shutil.make_archive('tRIBS', 'zip', tf_files_dir.name)
    print(f'\nWrote archive = {output_archive}\n')

    print('\n\nScript assemble_files completed with normal execution.\n\n')
