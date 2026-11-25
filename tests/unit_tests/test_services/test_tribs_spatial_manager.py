import datetime
import json
import os
import shutil
from unittest import mock

import pytest

from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager


def _touch(path):
    with open(path, 'w') as f:
        f.write('')
    return str(path)


def test_files_to_visualize_keeps_only_the_last_time_integrated_file():
    files = ['/out/salas.0240_00i', '/out/salas.0000_00i', '/out/salas.1000_00i', '/out/salas.0120_30i']

    assert TribsSpatialManager._files_to_visualize(files) == ['/out/salas.1000_00i']


def test_files_to_visualize_keeps_a_single_time_integrated_file():
    assert TribsSpatialManager._files_to_visualize(['/out/salas.0700_00i']) == ['/out/salas.0700_00i']


def test_files_to_visualize_keeps_every_time_dynamic_file():
    files = ['/out/salas.0006_00d', '/out/salas.0000_00d', '/out/salas.0012_00d']

    assert TribsSpatialManager._files_to_visualize(files) == files


def test_files_to_visualize_without_output_files():
    assert TribsSpatialManager._files_to_visualize([]) == []


def test_is_tribs_variable_output_file(tmp_path):
    assert TribsSpatialManager._is_tribs_variable_output_file(_touch(tmp_path / 'salas.0000_00d'))
    assert TribsSpatialManager._is_tribs_variable_output_file(_touch(tmp_path / 'salas.0700_00i'))
    # Companion files that are not spatial variable output
    companions = ['__meta__.json', 'salas_voi', 'salas_area', 'salas_reach', 'salas_width',
                  'x.gltf', 'x.glb', 'x_legend.png']
    # Other tRIBS output that is not spatial variable output (same OUTFILENAME base, different extension)
    companions += ['salas.pixel', 'salas.mrf', 'salas.rft']
    for name in companions:
        assert not TribsSpatialManager._is_tribs_variable_output_file(_touch(tmp_path / name)), name
    # Directories
    os.mkdir(tmp_path / 'gltf')
    assert not TribsSpatialManager._is_tribs_variable_output_file(str(tmp_path / 'gltf'))


def test_find_voi_file(tmp_path):
    mesh_dir = tmp_path / 'mesh'
    output_dir = tmp_path / 'output'
    mesh_dir.mkdir()
    output_dir.mkdir()
    mesh_file = str(mesh_dir / 'salas')

    # Nothing available
    assert TribsSpatialManager._find_voi_file(mesh_file) is None
    assert TribsSpatialManager._find_voi_file(mesh_file, str(output_dir)) is None

    # In the output dataset collection (written by tRIBS with the _00d/_00i files)
    output_voi = _touch(output_dir / 'scenario_voi')
    assert TribsSpatialManager._find_voi_file(mesh_file, str(output_dir)) == output_voi

    # Next to the mesh files takes precedence
    mesh_voi = _touch(mesh_dir / 'salas_voi')
    assert TribsSpatialManager._find_voi_file(mesh_file, str(output_dir)) == mesh_voi
    assert TribsSpatialManager._find_voi_file(mesh_file) == mesh_voi


def test_parse_cluster_ports():
    parse = TribsSpatialManager._parse_cluster_ports
    assert parse('[8080]') == [8080]
    assert parse('[8081, 8082]') == [8081, 8082]
    assert parse('"[8080]"') == [8080]  # extra level of quoting left by an env loader
    assert parse('8080') == [8080]
    assert parse('["8080", 8081]') == [8080, 8081]  # digit strings are ports too (the app's own parsers accept them)
    assert parse('[1, 65535]') == [1, 65535]
    assert parse(None) == [8081, 8082, 8083, 8084]
    assert parse('not json') == [8081, 8082, 8083, 8084]
    assert parse('["a"]') == [8081, 8082, 8083, 8084]
    # JSON booleans are ints in Python; they must not become ports 1/0, and the cluster needs at least one port
    assert parse('true') == [8081, 8082, 8083, 8084]
    assert parse('[true]') == [8081, 8082, 8083, 8084]
    assert parse('[8080, false]') == [8081, 8082, 8083, 8084]
    assert parse('[]') == [8081, 8082, 8083, 8084]
    assert parse('[0]') == [8081, 8082, 8083, 8084]
    assert parse('[65536]') == [8081, 8082, 8083, 8084]
    assert parse('[70000]') == [8081, 8082, 8083, 8084]
    assert parse('[8080.0]') == [8081, 8082, 8083, 8084]  # not an int
    assert parse('{"a": 1}') == [8081, 8082, 8083, 8084]


