"""
Class that will create a dict with czml info for points and polygons and write it out to a czml file.
"""
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List

import numpy as np

import matplotlib

matplotlib.use('Agg')
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


@dataclass
class CzmlPointData:
    """Class to hold data values for a point."""
    location: List[float]
    values: List[float] = field(default_factory=[])
    id: str = None  # ID of the point
    start_time: datetime = None  # Start time of the point
    run_time: int = None  # Run time in hours
    interval: int = None  # Interval in hours
    min_value: float = None  # Minimum value of the data
    max_value: float = None  # Maximum value of the data

    @property
    def end_time(self):
        """Calculate the end time of the point."""
        return self.start_time + timedelta(hours=self.run_time)


@dataclass
class CzmlPolygonData:
    """Class to hold data values for a polygon."""
    locations: List[List[float]]
    values: List[float]
    id: str = None  # ID of the polygon
    start_time: datetime = None  # Start time of the polygon
    run_time: int = None  # Run time in hours
    interval: int = None  # Interval in hours
    min_value: float = None  # Minimum value of the data
    max_value: float = None  # Maximum value of the data

    @property
    def end_time(self):
        """Calculate the end time of the polygon."""
        return self.start_time + timedelta(hours=self.run_time)


class CZMLGenerator:
    def __init__(self, name):
        """Class initializer.

        Args:
            points (iterable): A list of points to be displayed in the czml file.
            polygons (iterable): A list of polygons to be displayed in the czml file.
            start_time (str): The start time of the czml file.
            runtime (str): The runtime of the czml file in hours.
            interval (str): The interval of the time steps in hours.
        """
        self.points = []
        self.point_data_values = []
        self.polygons = []
        self.polygon_data_values = []
        self.name = name
        self._origin = None
        self._extents = None

    def add_point(
        self,
        point: List[float],
        data_values: List[float] = None,
        id: str = None,
        start_time: datetime = None,
        run_time: int = None,
        interval: int = None
    ):
        """Add a point to the czml file.

        Args:
            point (List[float]): A list of the point's coordinates.
            data_values (List[float]): A list of data values to be displayed in the czml file.
        """
        czml_point = CzmlPointData(point, data_values, id, start_time, run_time, interval)
        self.points.append(czml_point)

    def add_polygon(
        self,
        polygon: List[List[float]],
        data_values: List[float] = None,
        id: str = None,
        start_time: datetime = None,
        run_time: int = None,
        interval: int = None
    ):
        """Add a polygon to the czml file.

        Args:
            polygon (List[List[float]]): A list of the polygon's coordinates.
            data_values (List[float]): A list of data values to be displayed in the czml file.
        """
        czml_polygon = CzmlPolygonData(polygon, data_values, id, start_time, run_time, interval)
        self.polygons.append(czml_polygon)

    def write_czml(self, filename, legend=False):
        czml = [{
            "id": "document",
            "name": self.name,
            "version": "1.0",
        }]

        for point in self.points:
            czml.append(self._generate_point_czml(point))

        for polygon in self.polygons:
            czml.append(self._generate_polygon_czml(polygon))

        with open(filename, 'w') as f:
            json.dump(czml, f, indent=4)

        if legend:
            if len(self.points) > 0:
                self.generate_point_legend(filename.replace('.czml', '_point_legend.png'))
            if len(self.polygons) > 0:
                self.generate_polygon_legend(filename.replace('.czml', '_polygon_legend.png'))

    def _generate_point_czml(self, point):
        min_point_value = np.min([np.min(point.values) for point in self.points])
        max_point_value = np.max([np.max(point.values) for point in self.points])
        czml = {
            "id": point.id,
            "position": {
                "cartographicDegrees": list(point.location) + [20]
            },
            "point": {
                "color": {
                    "rgba": [255, 255, 255, 255]
                },
                "outlineColor": {
                    "rgba": [0, 0, 0, 255]
                },
                "outlineWidth": 1,
                "pixelSize": 10,
                "show": True,
                "heightReference": "RELATIVE_TO_GROUND"
            },
        }

        if point.start_time is not None:
            czml["availability"] = f"{self._format_date(point.start_time)}/{self._format_date(point.end_time)}"
            czml["position"]["epoch"] = f"{self._format_date(point.start_time)}"

            if point.values is not None:
                czml["point"]["color"] = [
                    {
                        "interval":
                            f"{self._format_date(point.start_time + timedelta(hours=i*point.interval))}/"
                            f"{self._format_date(point.start_time + timedelta(hours=i*point.interval+point.interval))}",
                        "rgba": color.tolist() + [255]
                    } for i, color in
                    enumerate(self._get_colors_for_values(point.values, min=min_point_value, max=max_point_value))
                ]

        return czml

    def _generate_polygon_czml(self, polygon):
        min_polygon_value = np.min([np.min(polygon.values) for polygon in self.polygons])
        max_polygon_value = np.max([np.max(polygon.values) for polygon in self.polygons])
        czml = {
            "id": polygon.id,
            "polygon": {
                "positions": {
                    "cartographicDegrees": [location for location in polygon.locations]
                },
                "material": {
                    "solidColor": {
                        "color": {
                            "rgba": [0, 0, 0, 175]
                        }
                    }
                },
                "height": 0,
                "heightReference": "RELATIVE_TO_GROUND",
                "show": True
            }
        }

        if polygon.start_time is not None:
            czml["availability"] = f"{self._format_date(polygon.start_time)}/{self._format_date(polygon.end_time)}"

            if polygon.values is not None:
                p_interval = polygon.interval
                czml["polygon"]["material"]["solidColor"]["color"] = [{
                    "interval":
                        f"{self._format_date(polygon.start_time + timedelta(hours=i*p_interval))}/"
                        f"{self._format_date(polygon.start_time + timedelta(hours=i*p_interval+p_interval))}",
                    "rgba": color.tolist() + [175]
                } for i, color in enumerate(
                    self._get_colors_for_values(polygon.values, min=min_polygon_value, max=max_polygon_value)
                )]

        return czml

    def generate_point_legend(self, filename):
        min_point_value = np.min([np.min(point.values) for point in self.points])
        max_point_value = np.max([np.max(point.values) for point in self.points])
        self._generate_legend(min_point_value, max_point_value, filename)

    def generate_polygon_legend(self, filename):
        min_polygon_value = np.min([np.min(polygon.values) for polygon in self.polygons])
        max_polygon_value = np.max([np.max(polygon.values) for polygon in self.polygons])
        self._generate_legend(min_polygon_value, max_polygon_value, filename)

    def _generate_legend(self, min_val, max_val, legend_path):
        # Create a colormap from white to blue
        colormap = mcolors.LinearSegmentedColormap.from_list("WtoB", ["white", "blue"])

        if max_val - min_val == 0:
            max_val += 1  # This way the range looks a little better on the legend.

        # Create a gradient image
        gradient = np.linspace(0, 1, 256).reshape(1, -1)
        gradient = np.vstack((gradient, gradient))

        # Create a figure and axis to plot the gradient
        fig, ax = plt.subplots(figsize=(6, 1))
        ax.imshow(gradient, aspect='auto', cmap=colormap)

        # Set the ticks and labels
        ticks = np.linspace(0, 1, 5)
        tick_labels = np.linspace(min_val, max_val, 5)
        ax.set_xticks(ticks * (gradient.shape[1] - 1))
        ax.set_xticklabels([f'{label:.5f}' for label in tick_labels])
        ax.set_yticks([])

        # Save the figure as a PNG file
        plt.savefig(legend_path, bbox_inches='tight')
        plt.close()

    @staticmethod
    def _get_colors_for_values(numbers, min=None, max=None):
        # Scale the numbers to range 0-1    # Calculate the min, max and range of the numbers
        if min is None:
            min_val = np.min(numbers)
        else:
            min_val = min

        if max is None:
            max_val = np.max(numbers)
        else:
            max_val = max

        range_val = max_val - min_val

        # If all numbers are the same, return an array of green color
        if range_val == 0:
            return np.array([[0, 255, 0]] * len(numbers))

        # Otherwise, scale the numbers to range 0-1
        scaled_numbers = (np.array(numbers) - min_val) / range_val

        # Create a colormap that goes from green to red
        colormap = mcolors.LinearSegmentedColormap.from_list("WtoB", ["white", "blue"])

        # Map the scaled numbers to colors
        colors = colormap(scaled_numbers)

        # Convert colors to 8-bit RGB
        colors_8bit = (colors[:, :3] * 255).astype(int)

        return colors_8bit

    @staticmethod
    def _format_date(date):
        return date.strftime('%Y-%m-%dT%H:%M:%SZ')
