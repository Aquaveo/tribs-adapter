from pathlib import Path
from tribs_adapter.workflows.utilities import get_condor_env, safe_str

REQUEST_CPUS_PER_JOB = 1
JOB_EXECUTABLES_DIR = Path(__file__).parent / 'job_executables'


def preprocess_tin_job_callback(condor_workflow):
    """
    Define the Condor Jobs for the Preprocess TIN step.

    Returns:
        list<dicts>: Condor Job dicts, one for each job.
    """

    condor_env = get_condor_env()
    resource_workflow = condor_workflow.resource_workflow
    select_tin_step = resource_workflow.get_step_by_name('Select Datasets')
    tin_dataset = select_tin_step.get_parameter('form-values').get('tin_dataset')
    tin_dataset_name, tin_dataset_id = tin_dataset.split(':')
    tin_dataset_name = safe_str(tin_dataset_name)

    job_name = 'preprocess_tin_dataset'
    executable = f'{job_name}.py'
    job = {
        'name': job_name,
        'condorpy_template_name': 'vanilla_transfer_files',
        'category': 'generic_job',
        'remote_input_files': [str(JOB_EXECUTABLES_DIR / executable), ],
        'attributes': {
            'executable': executable,
            'arguments': [tin_dataset_name, tin_dataset_id],
            'transfer_input_files': [],
            'transfer_output_files': [],
            'environment': condor_env,
            'request_cpus': REQUEST_CPUS_PER_JOB
        }
    }
    return [job]


def run_metis_job_callback(condor_workflow):
    """
    Define the Condor Jobs for the RUN METIS step.

    Returns:
        list<dicts>: Condor Job dicts, one for each job.
    """

    condor_env = get_condor_env()
    resource_workflow = condor_workflow.resource_workflow

    select_tin_step = resource_workflow.get_step_by_name('Select Datasets')
    tin_dataset = select_tin_step.get_parameter('form-values').get('tin_dataset')
    tin_dataset_name, tin_dataset_id = tin_dataset.split(':')
    tin_dataset_name = tin_dataset_name.replace(' ', '_')
    stream_dataset = select_tin_step.get_parameter('form-values').get('stream_dataset')
    if stream_dataset == 'None':
        stream_dataset_name, stream_dataset_id = None, None
    else:
        stream_dataset_name, stream_dataset_id = stream_dataset.split(':')
        stream_dataset_name = stream_dataset_name.replace(' ', '_')

    config_step = resource_workflow.get_step_by_name('Configure Parallelization Options')
    config_step_params = config_step.get_parameter('form-values')
    mode = config_step_params.get('mode')
    num_processor = config_step_params.get('num_processor')

    run_metis_job_name = 'run_metis'
    run_metis_executable = f'{run_metis_job_name}.py'
    run_metis_job = {
        'name': run_metis_job_name,
        'condorpy_template_name': 'vanilla_transfer_files',
        'category': 'generic_job',
        'remote_input_files': [str(JOB_EXECUTABLES_DIR / run_metis_executable), ],
        'attributes': {
            'executable': run_metis_executable,
            'arguments': [tin_dataset_name, tin_dataset_id, mode, num_processor],
            'transfer_input_files': [],
            'transfer_output_files': [],
            'environment': condor_env,
            'request_cpus': REQUEST_CPUS_PER_JOB
        }
    }

    post_process_job_name = 'post_process'
    post_process_executable = f'{post_process_job_name}.py'
    post_process_job = {
        'name': post_process_job_name,
        'condorpy_template_name': 'vanilla_transfer_files',
        'category': 'generic_job',
        'remote_input_files': [str(JOB_EXECUTABLES_DIR / post_process_executable), ],
        'attributes': {
            'executable': post_process_executable,
            'arguments': [stream_dataset_name, stream_dataset_id],
            'transfer_input_files': [],
            'transfer_output_files': [],
            'environment': condor_env,
            'request_cpus': REQUEST_CPUS_PER_JOB
        },
        'parents': [run_metis_job['name']]
    }

    return [run_metis_job, post_process_job]
