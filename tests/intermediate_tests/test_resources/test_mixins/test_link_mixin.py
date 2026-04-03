import pytest
from tethysext.atcore.models.app_users import Resource

from tribs_adapter.resources import Dataset, Realization, Scenario, Project
from tribs_adapter.resources.mixins import LinkMixin


def test_defaults():
    """Test defaults."""
    assert LinkMixin.AS_PARENT == 'parent'
    assert LinkMixin.AS_CHILD == 'child'
    assert LinkMixin.link_as == LinkMixin.AS_CHILD

    inst = LinkMixin()
    assert inst.valid_link_types == (Resource, )
    assert inst.link_as == LinkMixin.AS_CHILD


def test_scenario_link_dataset(db_session, minimal_scenario, minimal_dataset):
    # add_link
    minimal_scenario.add_link(minimal_dataset)
    db_session.add(minimal_scenario)
    db_session.commit()

    assert minimal_dataset in minimal_scenario.get_linked()
    assert minimal_dataset in minimal_scenario.get_linked(of_type=Dataset)
    assert minimal_dataset in minimal_scenario.linked_datasets  # convenience property on Scenario
    assert minimal_dataset in minimal_scenario.children

    # remove_link
    minimal_scenario.remove_link(minimal_dataset)
    db_session.commit()
    db_session.refresh(minimal_scenario)

    assert minimal_dataset not in minimal_scenario.get_linked()
    assert minimal_dataset not in minimal_scenario.get_linked(of_type=Dataset)
    assert minimal_dataset not in minimal_scenario.linked_datasets  # convenience property on Scenario
    assert minimal_dataset not in minimal_scenario.children

    # cleanup
    db_session.delete(minimal_scenario)
    db_session.delete(minimal_dataset)
    db_session.commit()


def test_scenario_link_invalid(minimal_scenario, minimal_realization):
    with pytest.raises(ValueError) as exc:
        minimal_scenario.add_link(minimal_realization)

    assert exc.value.args[0] == 'Scenario resources can only be linked to: Dataset'


def test_scenario_get_linked_invalid(minimal_scenario):
    with pytest.raises(ValueError) as exc:
        minimal_scenario.get_linked(of_type=Realization)

    assert exc.value.args[0] == 'Scenario resources can only be linked to: Dataset'


def test_realization_link_dataset(db_session, minimal_realization, minimal_dataset):
    # add_link
    minimal_realization.add_link(minimal_dataset)
    db_session.add(minimal_realization)
    db_session.commit()

    assert minimal_dataset in minimal_realization.get_linked()
    assert minimal_dataset in minimal_realization.get_linked(of_type=Dataset)
    assert minimal_dataset in minimal_realization.linked_datasets  # convenience property on Realization
    assert minimal_dataset in minimal_realization.children

    # remove_link
    minimal_realization.remove_link(minimal_dataset)
    db_session.commit()
    db_session.refresh(minimal_realization)

    assert minimal_dataset not in minimal_realization.get_linked()
    assert minimal_dataset not in minimal_realization.get_linked(of_type=Dataset)
    assert minimal_dataset not in minimal_realization.linked_datasets  # convenience property on Realization
    assert minimal_dataset not in minimal_realization.children

    # cleanup
    db_session.delete(minimal_realization)
    db_session.delete(minimal_dataset)
    db_session.commit()


def test_realization_link_invalid(minimal_realization, minimal_scenario):
    with pytest.raises(ValueError) as exc:
        minimal_realization.add_link(minimal_scenario)

    assert exc.value.args[0] == 'Realization resources can only be linked to: Dataset'


def test_realization_get_linked_invalid(minimal_realization):
    with pytest.raises(ValueError) as exc:
        minimal_realization.get_linked(of_type=Scenario)

    assert exc.value.args[0] == 'Realization resources can only be linked to: Dataset'