def _file_entry(variable, hours, kind='d', legend=True, value_range=(0.5, 2.5)):
    stamp = f'{int(hours):04d}_00{kind}' if hours is not None else None
    name = f'abc-salas_salas-{stamp}_{variable}' if stamp else 'abc-salas'
    entry = dict(
        variable=variable, output_file=f'/out/salas.{stamp}' if stamp else None, hours=hours, kind=kind,
        gltf=f'/tmp/x/gltf/{name}.glb', legend=f'/tmp/x/gltf/{name}_legend.png' if legend else None,
    )
    if value_range is not None:  # None mimics files entries written before the range was recorded
        entry.update(min=value_range[0], max=value_range[1])
    return entry


URL_DIR = 'fdb/fc/gltf'


def test_build_gltf_variables():
    files = [  # unsorted, Nwt missing the middle time step, Mu without legends
        _file_entry('Mu', 20, legend=False), _file_entry('Nwt', 20), _file_entry('Mu', 0, legend=False),
        _file_entry('Nwt', 0), _file_entry('Mu', 10, legend=False),
    ]
    variables = TribsSpatialManager._build_gltf_variables(
        files, URL_DIR, start_date=datetime.datetime(2004, 6, 1), fallback_step_hours=168
    )
    assert [v['name'] for v in variables] == ['Mu', 'Nwt']
    mu, nwt = variables
    assert mu['start'] == '2004-06-01T00:00:00Z'
    assert mu['end'] == '2004-06-01T20:00:00Z'
    assert mu['step_hours'] == 10
    assert [t['hours'] for t in mu['timesteps']] == [0, 10, 20]
    assert [t['time'] for t in mu['timesteps']] == [
        '2004-06-01T00:00:00Z', '2004-06-01T10:00:00Z', '2004-06-01T20:00:00Z'
    ]
    assert mu['timesteps'][1]['url'] == 'fdb/fc/gltf/abc-salas_salas-0010_00d_Mu.glb'
    assert mu['timesteps'][1]['legend'] is None
    assert (mu['min'], mu['max']) == (0.5, 2.5)
    # Nwt: step derived from the files that exist (20 h), not the fallback
    assert [t['hours'] for t in nwt['timesteps']] == [0, 20]
    assert nwt['step_hours'] == 20
    assert nwt['timesteps'][0]['legend'] == 'fdb/fc/gltf/abc-salas_salas-0000_00d_Nwt_legend.png'
    json.dumps(variables)


def test_build_gltf_variables_without_start_date():
    files = [_file_entry('Mu', 10), _file_entry('Mu', 0)]
    variables = TribsSpatialManager._build_gltf_variables(files, URL_DIR)
    assert variables[0]['start'] is None
    assert variables[0]['end'] is None
    assert variables[0]['step_hours'] == 10
    assert [t['hours'] for t in variables[0]['timesteps']] == [0, 10]
    assert all(t['time'] is None for t in variables[0]['timesteps'])


def test_build_gltf_variables_single_timestep_uses_fallback_step():
    files = [_file_entry('Mu', 700, kind='i')]
    variables = TribsSpatialManager._build_gltf_variables(
        files, URL_DIR, start_date=datetime.datetime(2004, 6, 1), fallback_step_hours=10.0
    )
    assert variables[0]['start'] == variables[0]['end'] == '2004-06-30T04:00:00Z'
    assert variables[0]['step_hours'] == 10.0
    assert TribsSpatialManager._build_gltf_variables(files, URL_DIR)[0]['step_hours'] is None


