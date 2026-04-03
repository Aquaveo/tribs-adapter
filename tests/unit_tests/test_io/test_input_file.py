import datetime
import json

from pydantic import BaseModel
import pytest
from pytest_unordered import unordered

from tribs_adapter.io.input_file import tRIBSInput, FileDatabasePath, FileDatabasePathCollection
from tribs_adapter.io.options import OptMeshInput, OptIntercept


def compare_file_contents(out_file, expected_file):
    with open(out_file, 'r') as f:
        out_lines = f.read()

    with open(expected_file, 'r') as f:
        comp_lines = f.read()

    assert out_lines == comp_lines


@pytest.mark.parametrize(
    "input_file,expected_fixture", [
        ('salas.in', 'salas_raw_paths'),
        ('smallbasin.in', 'smallbasin_raw_paths'),
    ]
)
def test_tRIBSInput_from_input_file(request, input_file, expected_fixture, input_files_dir):
    expected = request.getfixturevalue(expected_fixture)
    in_file_path = input_files_dir / input_file
    t = tRIBSInput.from_input_file(in_file_path)
    p = t.model_dump()
    assert p == expected


@pytest.mark.parametrize(
    "input_fixture,expected_file", [
        ('salas_raw_paths', 'salas__tRIBSInput_to_input_file.in'),
        ('smallbasin_raw_paths', 'smallbasin__tRIBSInput_to_input_file.in'),
    ]
)
def test_tRIBSInput_to_input_file(request, input_fixture, expected_file, tmp_path, input_files_dir):
    input_dict = request.getfixturevalue(input_fixture)
    t = tRIBSInput(**input_dict)

    # Prepare paths for output file and expected file
    out_path = tmp_path / 'foo.in'
    expected_path = input_files_dir / expected_file

    # Write tRIBSInput object to input file (*.in)
    dot_in_path = t.to_input_file(out_path)
    assert dot_in_path.name == 'foo.in'

    # Compare written input file with expected file
    compare_file_contents(out_path, expected_path)


@pytest.mark.parametrize(
    "input_fixture,expected_file", [
        ('salas_raw_paths', 'salas__tRIBSInput_to_input_file.in'),
        ('smallbasin_raw_paths', 'smallbasin__tRIBSInput_to_input_file.in'),
    ]
)
def test_tRIBSInput_to_input_file_dir_exists(request, input_fixture, expected_file, tmp_path, input_files_dir):
    input_dict = request.getfixturevalue(input_fixture)
    t = tRIBSInput(**input_dict)

    # Prepare paths for output file and expected file
    out_path = tmp_path  # Dir that already exists
    expected_path = input_files_dir / expected_file

    # Write tRIBSInput object to input file (*.in)
    dot_in_path = t.to_input_file(out_path)
    assert dot_in_path.name == t.file_name

    # Compare written input file with expected file
    compare_file_contents(dot_in_path, expected_path)


@pytest.mark.parametrize(
    "input_fixture,expected_file", [
        ('salas_raw_paths', 'salas__tRIBSInput_to_input_file.in'),
        ('smallbasin_raw_paths', 'smallbasin__tRIBSInput_to_input_file.in'),
    ]
)
def test_tRIBSInput_to_input_file_dir_dne(request, input_fixture, expected_file, tmp_path, input_files_dir):
    input_dict = request.getfixturevalue(input_fixture)
    t = tRIBSInput(**input_dict)

    # Prepare paths for output file and expected file
    out_path = tmp_path / 'foo'  # Dir that doesn't exist
    expected_path = input_files_dir / expected_file

    # Write tRIBSInput object to input file (*.in)
    dot_in_path = t.to_input_file(out_path)
    assert dot_in_path.name == t.file_name

    # Compare written input file with expected file
    compare_file_contents(dot_in_path, expected_path)


@pytest.mark.parametrize(
    "input_fixture,expected_file", [
        ('salas_raw_paths', 'salas.json'),
        ('smallbasin_raw_paths', 'smallbasin.json'),
    ]
)
def test_tRIBSInput_to_model_dump_json(request, input_fixture, expected_file, input_files_dir):
    input_dict = request.getfixturevalue(input_fixture)
    t = tRIBSInput(**input_dict)
    dumped_json = t.model_dump_json()

    # Uncomment to update JSON files
    # with open(input_files_dir / expected_file, 'w') as f:
    #     f.write(dumped_json)

    with open(input_files_dir / expected_file, 'r') as f:
        expected = f.read()

    assert dumped_json == expected


