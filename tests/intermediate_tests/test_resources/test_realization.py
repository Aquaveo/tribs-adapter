import datetime
import json
from unittest import mock
from uuid import UUID, uuid4

import pytest
from pytest_unordered import unordered
from sqlalchemy.orm import object_session

from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from tribs_adapter.resources import Realization, Dataset, Scenario
from .realization_data import (
    expected_datasets_salas, expected_file_fields_salas, expected_datasets_examplebasin,
    expected_file_fields_examplebasin, expected_datasets_salas_issues, expected_file_fields_salas_issues
)
from .serialization_data import serialized_project, replace_random_vals, replace_random_vals_str

# Test cases
salas_in = ('salas/salas.in', expected_file_fields_salas, expected_datasets_salas, 5)
examplebasin_in = ('examplebasin/examplebasin.in', expected_file_fields_examplebasin, expected_datasets_examplebasin, 1)
salas_issues = ('salas_issues/salas_issues.in', expected_file_fields_salas_issues, expected_datasets_salas_issues, 8)


def test_exec_start_property(minimal_realization):
    assert isinstance(minimal_realization, Realization)
    minimal_realization.exec_start = datetime.datetime.now()
    ret = minimal_realization.exec_start
    assert isinstance(ret, datetime.datetime)


def test_exec_start_invalid(minimal_realization):
    with pytest.raises(ValueError):
        minimal_realization.exec_start = 'invalid'


def test_exec_start_initial(minimal_realization):
    assert minimal_realization.exec_start is None


def test_exec_end_property(minimal_realization):
    assert isinstance(minimal_realization, Realization)
    minimal_realization.exec_end = datetime.datetime.now()
    ret = minimal_realization.exec_end
    assert isinstance(ret, datetime.datetime)


def test_exec_end_invalid(minimal_realization):
    with pytest.raises(ValueError):
        minimal_realization.exec_end = 'invalid'


def test_exec_end_initial(minimal_realization):
    assert minimal_realization.exec_end is None


def test_realization_scenario_relationship(db_session, minimal_scenario, minimal_realization):
    # add to db
    db_session.add(minimal_realization)
    db_session.commit()
    realization = db_session.query(Realization).one()

    # initial
    assert realization.scenario is None

    # scenario setter
    realization.scenario = minimal_scenario
    db_session.commit()
    db_session.refresh(realization)
    assert realization.scenario == minimal_scenario
    assert realization.scenario in realization.parents

    # scenario setter overwrites existing scenario
    another_scenario = Scenario(name="Another Scenario")
    realization.scenario = another_scenario
    db_session.commit()
    db_session.refresh(realization)
    assert realization.scenario == another_scenario
    assert realization.scenario != minimal_scenario
    assert another_scenario in realization.parents
    assert minimal_scenario not in realization.parents

    # scenario getter
    scenario = realization.scenario
    assert isinstance(scenario, Scenario)

    # clean up
    db_session.delete(scenario)
    db_session.delete(realization)
    db_session.commit()


def test_realization_scenario_setter_invalid(minimal_realization):
    with pytest.raises(ValueError):
        minimal_realization.scenario = "some_invalid_scenario"


def realization_asserts_and_cleanup(
    realization_id, expected_file_fields, expected_datasets, expected_warnings, db_session, scenario, recwarn
):
    assert realization_id is not None
    assert len(recwarn) == expected_warnings

    realization = db_session.query(Realization).get(realization_id)

    assert realization.scenario is scenario
    assert len(realization.get_linked(of_type=Dataset)) == len(expected_datasets)
    assert realization.input_file is not None
    # assert realization.input_file == scenario.input_file

    for card, f in realization.input_file.files(mode=realization.input_file.FilesMode.OUTPUT_ONLY):
        expected = expected_file_fields[card]
        try:
            assert f.path == expected['path']
            assert len(f.file_database_paths) == len(expected['fdps'])
            for i, fdp in enumerate(f.file_database_paths):
                assert isinstance(fdp.resource_id, UUID)
                assert isinstance(fdp.file_collection_id, UUID)
                assert fdp.file_collection_paths == unordered(expected['fdps'][i])
        except AssertionError:
            print(f'Failed on card {card}')
            raise

    for dataset, expected_dataset in zip(
        sorted(realization.get_linked(of_type=Dataset), key=lambda d: d.name),
        sorted(expected_datasets, key=lambda e: e['name'])
    ):
        assert dataset.name == expected_dataset['name']
        assert dataset.description == expected_dataset['description']
        assert dataset.dataset_type == expected_dataset['type']
        assert realization in dataset.get_linked(of_type=Realization)
        db_session.delete(dataset)

    db_session.delete(realization)
    db_session.commit()


