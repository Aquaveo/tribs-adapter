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
            'max_features': 1,
        })
        return default_options

    def validate(self):
        """
        Validates parameter values of this step, including that all features fall within
        the extent of the input raster (stashed on the step by SelectPointMWV).

        Returns:
            bool: True if data is valid, else Raise exception.

        Raises:
            ValueError
        """
        super().validate()

        raster_extent = self.get_attribute('raster_extent', None)
        if not raster_extent:
            return True

        min_x, min_y, max_x, max_y = raster_extent

        # Allow a small tolerance (1% of each dimension) so edge clicks are not rejected
        tolerance_x = (max_x - min_x) * 0.01
        tolerance_y = (max_y - min_y) * 0.01
        min_x, min_y = min_x - tolerance_x, min_y - tolerance_y
        max_x, max_y = max_x + tolerance_x, max_y + tolerance_y

        geometry = self.get_parameter('geometry') or {}

        for feature in geometry.get('features', []):
            coordinates = feature.get('geometry', {}).get('coordinates', [])
            for x, y in self._iter_coordinates(coordinates):
                if not (min_x <= x <= max_x and min_y <= y <= max_y):
                    singular_name = self.options.get('singular_name', 'Feature').lower()
                    raise ValueError(
                        f'The {singular_name} must be located within the extent of the input raster.'
                    )

        return True

    @classmethod
    def _iter_coordinates(cls, coordinates):
        """
        Yield (x, y) pairs from arbitrarily nested GeoJSON coordinates (Point, LineString, Polygon, Multi*).

        Args:
            coordinates(list): The coordinates member of a GeoJSON geometry.

        Yields:
            tuple: (x, y) coordinate pairs.
        """
        if coordinates and isinstance(coordinates[0], (int, float)):
            yield coordinates[0], coordinates[1]
        else:
            for nested in coordinates:
                yield from cls._iter_coordinates(nested)
