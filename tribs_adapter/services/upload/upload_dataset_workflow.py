from tribs_adapter.services.upload.upload_resource_workflow import UploadResourceWorkflow


class UploadDatasetWorkflow(UploadResourceWorkflow):
    def get_jobs(self):
        """
        Get CondorWorkflowJobNodes and the corresponding status key.

        Returns:
            list: A list of 2 tuples in the format [(CondorWorkflowJobNodes, 'status_key'), ...]
        """
        upload_visualization_layer = self.upload_visualization_layer(
            job_name='upload_dataset_visualization', status_key=self.UPLOAD_VISUALIZATION_LAYER_STATUS_KEY
        )
        return [(upload_visualization_layer, self.UPLOAD_VISUALIZATION_LAYER_STATUS_KEY)]