@pytest.mark.parametrize(
    "json_file,expected_fixture", [
        ('salas.json', 'salas_raw_paths'),
        ('smallbasin.json', 'smallbasin_raw_paths'),
    ]
)
def test_tRIBSInput_from_model_dump_json(request, json_file, expected_fixture, input_files_dir):
    expected_dict = request.getfixturevalue(expected_fixture)
    with open(input_files_dir / json_file, 'r') as f:
        in_json_str = f.read()

    in_json = json.loads(in_json_str)
    t = tRIBSInput(**in_json)
    dumped_dict = t.model_dump()

    assert dumped_dict == expected_dict


@pytest.mark.parametrize(
    "input_fixture,expected_file", [
        ('salas_resource_paths', 'salas_resource_paths.json'),
        ('smallbasin_resource_paths', 'smallbasin_resource_paths.json'),
    ]
)
def test_tRIBSInput_to_model_dump_json_with_resource_paths(request, input_fixture, expected_file, input_files_dir):
    input_dict = request.getfixturevalue(input_fixture)
    t = tRIBSInput(**input_dict)
    dumped_json = t.model_dump_json()

    # Uncomment to update JSON files
    # with open(input_files_dir / expected_file, 'w') as f:
    #     f.write(dumped_json)

    with open(input_files_dir / expected_file, 'r') as f:
        expected = f.read()

    assert dumped_json == expected


@pytest.mark.parametrize(
    "json_file,expected_fixture", [
        ('salas_resource_paths.json', 'salas_resource_paths'),
        ('smallbasin_resource_paths.json', 'smallbasin_resource_paths'),
    ]
)
def test_tRIBSInput_from_model_dump_json_with_resource_paths(request, json_file, expected_fixture, input_files_dir):
    expected_dict = request.getfixturevalue(expected_fixture)
    with open(input_files_dir / json_file, 'r') as f:
        in_json_str = f.read()

    in_json = json.loads(in_json_str)
    t = tRIBSInput(**in_json)
    dumped_dict = t.model_dump()

    assert dumped_dict == expected_dict


@pytest.mark.parametrize(
    "input_file,expected_cards", [
        (
            'salas.in', [
                'WEATHERTABLENAME',
                'BEDROCKFILE',
                'GWATERFILE',
                'SOILTABLENAME',
                'SOILMAPNAME',
                'RAINFILE',
                'LANDTABLENAME',
                'LANDMAPNAME',
                'HYDRONODELIST',
                'OUTLETNODELIST',
                'NODEOUTPUTLIST',
                'POINTFILENAME',
                'INPUTDATAFILE',
                'HYDROMETBASENAME',
                'GAUGESTATIONS',
                'HYDROMETCONVERT',
                'HYDROMETSTATIONS',
                'HYDROMETGRID',
                'OUTFILENAME',
                'OUTHYDROFILENAME',
            ]
        ),
        (
            'smallbasin.in', [
                'BEDROCKFILE',
                'GWATERFILE',
                'SOILTABLENAME',
                'SOILMAPNAME',
                'RAINFILE',
                'LANDTABLENAME',
                'LANDMAPNAME',
                'HYDRONODELIST',
                'OUTLETNODELIST',
                'NODEOUTPUTLIST',
                'POINTFILENAME',
                'INPUTDATAFILE',
                'ARCINFOFILENAME',
                'HYDROMETSTATIONS',
                'HYDROMETBASENAME',
                'OUTFILENAME',
                'OUTHYDROFILENAME',
            ]
        ),
    ]
)
def test_tRIBSInput_files(input_file, expected_cards, input_files_dir):
    in_file_path = input_files_dir / input_file
    t = tRIBSInput.from_input_file(in_file_path)
    cards = []
    for card, field in t.files():
        assert isinstance(field, (FileDatabasePath, FileDatabasePathCollection))
        cards.append(card)
    assert cards == unordered(expected_cards)


