import pytest

from tribs_adapter.resources import Scenario, Realization
from tribs_adapter.io import tRIBSInput


def test_scenario_input_file_property(minimal_scenario, smallbasin_resource_paths):
    assert isinstance(minimal_scenario, Scenario)
    minimal_scenario.input_file = tRIBSInput(**smallbasin_resource_paths)
    ret = minimal_scenario.input_file
    assert isinstance(ret, tRIBSInput)


def test_scenario_input_file_invalid(minimal_scenario):
    with pytest.raises(ValueError):
        minimal_scenario.input_file = 'invalid'


def test_scenario_input_file_initial(minimal_scenario):
    assert minimal_scenario.input_file is None


def test_realization_input_file_property(minimal_realization, smallbasin_resource_paths):
    assert isinstance(minimal_realization, Realization)
    minimal_realization.input_file = tRIBSInput(**smallbasin_resource_paths)
    ret = minimal_realization.input_file
    assert isinstance(ret, tRIBSInput)


def test_realization_input_file_invalid(minimal_realization):
    with pytest.raises(ValueError):
        minimal_realization.input_file = 'invalid'


def test_realization_input_file_initial(minimal_realization):
    assert minimal_realization.input_file is None