def test_build_gltf_variables_static_entry():
    files = [_file_entry('Elevation', None)]
    variables = TribsSpatialManager._build_gltf_variables(files, URL_DIR, start_date=datetime.datetime(2004, 6, 1))
    assert variables == [dict(
        name='Elevation', label='Elevation', units=None, tier=None, description='', factor=1.0,
        start=None, end=None, step_hours=None, min=0.5, max=2.5,
        timesteps=[dict(hours=None, time=None, url='fdb/fc/gltf/abc-salas.glb',
                        legend='fdb/fc/gltf/abc-salas_legend.png')],
    )]
    assert TribsSpatialManager._build_gltf_variables([], URL_DIR) == []


def test_build_gltf_variables_with_variable_kind():
    """With a variable table, entries carry the sheet's label, units and tier and a display-unit range."""
    files = [
        _file_entry('AvSM', 0, value_range=(0.1, 0.9)), _file_entry('Mystery', 0),
        _file_entry('AvSnSub', 0, value_range=(0.0, 2.0)),
    ]
    variables = TribsSpatialManager._build_gltf_variables(files, URL_DIR, variable_kind='integrated')
    av_sm, mystery, snow = variables
    assert (av_sm['label'], av_sm['units'], av_sm['tier']) == (
        'Mean Surface Soil Moisture (Top 10 cm)', '% saturation', 'priority'
    )
    assert (av_sm['min'], av_sm['max'], av_sm['factor']) == (10.0, 90.0, 100.0)
    assert av_sm['description'].startswith('Time-averaged relative saturation')
    assert av_sm['name'] == 'AvSM'  # the layer key stays the raw column name
    # A column the sheet does not list keeps its name, with no units, tier or conversion
    assert (mystery['label'], mystery['units'], mystery['tier'], mystery['factor']) == ('Mystery', None, None, 1.0)
    assert (mystery['min'], mystery['max']) == (0.5, 2.5)
    # AvSnSub is only in the mrf table, so under 'integrated' it is unknown
    assert snow['tier'] is None and (snow['min'], snow['max']) == (0.0, 2.0)
    json.dumps(variables)


def test_build_gltf_variables_without_value_range():
    """Files entries written before min/max were recorded still group; the range is reported as None."""
    files = [_file_entry('Mu', 10, value_range=None), _file_entry('Mu', 0, value_range=None)]
    variables = TribsSpatialManager._build_gltf_variables(files, URL_DIR)
    assert variables[0]['min'] is None and variables[0]['max'] is None
    assert [t['hours'] for t in variables[0]['timesteps']] == [0, 10]


def test_build_gltf_variables_from_mesh_output(files_dir, tmp_path):
    """End to end over the tin fixture: five time-dynamic files, 10 hours apart (ET changes in every one)."""
    from tribs_adapter.io.tribs_mesh import tRIBSMeshViz

    layers_dir = files_dir / 'spatial_manager' / 'layers' / 'tin'
    output_files = sorted(str(p) for p in (layers_dir / 'output').glob('salas.*_00d'))
    assert len(output_files) == 5
    tmv = tRIBSMeshViz(mesh_basename=layers_dir / 'salas', mesh_epsg=32613, output_files=output_files)
    meta = tmv.to_gltf(str(tmp_path / 'abc-salas'), output_variables=['ET'], generate_legend=True)

    variables = TribsSpatialManager._build_gltf_variables(
        meta['files'], URL_DIR, start_date=datetime.datetime(2004, 6, 1), fallback_step_hours=168
    )
    assert len(variables) == 1
    et = variables[0]
    assert et['name'] == 'ET'
    assert [t['hours'] for t in et['timesteps']] == [0, 10, 20, 30, 40]
    assert et['step_hours'] == 10
    assert et['start'] == '2004-06-01T00:00:00Z'
    assert et['end'] == '2004-06-02T16:00:00Z'
    assert et['timesteps'][0]['url'] == 'fdb/fc/gltf/abc-salas_salas-0000_00d_ET.glb'
    # One legend per variable, scaled over all time steps and shared by every time step
    assert all(t['legend'] == 'fdb/fc/gltf/abc-salas_ET_legend.png' for t in et['timesteps'])
    assert all(os.path.exists(tmp_path / os.path.basename(t['url'])) for t in et['timesteps'])


