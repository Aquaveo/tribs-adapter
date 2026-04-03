from collections import Counter
from datetime import datetime
import numpy as np

from tribs_adapter.common.czml_generator import CZMLGenerator


def test_add_point():
    czml = CZMLGenerator('test')
    czml.add_point([0, 0], [1, 2, 3], 'id', datetime(2021, 1, 1), 1, 1)
    assert len(czml.points) == 1
    assert czml.points[0].location == [0, 0]
    assert czml.points[0].values == [1, 2, 3]
    assert czml.points[0].id == 'id'
    assert czml.points[0].start_time == datetime(2021, 1, 1, 0, 0)
    assert czml.points[0].run_time == 1
    assert czml.points[0].interval == 1

    # add second point
    czml.add_point([1, 1], [4, 5, 6], 'id2', datetime(2021, 1, 1), 1, 1)
    assert len(czml.points) == 2
    assert czml.points[1].location == [1, 1]
    assert czml.points[1].values == [4, 5, 6]
    assert czml.points[1].id == 'id2'
    assert czml.points[1].start_time == datetime(2021, 1, 1, 0, 0)
    assert czml.points[1].run_time == 1
    assert czml.points[1].interval == 1


def test_add_polygon():
    czml = CZMLGenerator('test')
    czml.add_polygon([[0, 0], [1, 0], [1, 1], [0, 1]], [1, 2, 3], 'id', datetime(2021, 1, 1), 1, 1)
    assert len(czml.polygons) == 1
    assert czml.polygons[0].locations == [[0, 0], [1, 0], [1, 1], [0, 1]]
    assert czml.polygons[0].values == [1, 2, 3]
    assert czml.polygons[0].id == 'id'
    assert czml.polygons[0].start_time == datetime(2021, 1, 1, 0, 0)
    assert czml.polygons[0].run_time == 1
    assert czml.polygons[0].interval == 1

    # add second polygon
    czml.add_polygon([[2, 2], [3, 2], [3, 3], [2, 3]], [4, 5, 6], 'id2', datetime(2021, 1, 1), 1, 1)
    assert len(czml.polygons) == 2
    assert czml.polygons[1].locations == [[2, 2], [3, 2], [3, 3], [2, 3]]
    assert czml.polygons[1].values == [4, 5, 6]
    assert czml.polygons[1].id == 'id2'
    assert czml.polygons[1].start_time == datetime(2021, 1, 1, 0, 0)
    assert czml.polygons[1].run_time == 1
    assert czml.polygons[1].interval == 1


def test_write_czml(tmp_path):
    czml = CZMLGenerator('test')
    czml.add_point([0, 0], [1, 2, 3], 'id', datetime(2021, 1, 1), 1, 1)
    czml.add_polygon([[0, 0], [1, 0], [1, 1], [0, 1]], [1, 2, 3], 'id', datetime(2021, 1, 1), 1, 1)
    czml.write_czml(tmp_path / 'test.czml')
    assert (tmp_path / 'test.czml').exists()


def test_generate_czml_for_pixel_files():
    # Generate CZML for pixel files
    czml = CZMLGenerator('test')
    czml.add_point([0, 0], [1, 2, 3], 'id', datetime(2021, 1, 1), 1, 1)
    point_czml = czml._generate_point_czml(czml.points[0])
    assert point_czml == {
        'id': 'id',
        'position': {
            'cartographicDegrees': [0, 0, 20],
            'epoch': '2021-01-01T00:00:00Z'
        },
        'point': {
            'color': [{
                'interval': '2021-01-01T00:00:00Z/2021-01-01T01:00:00Z',
                'rgba': [255, 255, 255, 255]
            }, {
                'interval': '2021-01-01T01:00:00Z/2021-01-01T02:00:00Z',
                'rgba': [127, 127, 255, 255]
            }, {
                'interval': '2021-01-01T02:00:00Z/2021-01-01T03:00:00Z',
                'rgba': [0, 0, 255, 255]
            }],
            'outlineColor': {
                'rgba': [0, 0, 0, 255]
            },
            'outlineWidth': 1,
            'pixelSize': 10,
            'show': True,
            'heightReference': 'RELATIVE_TO_GROUND'
        },
        'availability': '2021-01-01T00:00:00Z/2021-01-01T01:00:00Z'
    }


def test_generate_point_czml_no_start_time():
    # Generate CZML for point files with no start time
    czml = CZMLGenerator('test')
    czml.add_point([0, 0], [1, 2, 3], 'id', None, 1, 1)
    point_czml = czml._generate_point_czml(czml.points[0])
    assert point_czml == {
        'id': 'id',
        'position': {
            'cartographicDegrees': [0, 0, 20]
        },
        'point': {
            'color': {
                "rgba": [255, 255, 255, 255]
            },
            'outlineColor': {
                'rgba': [0, 0, 0, 255]
            },
            'outlineWidth': 1,
            'pixelSize': 10,
            'show': True,
            'heightReference': 'RELATIVE_TO_GROUND'
        },
    }


