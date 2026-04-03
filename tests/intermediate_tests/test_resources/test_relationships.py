import pytest

from tribs_adapter.resources import Project, Scenario


def test_project_scenarios_relationship(db_session, minimal_project, minimal_scenario):
    # add to db
    db_session.add(minimal_project)
    db_session.commit()
    project = db_session.query(Project).one()

    # initial
    assert len(project.scenarios) == 0

    # add_scenario
    project.add_scenario(minimal_scenario)
    assert minimal_scenario in project.scenarios
    assert minimal_scenario in project.children
    db_session.commit()
    db_session.refresh(project)

    # scenarios getter
    assert len(project.scenarios) == 1
    scenario_id = project.scenarios[0].id
    assert len(project.children) == 1
    assert project.children[0].id == scenario_id

    # get_scenario
    scenario = project.get_scenario(scenario_id)
    assert isinstance(scenario, Scenario)
    assert scenario in project.scenarios

    not_a_scenario = project.get_scenario('00000000-0000-0000-0000-000000000000')
    assert not_a_scenario is None

    # remove_scenario
    project.remove_scenario(scenario)
    assert scenario not in project.scenarios

    # clean up
    db_session.delete(project)
    db_session.delete(scenario)
    db_session.commit()


def test_project_add_scenario_invalid(minimal_project):
    with pytest.raises(ValueError):
        minimal_project.add_scenario('not-a-scenario')


def test_project_remove_scenario_invalid(minimal_project):
    with pytest.raises(ValueError):
        minimal_project.remove_scenario('not-a-scenario')


def test_scenario_project_relationship(db_session, minimal_project, minimal_scenario):
    # add to db
    db_session.add(minimal_scenario)
    db_session.commit()
    scenario = db_session.query(Scenario).one()

    # initial
    assert scenario.project is None

    # project setter
    scenario.project = minimal_project
    db_session.commit()
    db_session.refresh(scenario)
    assert scenario.project == minimal_project
    assert scenario.project in scenario.parents

    # project getter
    project = scenario.project
    assert isinstance(project, Project)

    # clean up
    db_session.delete(project)
    db_session.delete(scenario)
    db_session.commit()