salas_all_files = (
    'salas.in', tRIBSInput.FilesMode.ALL_FILES, [
        'WEATHERTABLENAME',
        'BEDROCKFILE',
        'GWATERFILE',
        'SOILTABLENAME',
        'SOILMAPNAME',
        'RAINFILE',
        'LANDTABLENAME',
        'LANDMAPNAME',
        'HYDRONODELIST',
        'OUTLETNODELIST',
        'NODEOUTPUTLIST',
        'POINTFILENAME',
        'INPUTDATAFILE',
        'HYDROMETBASENAME',
        'GAUGESTATIONS',
        'HYDROMETCONVERT',
        'HYDROMETSTATIONS',
        'HYDROMETGRID',
        'OUTFILENAME',
        'OUTHYDROFILENAME',
    ]
)
salas_input_only = (
    'salas.in', tRIBSInput.FilesMode.INPUT_ONLY, [
        'WEATHERTABLENAME',
        'BEDROCKFILE',
        'GWATERFILE',
        'SOILTABLENAME',
        'SOILMAPNAME',
        'RAINFILE',
        'LANDTABLENAME',
        'LANDMAPNAME',
        'HYDRONODELIST',
        'OUTLETNODELIST',
        'NODEOUTPUTLIST',
        'POINTFILENAME',
        'INPUTDATAFILE',
        'HYDROMETBASENAME',
        'GAUGESTATIONS',
        'HYDROMETCONVERT',
        'HYDROMETSTATIONS',
        'HYDROMETGRID',
    ]
)
salas_output_only = ('salas.in', tRIBSInput.FilesMode.OUTPUT_ONLY, [
    'OUTFILENAME',
    'OUTHYDROFILENAME',
])
smallbasin_all_files = (
    'smallbasin.in', tRIBSInput.FilesMode.ALL_FILES, [
        'BEDROCKFILE',
        'GWATERFILE',
        'SOILTABLENAME',
        'SOILMAPNAME',
        'RAINFILE',
        'LANDTABLENAME',
        'LANDMAPNAME',
        'HYDRONODELIST',
        'OUTLETNODELIST',
        'NODEOUTPUTLIST',
        'POINTFILENAME',
        'INPUTDATAFILE',
        'ARCINFOFILENAME',
        'HYDROMETSTATIONS',
        'HYDROMETBASENAME',
        'OUTFILENAME',
        'OUTHYDROFILENAME',
    ]
)
smallbasin_input_only = (
    'smallbasin.in', tRIBSInput.FilesMode.INPUT_ONLY, [
        'BEDROCKFILE',
        'GWATERFILE',
        'SOILTABLENAME',
        'SOILMAPNAME',
        'RAINFILE',
        'LANDTABLENAME',
        'LANDMAPNAME',
        'HYDRONODELIST',
        'OUTLETNODELIST',
        'NODEOUTPUTLIST',
        'POINTFILENAME',
        'INPUTDATAFILE',
        'ARCINFOFILENAME',
        'HYDROMETSTATIONS',
        'HYDROMETBASENAME',
    ]
)
smallbasin_output_only = ('smallbasin.in', tRIBSInput.FilesMode.OUTPUT_ONLY, [
    'OUTFILENAME',
    'OUTHYDROFILENAME',
])


@pytest.mark.parametrize(
    "input_file,files_mode,expected_cards", [
        salas_all_files, salas_input_only, salas_output_only, smallbasin_all_files, smallbasin_input_only,
        smallbasin_output_only
    ]
)
def test_tRIBSInput_files_with_mode(input_file, files_mode, expected_cards, input_files_dir):
    in_file_path = input_files_dir / input_file
    t = tRIBSInput.from_input_file(in_file_path)
    cards = []
    for card, field in t.files(mode=files_mode):
        assert isinstance(field, (FileDatabasePath, FileDatabasePathCollection))
        cards.append(card)
    assert cards == unordered(expected_cards)


@pytest.mark.parametrize(
    "input_file,expected_fixture", [
        ('salas.in', 'salas_raw_paths_copy_update'),
        ('smallbasin.in', 'smallbasin_raw_paths_copy_update'),
    ]
)
def test_tRIBSInput_copy_update(request, input_file, expected_fixture, input_files_dir):
    expected = request.getfixturevalue(expected_fixture)
    in_file_path = input_files_dir / input_file
    t = tRIBSInput.from_input_file(in_file_path)
    update_dict = {
        'GRAPHOPTION': 1,
        'STDUR': 0.1,
        'RAININTRVL': 2.0,
        'STARTDATE': '2020-04-01 00:00:00',
    }
    u = t.copy_update(update_dict)
    assert u is not t
    p = u.model_dump()
    assert p == expected


