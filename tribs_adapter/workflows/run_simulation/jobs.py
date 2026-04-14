import os
from pathlib import Path

from ..utilities import safe_str, get_condor_env, get_tribspar_executable_path

REQUEST_CPUS_PER_JOB = 1
JOB_EXECUTABLES_DIR = Path(__file__).parent / 'job_executables'


def preprocess_parallel_partition_dataset_job_callback(condor_workflow):
    """
    Define the Condor Job for the Preprocess METIS Dataset step.

    Returns:
        list<dicts>: Condor Job dicts, one for each job.
    """
    condor_env = get_condor_env()
    resource_workflow = condor_workflow.resource_workflow
    step = resource_workflow.get_step_by_name("Select a Parallel Partitioning Dataset")
    dataset = step.get_parameter('form-values')['parallel_partitioning_dataset']
    dataset_name, dataset_id = dataset.split(':')
    dataset_name = safe_str(dataset_name)

    job_name = 'preprocess_parallel_partitioning_dataset'
    executable = f'{job_name}.py'
    job = {
        'name': job_name,
        'condorpy_template_name': 'vanilla_transfer_files',
        'category': 'generic_job',
        'remote_input_files': [str(JOB_EXECUTABLES_DIR / executable), ],
        'attributes': {
            'executable': executable,
            'arguments': [dataset_name, dataset_id],
            'transfer_input_files': [],
            'transfer_output_files': [],
            'environment': condor_env,
            'request_cpus': REQUEST_CPUS_PER_JOB
        }
    }
    return [job]


def build_run_jobs_callback(condor_workflow):
    """
    Define the Condor Job for the run step.

    Returns:
        list<dicts>: Condor Job dicts, one for each job.
    """
    condor_env = get_condor_env()
    resource_workflow = condor_workflow.resource_workflow
    job_executables_dir = Path(__file__).parent / 'job_executables'
    tRIBSpar_path = str(get_tribspar_executable_path())
    num_procs = resource_workflow.get_attribute('preprocess_parallel_partition_output').get('num_procs')
    machine_count = int(num_procs / 8) if not num_procs % 8 else int(num_procs / 8) + 1

    assemble_job = {
        'name': 'assemble_files',
        'condorpy_template_name': 'vanilla_transfer_files',
        'remote_input_files': [os.path.join(job_executables_dir, 'assemble_files.py'), ],
        'attributes': {
            'executable': 'assemble_files.py',
            'transfer_output_files': ['tRIBS.zip'],
            'environment': condor_env,
            'request_cpus': REQUEST_CPUS_PER_JOB
        },
    }

    run_job = {
        'name': 'run_tribs',
        'condorpy_template_name': 'vanilla_transfer_files',
        'remote_input_files': [
            os.path.join(job_executables_dir, 'run_tribs.py'),
            tRIBSpar_path,
        ],
        'attributes': {
            'executable': 'run_tribs.py',
            'transfer_input_files': ['../assemble_files/tRIBS.zip', '../tRIBSpar'],
            'transfer_output_files': [
                # 'tribs_files',  # Uncomment to leave behind unzipped tRIBS input files for debugging
            ],
            'environment': condor_env,
            'request_cpus': num_procs,
            'universe': 'parallel',
            'machine_count': machine_count,
            'should_transfer_files': 'YES',
            'transfer_executable': 'TRUE',
            'when_to_transfer_output': 'ON_EXIT_OR_EVICT',
            # TODO run tribsPar as executable, and add pre-script and post-script
        },
        'parents': [assemble_job['name']],
    }

    # Add to workflow jobs
    return [assemble_job, run_job]


def build_jobs_callback(condor_workflow):
    """
    Define the Condor Jobs for the run step.

    Returns:
        list<dicts>: Condor Job dicts, one for each job.
    """
    jobs = []
    condor_env = get_condor_env()
    resource_workflow = condor_workflow.resource_workflow

    # Get the selected scenarios
    points_step = resource_workflow.get_step_by_name('Generic Spatial Input Step')
    points_geometry = points_step.get_parameter('geometry')

    post_process_tif = []
    post_process_input_files = []
    post_process_parents = []

    # Create one job per point
    for idx, point in enumerate(points_geometry.get('features', [])):
        # Set up the job for the generic job
        executable = 'run_generic_job.py'
        point_name = safe_str(point.get('properties', {}).get('point_name', f'point_{idx + 1}'))
        job_name = f'run_{point_name}'
        output_filename = f'{job_name}_out.json'

        job = {
            'name': job_name,
            'condorpy_template_name': 'vanilla_transfer_files',
            'category': 'generic_job',
            'remote_input_files': [str(JOB_EXECUTABLES_DIR / executable), ],
            'attributes': {
                'executable': executable,
                'arguments': [point_name, idx, output_filename],
                'transfer_input_files': [f'../{executable}', ],
                'transfer_output_files': [output_filename, ],
                'environment': condor_env,
                'request_cpus': REQUEST_CPUS_PER_JOB
            }
        }

        # Add output file as input to post processing job
        post_process_tif.append(f'../{job_name}/{output_filename}')
        post_process_input_files.append(output_filename)

        # Add job as parent to post processing job
        post_process_parents.append(job['name'])

        # Add to workflow jobs
        jobs.append(job)

    # Setup post processing job
    post_process_executable = 'run_post_process.py'
    post_process_job = {
        'name': 'post_processing',
        'condorpy_template_name': 'vanilla_transfer_files',
        'remote_input_files': [str(JOB_EXECUTABLES_DIR / post_process_executable), ],
        'attributes': {
            'executable': post_process_executable,
            'arguments': [','.join(post_process_input_files)],
            'transfer_input_files': post_process_tif,
            'transfer_output_files': [],
            'request_cpus': REQUEST_CPUS_PER_JOB,
            'environment': condor_env,
        },
        'parents': post_process_parents,
    }
    jobs.append(post_process_job)

    return jobs