# --- create_layer_for_dataset: glTF output datasets -----------------------------------------------------------------
# The branch wires the linked realization's node file dataset, STARTDATE and SPOPINTRVL into the glTF viz. The output
# writer (create_tribs_tin_layer, covered by the intermediate tests on real files) is replaced by a spy; _build_gltf_viz
# runs for real so the assertions are on the viz the dataset ends up with.


@pytest.fixture
def tsm():
    return TribsSpatialManager(mock.MagicMock(), reload_ports=[8080])


def _output_dataset(path, dataset_type=DatasetTypes.TRIBS_OUT_TIME_INTEGRATED, start_date=None, spopintrvl=6,
                    linked=True, metstep=60.0):
    dataset = mock.MagicMock()
    dataset.id = 'ds-1'
    dataset.dataset_type = dataset_type
    dataset.file_collection_client.path = str(path)
    dataset.name = 'Output Dataset'
    dataset.file_collection_client.add_item.side_effect = lambda czml_path: shutil.copytree(czml_path, path / 'added')
    dataset.file_collection.file_database_id = 'fdb'
    dataset.file_collection.id = 'fc'
    dataset.linked_realizations = []
    if linked:
        realization = mock.MagicMock()
        realization.id = 'real-1'
        realization.input_file.files_and_pathnames.mesh_generation.INPUTDATAFILE.resource_id = 'node-ds'
        realization.input_file.run_parameters.time_variables.STARTDATE = start_date
        realization.input_file.run_parameters.time_variables.SPOPINTRVL = spopintrvl
        realization.input_file.run_parameters.time_variables.METSTEP = metstep
        dataset.linked_realizations = [realization]
    return dataset


def _session_with_node_file_dataset():
    node_file_dataset = mock.MagicMock()
    session = mock.MagicMock()
    session.query.return_value.get.return_value = node_file_dataset
    return session, node_file_dataset


def _gltf_meta(*entries):
    return dict(origin=[-105.0, 40.0, 1500.0], extents=[-105.1, 39.9, -104.9, 40.1], files=list(entries))


def _patch_tin_layer_writer(mocker, *entries):
    """Replace create_tribs_tin_layer with a spy that writes the (empty) files its metadata names into the output
    dataset's ``gltf`` directory, as the real writer does, and returns that metadata."""
    meta = _gltf_meta(*entries)

    def write(node_file_dataset, mesh_epsg, output_dataset=None, output_variables=None, variable_kind=None,
              met_step_hours=1.0):
        gltf_dir = os.path.join(output_dataset.file_collection_client.path, 'gltf')
        os.makedirs(gltf_dir, exist_ok=True)
        for entry in meta['files']:
            for path in (entry['gltf'], entry['legend']):
                if path:
                    open(os.path.join(gltf_dir, os.path.basename(path)), 'w').close()
        return meta

    return mocker.patch.object(TribsSpatialManager, 'create_tribs_tin_layer', side_effect=write)


def _viz_set_on(dataset):
    dataset.set_attribute.assert_called_once()
    name, viz = dataset.set_attribute.call_args.args
    assert name == 'viz'
    return viz


