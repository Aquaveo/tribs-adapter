from tribs_adapter.resources import Project, Scenario, Realization


def test_project_descendant_property(
    db_session, minimal_project, minimal_scenario, minimal_dataset, minimal_realization
):
    # Setup
    minimal_scenario.project = minimal_project
    minimal_realization.scenario = minimal_scenario
    db_session.add(minimal_project)
    db_session.commit()

    project = db_session.query(Project).one()
    scenario = db_session.query(Scenario).one()
    realization = db_session.query(Realization).one()

    # Tests
    r_project = realization.project
    assert r_project == project

    # Tear down
    db_session.delete(project)
    db_session.delete(scenario)
    db_session.delete(realization)
    db_session.commit()


def test_project_descendant_property_no_parent(db_session, minimal_scenario, minimal_dataset, minimal_realization):
    db_session.add(minimal_scenario)
    db_session.add(minimal_realization)
    db_session.commit()

    scenario = db_session.query(Scenario).one()
    realization = db_session.query(Realization).one()

    s_project = scenario.project
    assert s_project is None
    r_project = realization.project
    assert r_project is None

    db_session.delete(scenario)
    db_session.delete(realization)
    db_session.commit()