def test_generate_point_czml_no_values():
    # Generate CZML for point files with no values
    czml = CZMLGenerator('test')
    czml.add_point([0, 0], None, 'id', datetime(2021, 1, 1), 1, 1)
    point_czml = czml._generate_point_czml(czml.points[0])
    assert point_czml == {
        'id': 'id',
        'position': {
            'cartographicDegrees': [0, 0, 20],
            'epoch': '2021-01-01T00:00:00Z'
        },
        'point': {
            'color': {
                "rgba": [255, 255, 255, 255]
            },
            'outlineColor': {
                'rgba': [0, 0, 0, 255]
            },
            'outlineWidth': 1,
            'pixelSize': 10,
            'show': True,
            'heightReference': 'RELATIVE_TO_GROUND'
        },
        'availability': '2021-01-01T00:00:00Z/2021-01-01T01:00:00Z'
    }


def test_generate_polygon_czml():
    # Generate CZML for polygon files
    czml = CZMLGenerator('test')
    czml.add_polygon([[0, 0], [1, 0], [1, 1], [0, 1]], [1, 2, 3], 'id', datetime(2021, 1, 1), 1, 1)
    polygon_czml = czml._generate_polygon_czml(czml.polygons[0])
    assert polygon_czml == {
        'id': 'id',
        'polygon': {
            'positions': {
                'cartographicDegrees': [[0, 0], [1, 0], [1, 1], [0, 1]]
            },
            'material': {
                'solidColor': {
                    'color': [{
                        'interval': '2021-01-01T00:00:00Z/2021-01-01T01:00:00Z',
                        'rgba': [255, 255, 255, 175]
                    }, {
                        'interval': '2021-01-01T01:00:00Z/2021-01-01T02:00:00Z',
                        'rgba': [127, 127, 255, 175]
                    }, {
                        'interval': '2021-01-01T02:00:00Z/2021-01-01T03:00:00Z',
                        'rgba': [0, 0, 255, 175]
                    }]
                }
            },
            'height': 0,
            'heightReference': 'RELATIVE_TO_GROUND',
            'show': True
        },
        'availability': '2021-01-01T00:00:00Z/2021-01-01T01:00:00Z'
    }


def test_generate_polygon_czml_no_start_time():
    # Generate CZML for polygon files with no start time
    czml = CZMLGenerator('test')
    czml.add_polygon([[0, 0], [1, 0], [1, 1], [0, 1]], [1, 2, 3], 'id', None, 1, 1)
    polygon_czml = czml._generate_polygon_czml(czml.polygons[0])
    assert polygon_czml == {
        'id': 'id',
        'polygon': {
            'positions': {
                'cartographicDegrees': [[0, 0], [1, 0], [1, 1], [0, 1]]
            },
            'material': {
                'solidColor': {
                    'color': {
                        "rgba": [0, 0, 0, 175]
                    }
                }
            },
            'height': 0,
            'heightReference': 'RELATIVE_TO_GROUND',
            'show': True
        },
    }


def test_generate_polygon_czml_no_values():
    # Generate CZML for polygon files with no values
    czml = CZMLGenerator('test')
    czml.add_polygon([[0, 0], [1, 0], [1, 1], [0, 1]], None, 'id', datetime(2021, 1, 1), 1, 1)
    polygon_czml = czml._generate_polygon_czml(czml.polygons[0])
    assert polygon_czml == {
        'id': 'id',
        'polygon': {
            'positions': {
                'cartographicDegrees': [[0, 0], [1, 0], [1, 1], [0, 1]],
            },
            'material': {
                'solidColor': {
                    'color': {
                        "rgba": [0, 0, 0, 175]
                    }
                }
            },
            'height': 0,
            'heightReference': 'RELATIVE_TO_GROUND',
            'show': True
        },
        'availability': '2021-01-01T00:00:00Z/2021-01-01T01:00:00Z'
    }


def test_get_colors_for_values():
    numbers = [0, 1, 2, 3, 4]
    colors = CZMLGenerator._get_colors_for_values(numbers)
    assert Counter(map(tuple, colors)) == Counter(
        map(tuple, np.array([[255, 255, 255], [191, 191, 255], [127, 127, 255], [63, 63, 255], [0, 0, 255]]))
    )

    colors = CZMLGenerator._get_colors_for_values(numbers, min=1, max=3)
    assert Counter(map(tuple, colors)) == Counter(
        map(tuple, np.array([[255, 255, 255], [255, 255, 255], [127, 127, 255], [0, 0, 255], [0, 0, 255]]))
    )


def test_format_data():
    test_date = datetime(2021, 1, 1, 0, 0)
    formatted_date = CZMLGenerator._format_date(test_date)
    assert formatted_date == '2021-01-01T00:00:00Z'