def test_tRIBSInput_set_value(input_files_dir):
    in_file_path = input_files_dir / 'salas.in'
    t = tRIBSInput.from_input_file(in_file_path)
    assert t.files_and_pathnames.mesh_generation.INPUTDATAFILE.path == 'Output/voronoi/salas'
    t.set_value('INPUTDATAFILE', FileDatabasePath(path='foo/bar'))
    assert t.files_and_pathnames.mesh_generation.INPUTDATAFILE.path == 'foo/bar'

    assert t.run_options.OPTMESHINPUT == OptMeshInput.points
    t.set_value('OPTMESHINPUT', OptMeshInput.tMesh)
    assert t.run_options.OPTMESHINPUT == OptMeshInput.tMesh
    t.set_value('OPTMESHINPUT', 3)
    assert t.run_options.OPTMESHINPUT == OptMeshInput.arcGridRandom


@pytest.mark.parametrize("input_file", [
    'salas.in',
    'smallbasin.in',
])
def test_tRIBSInput_files_update(input_file, input_files_dir):
    in_file_path = input_files_dir / input_file
    t = tRIBSInput.from_input_file(in_file_path)

    # Update values of field in loop
    for _, field in t.files():
        if isinstance(field, FileDatabasePath):
            field.file_collection_paths = ['foo']
        else:
            field.file_database_paths = ['foo']

    # Verify changes were persisted in model
    assert t.files_and_pathnames.mesh_generation.POINTFILENAME.file_collection_paths == ['foo']
    assert t.files_and_pathnames.output_data.OUTFILENAME.file_database_paths == ['foo']

    for _, field in t.files():
        if isinstance(field, FileDatabasePath):
            assert field.file_collection_paths == ['foo']
        else:
            assert field.file_database_paths == ['foo']


@pytest.mark.parametrize(
    "input_file,card,expected_value", [
        (
            'salas.in', 'INPUTDATAFILE',
            FileDatabasePath(
                resource_id=None, file_collection_id=None, file_collection_paths=[], path='Output/voronoi/salas'
            )
        ),
        ('salas.in', 'OUTHYDROFILENAME', FileDatabasePathCollection(file_database_paths=[], path='Output/hyd/salas')),
        ('salas.in', 'DEPTHTOBEDROCK', 5.0),
        ('salas.in', 'OPTMESHINPUT', OptMeshInput.points),
        ('salas.in', 'ARCINFOFILENAME', None),
        ('salas.in', 'DOESNOTEXIST', None),
        ('smallbasin.in', 'STARTDATE', datetime.datetime(1996, 9, 24, 0, 0)),
        (
            'smallbasin.in', 'ARCINFOFILENAME',
            FileDatabasePath(
                resource_id=None, file_collection_id=None, file_collection_paths=[], path='Input/ArcFiles/smallbasin'
            )
        ),
        ('smallbasin.in', 'OPTINTERCEPT', OptIntercept.canopyWaterBalance),
        ('smallbasin.in', 'INPUTTIME', 0),
        ('smallbasin.in', 'CHANNELWIDTHFILE', None),
        ('smallbasin.in', 'DOESNOTEXIST', None),
    ]
)
def test_tRIBSInput_get_value(input_file, card, expected_value, input_files_dir):
    in_file_path = input_files_dir / input_file
    t = tRIBSInput.from_input_file(in_file_path)

    ret = t.get_value(card)

    assert ret == expected_value


@pytest.mark.parametrize(
    "input_file,card", [
        ('salas.in', 'ARCINFOFILENAME'),
        ('salas.in', 'DOESNOTEXIST'),
        ('smallbasin.in', 'CHANNELWIDTHFILE'),
        ('smallbasin.in', 'DOESNOTEXIST'),
    ]
)
def test_tRIBSInput_get_value_custom_default(input_file, card, input_files_dir):
    in_file_path = input_files_dir / input_file
    t = tRIBSInput.from_input_file(in_file_path)

    ret = t.get_value(card, default='foo')

    assert ret == 'foo'


