from pathlib import Path

from ..utilities import safe_str, get_condor_env

REQUEST_CPUS_PER_JOB = 1
JOB_EXECUTABLES_DIR = Path(__file__).parent / 'job_executables'


def build_jobs_callback(condor_workflow):
    """
    Define the Condor Jobs for the run step.

    Returns:
        list<dicts>: Condor Job dicts, one for each job.
    """
    condor_env = get_condor_env()

    jobs = []
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
