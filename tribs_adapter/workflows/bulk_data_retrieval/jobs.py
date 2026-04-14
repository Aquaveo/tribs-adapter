from pathlib import Path

from ..utilities import safe_str, get_condor_env

REQUEST_CPUS_PER_JOB = 1
JOB_EXECUTABLES_DIR = Path(__file__).parent / "job_executables"


def build_jobs_callback(condor_workflow):
    """
    Define the Condor Jobs for the run step.

    Returns:
        list<dicts>: Condor Job dicts, one for each job.
    """
    jobs = []
    condor_env = get_condor_env()
    resource_workflow = condor_workflow.resource_workflow

    # Get the created polygon
    polygon_step = resource_workflow.get_step_by_name("Select Area of Interest")
    polygon_geometry = polygon_step.get_parameter("geometry")

    # Create one job per point
    for idx, polygon in enumerate(polygon_geometry.get("features", [])):

        # Set up the job for the generic job
        executable = "run_bulk_soil_data_retrieval.py"
        polygon_name = safe_str(polygon.get("properties", {}).get("polygon_name", f"polygon_{idx + 1}"))
        job_name = f"run_bulk_soil_data_retrieval_{polygon_name}"

        job = {
            "name": job_name,
            "condorpy_template_name": "vanilla_transfer_files",
            "category": "generic_job",
            "remote_input_files": [str(JOB_EXECUTABLES_DIR / executable), ],
            "attributes": {
                "executable": executable,
                "arguments": [polygon_name, idx],
                "transfer_input_files": [f"../{executable}", ],
                "transfer_output_files": [],
                "environment": condor_env,
                "request_cpus": REQUEST_CPUS_PER_JOB,
            },
        }

        # Add to workflow jobs
        jobs.append(job)

    return jobs
