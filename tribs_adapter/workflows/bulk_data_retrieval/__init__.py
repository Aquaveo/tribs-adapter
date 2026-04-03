from tribs_adapter.app_users import TribsRoles
from ..tribs_workflow import TribsWorkflow
from .jobs import build_jobs_callback
from .attributes import PolygonAttributes


class BulkDataRetrievalWorkflow(TribsWorkflow):
    """
    Bulk data retrieval workflow data model.
    """

    TYPE = "bulk_data_retrieval_workflow"
    DISPLAY_TYPE_SINGULAR = "Bulk Data Retrieval Workflow"
    DISPLAY_TYPE_PLURAL = "Bulk Data Retrieval Workflows"

    __mapper_args__ = {"polymorphic_identity": TYPE}

    @classmethod
    def new(
        cls,
        app,
        name,
        resource_id,
        creator_id,
        geoserver_name,
        map_manager,
        spatial_manager,
        **kwargs,
    ):
        from tethysext.atcore.models.resource_workflow_steps import (SpatialInputRWS, SpatialCondorJobRWS)

        """
        Factor class method that creates a new workflow with steps
        Args:
            app(TethysApp): The TethysApp hosting this workflow (e.g. Agwa).
            name(str): Name for this instance of the workflow.
            resource_id(str|uuid): ID of the resource.
            creator_id(str): Username of the user that created the workflow.
            geoserver_name(str): Name of the SpatialDatasetServiceSetting pointing at the GeoServer to use for steps with MapViews.
            map_manager(MapManagerBase): The MapManager to use for the steps with MapViews.
            spatial_manager(SpatialManager): The SpatialManager to use for the steps with MapViews.
            kwargs: additional arguments to use when configuring workflows.

        Returns:
            ResourceWorkflow: the new workflow.
        """  # noqa:E501
        # Create new workflow instance
        workflow = cls(
            name=name,
            resource_id=resource_id,
            creator_id=creator_id,
            lock_when_finished=False,
        )

        # -------------------------------------------------------------------------------------------------------------
        select_area_input_step = SpatialInputRWS(
            name="Select Area of Interest",
            order=10,
            help="Create a polygon to define the extents of the data retrieval. "
            "The length and the width of the polygon should be greater than 1500 meters.",
            options={
                "shapes": ["polygons", "extents"],
                "singular_name": "Polygon",
                "plural_name": "Polygons",
                "allow_shapefile": True,
                "allow_drawing": True,
                "attributes": PolygonAttributes(),
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN],
        )
        workflow.steps.append(select_area_input_step)

        # -------------------------------------------------------------------------------------------------------------
        retrieve_soil_data_execute_step = SpatialCondorJobRWS(
            name="Download Bulk Soil Data",
            order=20,
            help="Review input and then press the Run button to run the workflow and download the soil data. "
            "Press Next after the execution completes to continue.",
            options={
                "scheduler": app.SCHEDULER_NAME,
                "jobs": build_jobs_callback,
                "working_message": "Please wait for the execution to finish running before proceeding.",
                "error_message": "An error occurred with the run. Please adjust your input and try running again.",
                "pending_message": "Please run the workflow to continue.",
            },
            geoserver_name=geoserver_name,
            map_manager=map_manager,
            spatial_manager=spatial_manager,
            active_roles=[TribsRoles.ORG_USER, TribsRoles.ORG_ADMIN],
        )
        workflow.steps.append(retrieve_soil_data_execute_step)

        return workflow