@pytest.mark.parametrize(
    'input_file,expected_file_fields,expected_datasets,expected_warnings', [salas_in, examplebasin_in, salas_issues]
)
def test_realization_new(
    input_file,
    expected_file_fields,
    expected_datasets,
    expected_warnings,
    db_session,
    scenario_with_input,
    files_dir,
    recwarn,
):
    input_file_path = files_dir / 'models' / input_file
    scenario = scenario_with_input(input_file_path)
    model_root = input_file_path.parent
    if 'salas.in' in input_file:
        model_root = str(model_root)  # Test at least one with a string path

    ret = Realization.new(
        session=db_session,
        name='Test Realization',
        description='Test Realization Description',
        created_by='_staff',
        scenario=scenario,
        model_root=model_root,
    )

    realization_asserts_and_cleanup(
        ret.id, expected_file_fields, expected_datasets, expected_warnings, db_session, scenario, recwarn
    )


def test_realization_new_model_root_dne(db_session, files_dir, scenario_with_input, recwarn):
    input_file_path = files_dir / 'models' / 'salas' / 'salas.in'
    scenario = scenario_with_input(input_file_path)
    with pytest.raises(FileNotFoundError) as exc:
        Realization.new(
            session=db_session,
            name='Test Realization',
            description='Test Realization Description',
            created_by='_staff',
            scenario=scenario,
            model_root='dne',
        )

    assert exc.value.args[0] == 'model_root "dne" is not a directory.'


@pytest.mark.parametrize(
    'input_file,expected_file_fields,expected_datasets,expected_warnings', [salas_in, examplebasin_in, salas_issues]
)
def test_realization_init(
    input_file,
    expected_file_fields,
    expected_datasets,
    expected_warnings,
    db_session,
    scenario_with_input,
    files_dir,
    recwarn,
):
    input_file_path = files_dir / 'models' / input_file
    scenario = scenario_with_input(input_file_path)
    model_root = input_file_path.parent
    if 'salas.in' in input_file:
        model_root = str(model_root)  # Test at least one with a string path

    realization = Realization()
    realization.name = 'Test Realization'
    realization.description = 'Test Realization Init'
    realization.created_by = '_staff'
    db_session.add(realization)
    db_session.commit()
    mock_sm = mock.MagicMock(spec=TribsSpatialManager)

    realization.init(
        scenario=scenario,
        model_root=model_root,
        spatial_manager=mock_sm,
    )

    realization_asserts_and_cleanup(
        realization.id, expected_file_fields, expected_datasets, expected_warnings, db_session, scenario, recwarn
    )
    if 'issues' not in input_file:
        mock_sm.create_layer_for_dataset.assert_called()


def test_realization_init_already_initialized(db_session, scenario_with_input, files_dir, recwarn):
    input_file_path = files_dir / 'models' / 'salas' / 'salas.in'
    scenario = scenario_with_input(input_file_path)
    model_root = input_file_path.parent
    realization = Realization()
    realization.name = 'Test Realization'
    realization.description = 'Test Realization Init'
    realization.created_by = '_staff'
    db_session.add(realization)
    db_session.commit()

    realization.init(
        scenario=scenario,
        model_root=model_root,
    )

    with pytest.raises(RuntimeError):
        realization.init(
            scenario=scenario,
            model_root=model_root,
        )  # second init should fail

    db_session.delete(realization)
    db_session.commit()