def test_dataset_link_realization(db_session, minimal_dataset, minimal_realization):
    # add_link
    minimal_dataset.add_link(minimal_realization)
    db_session.add(minimal_dataset)
    db_session.commit()

    assert minimal_realization in minimal_dataset.get_linked()
    assert minimal_realization in minimal_dataset.get_linked(of_type=Realization)
    assert minimal_realization in minimal_dataset.linked_realizations  # convenience property on Dataset
    assert minimal_realization in minimal_dataset.parents

    # remove_link
    minimal_dataset.remove_link(minimal_realization)
    db_session.commit()
    db_session.refresh(minimal_dataset)

    assert minimal_realization not in minimal_dataset.get_linked()
    assert minimal_realization not in minimal_dataset.get_linked(of_type=Realization)
    assert minimal_realization not in minimal_dataset.linked_realizations  # convenience property on Dataset
    assert minimal_realization not in minimal_dataset.parents

    # cleanup
    db_session.delete(minimal_dataset)
    db_session.delete(minimal_realization)
    db_session.commit()


def test_dataset_link_scenario(db_session, minimal_dataset, minimal_scenario):
    # add_link
    minimal_dataset.add_link(minimal_scenario)
    db_session.add(minimal_dataset)
    db_session.commit()

    assert minimal_scenario in minimal_dataset.get_linked()
    assert minimal_scenario in minimal_dataset.get_linked(of_type=Scenario)
    assert minimal_scenario in minimal_dataset.linked_scenarios  # convenience property on Dataset
    assert minimal_scenario in minimal_dataset.parents

    # remove_link
    minimal_dataset.remove_link(minimal_scenario)
    db_session.commit()
    db_session.refresh(minimal_dataset)

    assert minimal_scenario not in minimal_dataset.get_linked()
    assert minimal_scenario not in minimal_dataset.get_linked(of_type=Scenario)
    assert minimal_scenario not in minimal_dataset.linked_scenarios  # convenience property on Dataset
    assert minimal_scenario not in minimal_dataset.parents

    # cleanup
    db_session.delete(minimal_dataset)
    db_session.delete(minimal_scenario)
    db_session.commit()


def test_dataset_link_multiple(db_session, minimal_project, minimal_dataset, minimal_scenario, minimal_realization):
    # add_link
    minimal_dataset.project = minimal_project
    minimal_dataset.add_link(minimal_scenario)
    minimal_dataset.add_link(minimal_realization)
    db_session.add(minimal_dataset)
    db_session.commit()

    linked = minimal_dataset.get_linked()
    assert minimal_scenario in linked
    assert minimal_realization in linked
    assert minimal_project not in linked
    linked_scenarios = minimal_dataset.get_linked(of_type=Scenario)
    assert minimal_scenario in linked_scenarios
    assert minimal_realization not in linked_scenarios
    assert minimal_project not in linked_scenarios
    assert minimal_dataset.linked_scenarios == linked_scenarios
    linked_realizations = minimal_dataset.get_linked(of_type=Realization)
    assert minimal_realization in linked_realizations
    assert minimal_scenario not in linked_realizations
    assert minimal_project not in linked_realizations
    assert minimal_dataset.linked_realizations == linked_realizations

    assert minimal_scenario in minimal_dataset.parents
    assert minimal_realization in minimal_dataset.parents
    assert minimal_project in minimal_dataset.parents

    # remove_link
    minimal_dataset.remove_link(minimal_scenario)
    db_session.commit()
    db_session.refresh(minimal_dataset)

    assert minimal_scenario not in minimal_dataset.get_linked()
    assert minimal_scenario not in minimal_dataset.get_linked(of_type=Scenario)
    assert minimal_scenario not in minimal_dataset.parents
    assert minimal_realization in minimal_dataset.get_linked()

    # cleanup
    db_session.delete(minimal_project)
    db_session.delete(minimal_dataset)
    db_session.delete(minimal_scenario)
    db_session.delete(minimal_realization)
    db_session.commit()


def test_dataset_link_invalid(minimal_dataset, minimal_project):
    with pytest.raises(ValueError) as exc:
        minimal_dataset.add_link(minimal_project)

    assert exc.value.args[0] == 'Dataset resources can only be linked to: Scenario, Realization'


def test_dataset_get_linked_invalid(minimal_dataset):
    with pytest.raises(ValueError) as exc:
        minimal_dataset.get_linked(of_type=Project)

    assert exc.value.args[0] == 'Dataset resources can only be linked to: Scenario, Realization'
