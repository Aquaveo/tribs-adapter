#!/opt/tethys-python
"""
********************************************************************************
* Name: preprocess_tin_dataset.py
* Author: Yue Sun
* Created On: Jul 24, 2025
* Copyright: (c) Aquaveo 2025
********************************************************************************
"""
import os
import tempfile

from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job
from tribs_adapter.resources.dataset import Dataset


@workflow_step_job
def main(
    resource_db_session,
    model_db_session,
    resource,
    workflow,
    step,
    gs_private_url,
    gs_public_url,
    resource_class,
    workflow_class,
    params_json,
    params_file,
    cmd_args,
    extra_args,
):
    if extra_args and len(extra_args) >= 2:
        tin_dataset_name, tin_dataset_id = extra_args[0], extra_args[1]
        tin_dataset = resource_db_session.query(Dataset).get(tin_dataset_id)
        if not tin_dataset:
            raise RuntimeError(f"Dataset with id {tin_dataset_id} not found.")
        tin_client = tin_dataset.file_collection_client
        tin_temp_dir = tempfile.TemporaryDirectory(dir=os.getcwd(), prefix="tin_")
        reach_path = None
        for file in tin_client.files:
            tin_client.export_item(item=file, target=tin_temp_dir.name)
            if file.endswith(".reach"):
                reach_path = os.path.join(tin_temp_dir.name, file)

        num_reach = 0
        with open(reach_path, 'r') as file:
            num_reach = sum(1 for _ in file)

        workflow.set_attribute('preprocess_tin_output', {'num_reach': num_reach})

        print(f"Finish preprocessing the TIN dataset {tin_dataset_name}")
