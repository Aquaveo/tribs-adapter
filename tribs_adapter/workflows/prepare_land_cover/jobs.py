from pathlib import Path
from tribs_adapter.workflows.utilities import get_condor_env, safe_str

REQUEST_CPUS_PER_JOB = 1
JOB_EXECUTABLES_DIR = Path(__file__).parent / 'job_executables'


def extract_class_ids_job_callback(condor_workflow):
    """
    Define the Condor Jobs for the run step.

    Returns:
        list<dicts>: Condor Job dicts, one for each job.
    """
    condor_env = get_condor_env()
    resource_workflow = condor_workflow.resource_workflow

    select_datasets_step = resource_workflow.get_step_by_name('Select Datasets')
    lu_dataset = select_datasets_step.get_parameter('form-values').get('lu_dataset')
    lu_dataset_name, lu_dataset_id = lu_dataset.split(':')
    wb_dataset = select_datasets_step.get_parameter('form-values').get('watershed_boundary_dataset')
    wb_dataset_name, wb_dataset_id = wb_dataset.split(':')

    job_name = 'extract_class_ids'
    executable = f'{job_name}.py'
    job = {
        'name': job_name,
        'condorpy_template_name': 'vanilla_transfer_files',
        'category': 'generic_job',
        'remote_input_files': [str(JOB_EXECUTABLES_DIR / executable), ],
        'attributes': {
            'executable': executable,
            'arguments': [safe_str(lu_dataset_name), lu_dataset_id, safe_str(wb_dataset_name), wb_dataset_id],
            'transfer_input_files': [],
            'transfer_output_files': [],
            'environment': condor_env,
            'request_cpus': REQUEST_CPUS_PER_JOB
        }
    }

    return [job]


def generate_tribs_files_job_callback(condor_workflow):
    condor_env = get_condor_env()
    job_name = 'generate_tribs_files'
    executable = f'{job_name}.py'
    job = {
        'name': job_name,
        'condorpy_template_name': 'vanilla_transfer_files',
        'category': 'generic_job',
        'remote_input_files': [str(JOB_EXECUTABLES_DIR / executable), ],
        'attributes': {
            'executable': executable,
            'arguments': '',
            'transfer_input_files': [],
            'transfer_output_files': [],
            'environment': condor_env,
            'request_cpus': REQUEST_CPUS_PER_JOB
        }
    }
    return [job]
