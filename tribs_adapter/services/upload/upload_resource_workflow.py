import os
import inspect

from tethysext.atcore.services.resource_condor_workflow import ResourceCondorWorkflow
from tethysext.atcore.services.resource_spatial_manager import ResourceSpatialManager

from tribs_adapter.workflows.utilities import get_condor_env, get_condor_fdb_root


class UploadResourceWorkflow(ResourceCondorWorkflow):
    UPLOAD_VISUALIZATION_LAYER_STATUS_KEY = "create_visualization_layer"

    def __init__(
        self,
        app,
        user,
        workflow_name,
        workspace_path,
        resource_db_url,
        resource,
        scheduler,
        job_manager,
        status_keys=None,
        spatial_manager=None,
        gs_engine=None,
        **kwargs,
    ):
        """
        Constructor.

        Args:
            app (TethysApp): App class for the Tethys app.
            user (auth.User): Django user.
            workflow_name (str): Name of the job.
            workspace_path (str): Path to workspace to be used by job.
            resource_db_url (str): SQLAlchemy url to Resource database.
            resource (Resource): Instance of the Resource.
            scheduler (Scheduler): The condor scheduler for the application
            job_manager (JobManger): The condor job manager for the application.
            status_keys (list): One or more keys of statuses to check to determine resource status. The other jobs must update these statuses to one of the Resource.OK_STATUSES for the resource to be marked as SUCCESS.
            spatial_manager (ResourceSpatialManager): Spatial Manager Class for the Resource.
        """  # noqa: E501
        if status_keys is None:
            status_keys = []

        if (
            not spatial_manager or not inspect.isclass(spatial_manager) or
            not issubclass(spatial_manager, ResourceSpatialManager)
        ):
            raise ValueError("Argument spatial_manager is required and must be a subclass of ResourceSpatialManager.")

        super().__init__(
            app=app,
            user=user,
            workflow_name=workflow_name,
            workspace_path=workspace_path,
            resource_db_url=resource_db_url,
            resource=resource,
            scheduler=scheduler,
            job_manager=job_manager,
            status_keys=status_keys,
            **kwargs,
        )
        self.datastore = spatial_manager.DATASTORE
        self.spatial_manager = (f"{spatial_manager.__module__}.{spatial_manager.__name__}")
        self.condor_fdb_root = get_condor_fdb_root()
        self.gs_engine = gs_engine

    def upload_visualization_layer(self, job_name, status_key):
        from tethys_compute.models import CondorWorkflowJobNode
        """Generate a job that will create a layer in GeoServer from the SpatialResource."""
        job_executables_dir = self.app.get_job_executable_dir()
        upload_visualization_layer = CondorWorkflowJobNode(
            name=job_name,
            workflow=self.workflow,
            condorpy_template_name="vanilla_transfer_files",
            category="geoserver",
            remote_input_files=(
                os.path.join(
                    job_executables_dir,
                    "tribs_resources",
                    "create_visualization_executable.py",
                ),
            ),
            attributes=dict(
                executable="create_visualization_executable.py",
                arguments=(
                    self.datastore,
                    self.resource_id,
                    self.resource_db_url,
                    self.gs_engine.endpoint,
                    self.gs_engine.public_endpoint,
                    self.gs_engine.username,
                    self.gs_engine.password,
                    self.spatial_manager,
                    status_key,
                ),
                environment=get_condor_env(),
            ),
        )
        upload_visualization_layer.save()
        return upload_visualization_layer