@pytest.mark.parametrize(("card,expected_extensions"), [
    ('INPUTDATAFILE', ['.edges', '.nodes', '.tri', '.z', '_area', '_reach', '_voi', '_width']),
    ('RAINFILE', ['txt']),
])
def test_tRIBSInput_get_expected_file_extensions(card, expected_extensions, input_files_dir):
    in_file_path = input_files_dir / 'salas.in'
    t = tRIBSInput.from_input_file(in_file_path)

    ret = t.get_expected_file_extensions(card)

    assert ret == unordered(expected_extensions)


def test_tRIBSInput_get_expected_file_extensions_invalid_card(input_files_dir):
    in_file_path = input_files_dir / 'salas.in'
    t = tRIBSInput.from_input_file(in_file_path)

    with pytest.raises(ValueError):
        t.get_expected_file_extensions('DOESNOTEXIST')

    with pytest.raises(ValueError):
        t.get_expected_file_extensions('STARTDATE')  # not a file card


@pytest.mark.parametrize(("input_file,card,relative_paths"), [
    (
        'salas/salas.in', 'INPUTDATAFILE', [
            'Output/voronoi/salas.edges', 'Output/voronoi/salas.nodes', 'Output/voronoi/salas.tri',
            'Output/voronoi/salas.z', 'Output/voronoi/salas_area', 'Output/voronoi/salas_reach',
            'Output/voronoi/salas_voi', 'Output/voronoi/salas_width'
        ]
    ),
    ('salas/salas.in', 'RAINFILE', ['Rain/p0630200417.txt', 'Rain/p0531200418.txt']),
    ('salas_issues/salas_issues.in', 'RAINFILE', []),
    (
        'salas_issues/salas_issues.in', 'FORECASTFILE',
        ['Forecast/Nested', 'Forecast/forecast.fake', 'Forecast/Nested/nested_forecast.fake']
    ),
])
def test_tRIBSInput_expand_paths(input_file, card, relative_paths, files_dir):
    in_file_path = files_dir / 'models' / input_file
    model_root = in_file_path.parent
    t = tRIBSInput.from_input_file(in_file_path)
    ret = t.expand_paths(card, model_root)

    expected_paths = [model_root / r for r in relative_paths]
    assert ret == unordered(expected_paths)


def test_tRIBSInput_expand_paths_invalid_card(files_dir):
    in_file_path = files_dir / 'models' / 'salas' / 'salas.in'
    model_root = in_file_path.parent
    t = tRIBSInput.from_input_file(in_file_path)

    with pytest.raises(ValueError):
        t.expand_paths('DOESNOTEXIST', model_root)

    with pytest.raises(ValueError):
        t.expand_paths('STARTDATE', model_root)  # not a file card


@pytest.mark.parametrize(("input_file,card,expected_warning_msg"), [
    ('salas_issues/salas_issues.in', 'HYDROMETGRID', 'is a directory'),
    ('salas_issues/salas_issues.in', 'BEDROCKFILE', 'it does not exist'),
    ('salas_issues/salas_issues.in', 'LANDMAPNAME', 'expects a file with one of the following extensions: .lan'),
])
def test_tRIBSInput_warnings(input_file, card, expected_warning_msg, files_dir):
    in_file_path = files_dir / 'models' / input_file
    model_root = in_file_path.parent
    t = tRIBSInput.from_input_file(in_file_path)

    with pytest.warns(UserWarning) as record:
        ret = t.expand_paths(card, model_root)
        assert len(record) == 1
        wrn_msg = record[0].message.args[0]
        assert card in wrn_msg
        assert expected_warning_msg in wrn_msg

    assert ret == []


@pytest.mark.parametrize(("input_file,card,relative_paths"), [
    ('salas_issues/salas_issues.in', 'BEDROCKFILE', ['Input/salas.brd']),
])
def test_tRIBSInput_with_dne_files(input_file, card, relative_paths, files_dir):
    in_file_path = files_dir / 'models' / input_file
    model_root = in_file_path.parent
    t = tRIBSInput.from_input_file(in_file_path)

    ret = t.expand_paths(card, model_root, only_existing=False)

    expected_paths = [model_root / r for r in relative_paths]
    assert ret == expected_paths


