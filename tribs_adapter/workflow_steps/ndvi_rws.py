"""
********************************************************************************
* Name: ndvi_rws.py
* Author: sonia
* Created On: Jun 11, 2024
* Copyright: (c) Aquaveo 2024
********************************************************************************
"""
from tethysext.atcore.models.resource_workflow_steps import SpatialResourceWorkflowStep


class NDVIRWS(SpatialResourceWorkflowStep):
    """
    Workflow step used for retrieving simple spatial user input (points, lines, polygons).

    Options:
        shapes(list): The types of shapes to allow. Any combination of 'points', 'lines', 'polygons', and/or 'extents'.
        singular_name(str): Name to use when referring to a single feature in other areas of the user interface (e.g. "Detention Basin"). 
        plural_name(str): Name to use when referring to multiple features in other areas of the user interface (e.g. "Detention Basins").
        allow_shapefile(bool): Allow shapfile upload as spatial input. Defaults to True.
        allow_drawing(bool): Allow manually drawing shapes. Defaults to True.
        snapping_enabled(bool): Enabled snapping when drawing features. Defaults to True.
        snapping_layer(dict): Specify a layer to snap to. Create a 1-dict where the key is the dot-path to the layer attribute to use in comparison  and the value is the value to match (e.g. {'data.layer_id': 10}).
        snapping_options(dict): Supported options include edge, vertex, pixelTolerance. See: https://openlayers.org/en/latest/apidoc/module-ol_interaction_Snap.html
        allow_image(bool): Allow reference image upload as spatial input.  Defaults to False.
    """  # noqa: #501
    CONTROLLER = 'tethysapp.tribs.controllers.workflow_steps.ndvi_mwv.NDVIMWV'
    TYPE = 'ndvi_workflow_step'

    __mapper_args__ = {'polymorphic_identity': TYPE}

    @property
    def default_options(self):
        default_options = super().default_options
        default_options.update({})
        return default_options

    def init_parameters(self, *args, **kwargs):
        """
        Initialize the parameters for this step.

        Returns:
            dict<name:dict<help,value>>: Dictionary of all parameters with their initial value set.
        """
        return {
            'ndvi_threshold': {
                'help': 'NDVI threshold selected by the user.',
                'value': None,
                'required': True,
                'is_tabular': True
            },
        }

    def validate(self):
        """
        Validates parameter values of this this step.

        Returns:
            bool: True if data is valid, else Raise exception.

        Raises:
            ValueError
        """
        # Run super validate method first to perform built-in checks (e.g.: Required)
        super().validate()
        return True