def test_create_layer_for_time_integrated_dataset_wires_the_realization_into_the_viz(tsm, tmp_path, mocker):
    dataset = _output_dataset(tmp_path, start_date=datetime.datetime(2004, 6, 1), spopintrvl=6)
    session, node_file_dataset = _session_with_node_file_dataset()
    create = _patch_tin_layer_writer(mocker, _file_entry('Z', 0, kind='i'))

    tsm.create_layer_for_dataset(dataset, 26913, session)

    # The mesh comes from the realization's INPUTDATAFILE dataset and the output is rendered with the integrated table
    session.query.return_value.get.assert_called_once_with('node-ds')
    create.assert_called_once_with(
        node_file_dataset, mesh_epsg=26913, output_dataset=dataset, variable_kind='integrated', met_step_hours=1.0
    )
    viz = _viz_set_on(dataset)
    assert viz['type'] == 'gltf'
    assert viz['url'] == [f'{URL_DIR}/abc-salas_salas-0000_00i_Z.glb']
    assert viz['legend'] == [f'{URL_DIR}/abc-salas_salas-0000_00i_Z_legend.png']
    (z,) = viz['variables']
    assert (z['name'], z['tier'], z['label']) == ('Z', 'priority', 'Elevation')
    # STARTDATE anchors the time steps and SPOPINTRVL is the step of a single-file variable
    assert z['timesteps'][0]['time'] == '2004-06-01T00:00:00Z'
    assert (z['start'], z['step_hours']) == ('2004-06-01T00:00:00Z', 6)
    session.commit.assert_called_once()


def test_create_layer_for_time_integrated_dataset_without_a_parsed_startdate(tsm, tmp_path, mocker, caplog):
    """An unparsed STARTDATE (the raw card text) is logged and the variables keep only their hours."""
    dataset = _output_dataset(tmp_path, start_date='06/01/2004/00/00', spopintrvl=6)
    session, _ = _session_with_node_file_dataset()
    _patch_tin_layer_writer(mocker, _file_entry('Z', 0, kind='i'), _file_entry('Z', 10, kind='i'))

    with caplog.at_level('WARNING', logger='tribs_adapter.services.tribs_spatial_manager'):
        tsm.create_layer_for_dataset(dataset, 26913, session)

    assert any('STARTDATE' in r.message and 'real-1' in r.message for r in caplog.records)
    (z,) = _viz_set_on(dataset)['variables']
    assert [t['hours'] for t in z['timesteps']] == [0, 10]
    assert all(t['time'] is None for t in z['timesteps'])
    assert (z['start'], z['end'], z['step_hours']) == (None, None, 10)
    session.commit.assert_called_once()


def test_create_layer_for_time_dynamic_dataset_uses_the_dynamic_variable_table(tsm, tmp_path, mocker):
    dataset = _output_dataset(tmp_path, dataset_type=DatasetTypes.TRIBS_OUT_TIME_DYNAMIC,
                              start_date=datetime.datetime(2004, 6, 1), metstep=30.0)
    session, node_file_dataset = _session_with_node_file_dataset()
    create = _patch_tin_layer_writer(mocker, _file_entry('Nwt', 0, kind='d'), _file_entry('VegFraction', 0, kind='d'))

    tsm.create_layer_for_dataset(dataset, 26913, session)

    # METSTEP is in minutes; the writer gets it in hours for the derived variables
    create.assert_called_once_with(
        node_file_dataset, mesh_epsg=26913, output_dataset=dataset, variable_kind='dynamic', met_step_hours=0.5
    )
    nwt, veg = _viz_set_on(dataset)['variables']
    assert (nwt['name'], nwt['label'], nwt['units'], nwt['tier']) == ('Nwt', 'Depth to Groundwater', 'm', 'priority')
    assert (veg['label'], veg['units'], veg['tier']) == ('Vegetation Fraction', '%', 'secondary')


def test_create_layer_for_output_dataset_requires_a_linked_realization(tsm, tmp_path, mocker):
    dataset = _output_dataset(tmp_path, linked=False)
    session, _ = _session_with_node_file_dataset()
    create = mocker.patch.object(TribsSpatialManager, 'create_tribs_tin_layer')

    with pytest.raises(ValueError, match='requires a linked Realization.*ds-1'):
        tsm.create_layer_for_dataset(dataset, 26913, session)

    create.assert_not_called()
    dataset.set_attribute.assert_not_called()
    session.commit.assert_not_called()


