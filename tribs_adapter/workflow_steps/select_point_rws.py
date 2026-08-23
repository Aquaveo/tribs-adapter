"""
********************************************************************************
* Name: select_point_rws.py
* Author: Yue Sun
* Created On: Aug 20, 2026
* Copyright: (c) Aquaveo 2026
********************************************************************************
"""

import param
from tethysext.atcore.models.resource_workflow_steps import SpatialInputRWS


class PointAttributes(param.Parameterized):
    point_name = param.String(
        label="Name",
        doc="Name of point that will be used to reference it in results.",
        allow_None=False,  #: Required
    )


class SelectPointRWS(SpatialInputRWS):
    """
    Workflow step used for selecting a point on the map in Delineate Hydrologic Features From Point workflow.

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
    CONTROLLER = 'tethysapp.tribs.controllers.workflow_steps.select_point_mwv.SelectPointMWV'
    TYPE = 'select_point_workflow_step'

    __mapper_args__ = {'polymorphic_identity': TYPE}

    @property
    def default_options(self):
        default_options = super().default_options
        default_options.update({
            'shapes': ['points'],
            'singular_name': 'Point',
            'plural_name': 'Points',
            'allow_shapefile': True,
            'allow_drawing': True,
            'attributes': PointAttributes(),
        })
        return default_options
