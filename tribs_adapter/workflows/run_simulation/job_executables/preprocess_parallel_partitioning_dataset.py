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
import pandas as pd

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
        dataset_name, dataset_id = extra_args[0], extra_args[1]
        dataset = resource_db_session.query(Dataset).get(dataset_id)
        if not dataset:
            raise RuntimeError(f"Dataset with id {dataset_id} not found.")
        client = dataset.file_collection_client
        temp_dir = tempfile.TemporaryDirectory(dir=os.getcwd(), prefix="pp_")
        reach_filepath = None
        for file in client.files:
            client.export_item(item=file, target=temp_dir.name)
            if file.endswith(".reach"):
                reach_filepath = os.path.join(temp_dir.name, file)
        if not reach_filepath:
            raise RuntimeError(f"There's no .reach file in the dataset with id {dataset_id}")

        df = pd.read_csv(reach_filepath, delimiter=' ', names=['proc_id', 'reach_id'])
        num_procs = int(df['proc_id'].max())
        workflow.set_attribute('preprocess_parallel_partition_output', {'num_procs': num_procs})

        print(f"Finish preprocessing the parallel partitioning dataset {dataset_name}")