# --- create_tribs_czml_layer: value layers ---------------------------------------------------------------------------
# Real mrf/qout/pixel files from the czml_converters fixtures. The file collection keeps a copy of the czml folder it
# is given (the manager writes it in a temporary folder), so the tests read back the features and the values.

SIMPLE_FILES = os.path.join('czml_converters', 'simple_files')


def _czml_dataset(path, files_dir, dataset_type, data_file):
    shutil.copy(files_dir / SIMPLE_FILES / data_file, path / data_file)
    dataset = mock.MagicMock()
    dataset.id = 'ds-1'
    dataset.dataset_type = dataset_type
    dataset.file_collection_client.path = str(path)
    dataset.name = 'Output Dataset'
    dataset.file_collection_client.add_item.side_effect = lambda czml_path: shutil.copytree(czml_path, path / 'added')
    realization = mock.MagicMock()
    time_variables = realization.input_file.run_parameters.time_variables
    time_variables.STARTDATE = datetime.datetime(2004, 6, 1)
    time_variables.RUNTIME = 24
    time_variables.OPINTRVL = 1
    realization.input_file.files_and_pathnames.mesh_generation.INPUTDATAFILE.resource_id = 'node-ds'
    dataset.linked_realizations = [realization]
    session, node_file_dataset = _session_with_node_file_dataset()
    node_file_dataset.file_collection_client.path = str(files_dir / SIMPLE_FILES)  # holds simple.nodes
    return dataset, session


def _added(path, relative_path):
    return json.loads((path / 'added' / relative_path).read_text())


def test_create_tribs_czml_layer_for_mrf_offers_the_sheet_variables(tsm, tmp_path, files_dir):
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_MRF, 'simple.mrf')
    (tmp_path / 'czml').mkdir()  # a previous visualization

    meta = tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)

    # Priority variables first, then secondary; RainMax, RainMin and FState are hidden by the table
    names = [v['name'] for v in meta['variables']]
    assert names == ['MAP', 'MSMRt', 'MDGW', 'Srf', 'MSM100', 'MSMU']
    assert [v['tier'] for v in meta['variables']] == ['priority'] * 3 + ['secondary'] * 3
    by_name = {v['name']: v for v in meta['variables']}
    assert (by_name['MDGW']['label'], by_name['MDGW']['units'], by_name['MDGW']['factor']) == \
        ('Depth to Groundwater', 'm', 0.001)
    assert (by_name['MSMRt']['units'], by_name['MSMRt']['factor']) == ('% saturation', 100.0)
    assert by_name['MAP']['description']
    # One document with the basin polygon, and one values file per offered variable in display units
    assert sorted(os.listdir(tmp_path / 'added')) == ['ds-1.czml', 'values']
    document, polygon = _added(tmp_path, 'ds-1.czml')
    assert document['name'] == 'Output Dataset' and polygon['id'] == 'polygon [ds-1]'
    assert [v['values'] for v in meta['variables']] == [
        'values/000_MAP.json', 'values/001_MSMRt.json', 'values/002_MDGW.json', 'values/003_Srf.json',
        'values/004_MSM100.json', 'values/005_MSMU.json',
    ]
    mdgw = _added(tmp_path, 'values/002_MDGW.json')
    assert mdgw['ids'] == ['polygon [ds-1]'] and mdgw['hours'][:2] == [1.0, 2.0]
    assert mdgw['values'][0][0] == pytest.approx(3.41766)  # 3417.655425 mm in the file
    assert by_name['MDGW']['min'] <= mdgw['values'][0][0] <= by_name['MDGW']['max']
    # The times are the hours of the rows after STARTDATE
    assert by_name['MAP']['start'] == '2004-06-01T01:00:00Z' and by_name['MAP']['step_hours'] == 1.0
    # The old czml directory is replaced and the extent comes from the node file
    dataset.file_collection_client.delete_item.assert_called_once_with('czml')
    dataset.file_collection_client.add_item.assert_called_once()
    assert dataset.file_collection_client.add_item.call_args.args[0].endswith('czml')
    assert meta['origin'] is not None and len(meta['extents']) == 4
    json.dumps(meta)