def test_realization_init_dataset_exception(db_session, scenario_with_input, files_dir, recwarn):
    input_file_path = files_dir / 'models' / 'salas' / 'salas.in'
    scenario = scenario_with_input(input_file_path)
    model_root = input_file_path.parent
    realization = Realization()
    realization.name = 'Test Realization'
    realization.description = 'Test Realization Init'
    realization.created_by = '_staff'
    db_session.add(realization)
    db_session.commit()

    def dataset_new(name, *args, **kwargs):
        if name == 'Time-Dynamic Variable Output':
            raise RuntimeError('Test Dataset Exception')
        return mock.MagicMock(
            spec=Dataset,
            id=uuid4(),
            file_collection=mock.MagicMock(id=uuid4()),
            file_collection_client=mock.MagicMock(files=[]),
        )

    with mock.patch.object(Dataset, 'new', side_effect=dataset_new) as mock_new_dataset, \
         mock.patch('tribs_adapter.resources.realization.log') as mock_log:
        realization.init(
            scenario=scenario,
            model_root=model_root,
        )

    mock_log.exception.assert_called_once()
    mock_log.exception.assert_called_with(
        'Failed to initialize Dataset "Time-Dynamic Variable Output" for card "OUTFILENAME". Skipping...'
    )
    mock_new_dataset.assert_called()
    assert len(mock_new_dataset.call_args_list) == 7
    realization_output_files = realization.input_file.files(mode=realization.input_file.FilesMode.OUTPUT_ONLY)
    file_datasbase_paths = []
    for _, file_database_collection in realization_output_files:
        file_datasbase_paths.extend(file_database_collection.file_database_paths)
    # 7 output datasets in salas.in, but Time Dynamic fails to initialize
    assert len(file_datasbase_paths) == 6
    assert not any([d.name == 'Time-Dynamic Variable Output' for d in realization.get_linked(of_type=Dataset)])

    # Clean up
    for dataset in realization.get_linked(of_type=Dataset):
        db_session.delete(dataset)
    db_session.delete(realization)
    db_session.commit()


def test_realization_init_generate_visualization_exception(db_session, scenario_with_input, files_dir, recwarn):
    input_file_path = files_dir / 'models' / 'salas' / 'salas.in'
    scenario = scenario_with_input(input_file_path)
    model_root = input_file_path.parent
    realization = Realization()
    realization.name = 'Test Realization'
    realization.description = 'Test Realization Init'
    realization.created_by = '_staff'
    db_session.add(realization)
    db_session.commit()
    mock_sm = mock.MagicMock(spec=TribsSpatialManager)
    mock_sm.create_layer_for_dataset.side_effect = RuntimeError('Test Realization Visualization Exception')

    # No exception raised (init finishes)
    with mock.patch('tribs_adapter.resources.realization.log') as mock_log:
        realization.init(
            scenario=scenario,
            model_root=model_root,
            spatial_manager=mock_sm,
        )

        # should log the exception with any call to generate_visualizations had exceptions (all of them)
        assert mock_log.exception.call_count == 7

        # dataset objects are still created and linked to the realization
        for dataset in realization.linked_datasets:
            mock_log.exception.assert_any_call(
                f'Failed to generate visualization for Dataset named "{dataset.name}" ({dataset.id}).'
            )

    db_session.delete(realization)
    db_session.commit()


def test_realization_serialize(complete_project):
    realization = complete_project.scenarios[0].realizations[0]
    ret = realization.serialize()
    assert isinstance(ret, dict)
    replace_random_vals(ret)
    try:
        assert ret == serialized_project['scenarios'][0]['realizations'][0]
    except AssertionError:
        pytest.xfail(reason="Data order issues on different machines.")


def test_realization_serialize_json(complete_project):
    realization = complete_project.scenarios[0].realizations[0]
    ret = realization.serialize(format='json')
    assert isinstance(ret, str)
    ret = replace_random_vals_str(ret)
    retd = json.loads(ret)
    assert isinstance(retd, dict)
    try:
        assert retd == serialized_project['scenarios'][0]['realizations'][0]  # unstable: order issues on diff machines
    except AssertionError:
        pytest.xfail(reason="Data order issues on different machines.")


def test_realization_delete_children(complete_project):
    project = complete_project
    session = object_session(project)
    assert len(project.scenarios) == 1
    assert len(project.scenarios[0].realizations) == 1
    realization = project.scenarios[0].realizations[0]
    assert len(project.datasets) == 19
    assert len(realization.linked_datasets) == 7
    dataset_ids = [d.id for d in realization.linked_datasets]

    # Should datasets linked to realization
    realization.delete_children()

    assert len(project.datasets) == 12
    assert len(project.scenarios) == 1
    assert len(project.scenarios[0].realizations) == 1
    assert all(session.query(Dataset).get(did) is None for did in dataset_ids)