def test_FileDatabasePath():
    fdp = FileDatabasePath(
        resource_id='a73ce902-e443-4050-a06e-a89db54afd44',
        file_collection_id='bd470ab6-b5f3-4d9a-b6b1-84a1979a6502',
        file_collection_paths=['foo', 'bar'],
        path='baz'
    )

    assert str(fdp.resource_id) == 'a73ce902-e443-4050-a06e-a89db54afd44'
    assert str(fdp.file_collection_id) == 'bd470ab6-b5f3-4d9a-b6b1-84a1979a6502'
    assert fdp.file_collection_paths == ['foo', 'bar']
    assert fdp.path == 'baz'


def test_FileDatabasePath_no_args():
    fdp = FileDatabasePath()

    assert fdp.resource_id is None
    assert fdp.file_collection_id is None
    assert fdp.file_collection_paths == []
    assert fdp.path == ''


def test_FileDatabasePath_str():
    class Foo(BaseModel):
        fdp: FileDatabasePath = FileDatabasePath()

    foo = Foo(fdp='foo/baz.bar')

    assert foo.fdp.resource_id is None
    assert foo.fdp.file_collection_id is None
    assert foo.fdp.file_collection_paths == []
    assert foo.fdp.path == 'foo/baz.bar'


def test_FileDatabasePath_dict():
    class Foo(BaseModel):
        fdp: FileDatabasePath = FileDatabasePath()

    foo = Foo(
        fdp={
            'resource_id': 'a73ce902-e443-4050-a06e-a89db54afd44',
            'file_collection_id': 'bd470ab6-b5f3-4d9a-b6b1-84a1979a6502',
            'file_collection_paths': ['foo', 'bar'],
            'path': 'baz'
        }
    )

    assert str(foo.fdp.resource_id) == 'a73ce902-e443-4050-a06e-a89db54afd44'
    assert str(foo.fdp.file_collection_id) == 'bd470ab6-b5f3-4d9a-b6b1-84a1979a6502'
    assert foo.fdp.file_collection_paths == ['foo', 'bar']
    assert foo.fdp.path == 'baz'


def test_FileDatabasePath_dict_empty_str_ids():
    class Foo(BaseModel):
        fdp: FileDatabasePath = FileDatabasePath()

    foo = Foo(fdp={
        'resource_id': '',
        'file_collection_id': '',
    })

    assert foo.fdp.resource_id is None
    assert foo.fdp.file_collection_id is None
    assert foo.fdp.file_collection_paths == []
    assert foo.fdp.path == ''


def test_FileDatabasePath_error():
    class Foo(BaseModel):
        fdp: FileDatabasePath = FileDatabasePath()

    with pytest.raises(TypeError) as exc_info:
        Foo(fdp=1)  # not a dict or str

    assert exc_info.value.args[0] == 'Expected str or dict, got "int" instead.'


def test_FileDatabasePathCollection_str():
    class Foo(BaseModel):
        fdpc: FileDatabasePathCollection = FileDatabasePathCollection()

    foo = Foo(fdpc='foo/baz.bar')

    assert foo.fdpc.file_database_paths == []
    assert foo.fdpc.path == 'foo/baz.bar'


def test_FileDatabasePathCollection_dict():
    class Foo(BaseModel):
        fdpc: FileDatabasePathCollection = FileDatabasePathCollection()

    foo = Foo(
        fdpc={
            'file_database_paths': [{
                'resource_id': 'a73ce902-e443-4050-a06e-a89db54afd44',
                'file_collection_id': 'bd470ab6-b5f3-4d9a-b6b1-84a1979a6502',
                'file_collection_paths': ['foo', 'bar'],
                'path': 'goo'
            }],
            'path': 'baz'
        }
    )

    assert foo.fdpc.file_database_paths == [
        FileDatabasePath(
            resource_id='a73ce902-e443-4050-a06e-a89db54afd44',
            file_collection_id='bd470ab6-b5f3-4d9a-b6b1-84a1979a6502',
            file_collection_paths=['foo', 'bar'],
            path='goo'
        )
    ]
    assert foo.fdpc.path == 'baz'


def test_FileDatabasePathCollection_error():
    class Foo(BaseModel):
        fdpc: FileDatabasePathCollection = FileDatabasePathCollection()

    with pytest.raises(TypeError) as exc_info:
        Foo(fdpc=1)  # not a dict or str

    assert exc_info.value.args[0] == 'Expected str or dict, got "int" instead.'