def test_create_tribs_czml_layer_for_qout_keeps_the_unit_suffix_in_the_layer_name(tsm, tmp_path, files_dir):
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_QOUT, 'simple_Outlet.qout')

    meta = tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)

    # Hlev is hidden by the table; the layer keeps the file's column name, the label and units come from the table
    (qstrm,) = meta['variables']
    assert (qstrm['name'], qstrm['label'], qstrm['units'], qstrm['tier'], qstrm['factor']) == \
        ('Qstrm_m3-s', 'Streamflow', 'm³/s', 'priority', 1.0)
    assert qstrm['values'] == 'values/000_Qstrm_m3-s.json'
    _, outlet = _added(tmp_path, 'ds-1.czml')
    assert outlet['id'] == 'point_Outlet [ds-1]'
    values = _added(tmp_path, qstrm['values'])
    assert values['ids'] == ['point_Outlet [ds-1]']
    # The time axis is the file's own (every 0.06 h), starting with its first row
    assert values['hours'][:3] == [0.06, 0.12, 0.18]
    assert qstrm['start'] == '2004-06-01T00:03:36Z'
    assert len(values['values'][0]) == len(values['hours'])
    dataset.file_collection_client.delete_item.assert_not_called()


def test_create_tribs_czml_layer_for_pixel_keeps_every_variable_with_its_unit_token(tsm, tmp_path, files_dir):
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_PIXEL, 'simple.pixel')

    meta = tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)

    # Pixel variables are not in the sheet: all stay visible, named by the header, with the unit token translated
    assert [v['name'] for v in meta['variables']] == ['Nwt_mm', 'Nf_mm', 'Nt_mm', 'Mu_mm', 'Mi_mm']
    assert all((v['tier'], v['factor'], v['description']) == (None, 1.0, '') for v in meta['variables'])
    nwt = meta['variables'][0]
    assert (nwt['label'], nwt['units']) == ('Nwt', 'mm')
    # The point is the node named in the file's rows (node 1), with the values of its rows
    _, point = _added(tmp_path, 'ds-1.czml')
    assert point['id'] == 'point_1 [ds-1]'
    values = _added(tmp_path, nwt['values'])
    assert values == {
        'variable': 'Nwt_mm', 'start': '2004-06-01T00:00:00Z', 'hours': [0.0, 1.0, 2.0],
        'ids': ['point_1 [ds-1]'], 'values': [[4033.7, 4043.7, 4053.7]],
    }
    assert (nwt['min'], nwt['max']) == (4033.7, 4053.7)


def test_create_tribs_czml_layer_for_a_plain_pixel_header(tsm, tmp_path, files_dir):
    """Current tRIBS writes the header without column numbers: the layer has the same variables."""
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_PIXEL, 'simple.pixel')
    pixel_file = tmp_path / 'simple.pixel'
    lines = pixel_file.read_text().splitlines()
    pixel_file.write_text('\n'.join(['NodeID Time_hr Nwt_mm Nf_mm Nt_mm Mu_mm Mi_mm '] + lines[1:]) + '\n')

    meta = tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)

    assert [v['name'] for v in meta['variables']] == ['Nwt_mm', 'Nf_mm', 'Nt_mm', 'Mu_mm', 'Mi_mm']
    assert _added(tmp_path, meta['variables'][0]['values'])['values'] == [[4033.7, 4043.7, 4053.7]]


def test_create_tribs_czml_layer_fails_for_a_pixel_file_it_cannot_read(tsm, tmp_path, files_dir):
    """A header that gives no variables fails the layer instead of leaving it empty."""
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_PIXEL, 'simple.pixel')
    (tmp_path / 'simple.pixel').write_text('not a header\n1 2 3\n')

    with pytest.raises(ValueError, match='Could not find the NodeID column in the header of simple.pixel'):
        tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)

    dataset.file_collection_client.add_item.assert_not_called()


def test_create_tribs_czml_layer_fails_without_an_output_file(tsm, tmp_path, files_dir):
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_QOUT, 'simple_Outlet.qout')
    (tmp_path / 'simple_Outlet.qout').unlink()

    with pytest.raises(ValueError, match='No .qout file found in the file collection of dataset ds-1'):
        tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)


def _add_qout_file(path, name):
    shutil.copy(path / 'simple_Outlet.qout', path / name)


def test_create_tribs_czml_layer_for_qout_names_interior_points_as_their_files_do(tsm, tmp_path, files_dir):
    """The plot asks for a point by the name in its entity id, so that is the name of its file. The outlet is node 0
    of the simple mesh: its interior-node file repeats _Outlet.qout and is left out."""
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_QOUT, 'simple_Outlet.qout')
    _add_qout_file(tmp_path, 'simple_3.qout')
    _add_qout_file(tmp_path, 'simple_0.qout')

    meta = tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)

    ids = [entity['id'] for entity in _added(tmp_path, 'ds-1.czml')[1:]]
    assert ids == ['point_3 [ds-1]', 'point_Outlet [ds-1]']
    assert _added(tmp_path, meta['variables'][0]['values'])['ids'] == ids


def test_create_tribs_czml_layer_for_qout_keeps_the_node_name_of_an_outlet_without_an_outlet_file(
    tsm, tmp_path, files_dir
):
    """Without <base>_Outlet.qout the outlet's point is its node, the name the plot can find its file by."""
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_QOUT, 'simple_Outlet.qout')
    (tmp_path / 'simple_Outlet.qout').rename(tmp_path / 'simple_0.qout')

    tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)

    assert [entity['id'] for entity in _added(tmp_path, 'ds-1.czml')[1:]] == ['point_0 [ds-1]']


def test_create_tribs_czml_layer_for_qout_fails_for_a_node_the_mesh_does_not_have(tsm, tmp_path, files_dir):
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_QOUT, 'simple_Outlet.qout')
    _add_qout_file(tmp_path, 'simple_99.qout')

    with pytest.raises(ValueError, match='simple_99.qout is for node 99, which the mesh does not have'):
        tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)


def test_create_tribs_czml_layer_fails_when_no_variable_is_offered(tsm, tmp_path, files_dir):
    """A qout file with only hidden columns would leave a layer of gray points: fail it instead."""
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_QOUT, 'simple_Outlet.qout')
    (tmp_path / 'simple_Outlet.qout').write_text('1-Time,hr\t2-Hlev,m\n0.06\t0.1\n')

    with pytest.raises(ValueError, match='The files of dataset ds-1 hold no variable to show'):
        tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)


def test_create_layer_for_qout_dataset_sets_a_value_layer_viz(tsm, tmp_path, files_dir):
    """The viz names the one feature document and, per variable, the url of its values file; there are no legend
    images because the browser draws the legend."""
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_QOUT, 'simple_Outlet.qout')
    dataset.file_collection_client.add_item.side_effect = lambda source: shutil.copytree(source, tmp_path / 'czml')
    dataset.file_collection.file_database_id = 'fdb'
    dataset.file_collection.id = 'fc'

    tsm.create_layer_for_dataset(dataset, 32612, session)

    viz = _viz_set_on(dataset)
    assert viz['type'] == 'czml'
    assert viz['url'] == ['fdb/fc/czml/ds-1.czml']
    assert viz['legend'] == []
    assert viz['origin'] is not None and len(viz['extent']) == 4
    (qstrm,) = viz['variables']
    assert qstrm['values'] == 'fdb/fc/czml/values/000_Qstrm_m3-s.json'
    assert (qstrm['name'], qstrm['label']) == ('Qstrm_m3-s', 'Streamflow')
    assert isinstance(qstrm['min'], float) and isinstance(qstrm['max'], float)
    json.dumps(viz)
