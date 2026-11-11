import datetime
import json
import os
import shutil
from unittest import mock

import pytest

from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.services import tribs_spatial_manager as tsm_module
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager


def _touch(path):
    with open(path, 'w') as f:
        f.write('')
    return str(path)


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
    """End to end over the tin fixture: five time-dynamic files, 10 hours apart."""
    from tribs_adapter.io.tribs_mesh import tRIBSMeshViz

    layers_dir = files_dir / 'spatial_manager' / 'layers' / 'tin'
    output_files = sorted(str(p) for p in (layers_dir / 'output').glob('salas.*_00d'))
    assert len(output_files) == 5
    tmv = tRIBSMeshViz(mesh_basename=layers_dir / 'salas', mesh_epsg=32613, output_files=output_files)
    meta = tmv.to_gltf(str(tmp_path / 'abc-salas'), output_variables=['S'], generate_legend=True)

    variables = TribsSpatialManager._build_gltf_variables(
        meta['files'], URL_DIR, start_date=datetime.datetime(2004, 6, 1), fallback_step_hours=168
    )
    assert len(variables) == 1
    s = variables[0]
    assert s['name'] == 'S'
    assert [t['hours'] for t in s['timesteps']] == [0, 10, 20, 30, 40]
    assert s['step_hours'] == 10
    assert s['start'] == '2004-06-01T00:00:00Z'
    assert s['end'] == '2004-06-02T16:00:00Z'
    assert s['timesteps'][0]['url'] == 'fdb/fc/gltf/abc-salas_salas-0000_00d_S.glb'
    # One legend per variable, scaled over all time steps and shared by every time step
    assert all(t['legend'] == 'fdb/fc/gltf/abc-salas_S_legend.png' for t in s['timesteps'])
    assert all(os.path.exists(tmp_path / os.path.basename(t['url'])) for t in s['timesteps'])


# --- create_layer_for_dataset: glTF output datasets -----------------------------------------------------------------
# The branch wires the linked realization's node file dataset, STARTDATE and SPOPINTRVL into the glTF viz. The output
# writer (create_tribs_tin_layer, covered by the intermediate tests on real files) is replaced by a spy; _build_gltf_viz
# runs for real so the assertions are on the viz the dataset ends up with.


@pytest.fixture
def tsm():
    return TribsSpatialManager(mock.MagicMock(), reload_ports=[8080])


def _output_dataset(path, dataset_type=DatasetTypes.TRIBS_OUT_TIME_INTEGRATED, start_date=None, spopintrvl=6,
                    linked=True):
    dataset = mock.MagicMock()
    dataset.id = 'ds-1'
    dataset.dataset_type = dataset_type
    dataset.file_collection_client.path = str(path)
    dataset.file_collection.file_database_id = 'fdb'
    dataset.file_collection.id = 'fc'
    dataset.linked_realizations = []
    if linked:
        realization = mock.MagicMock()
        realization.id = 'real-1'
        realization.input_file.files_and_pathnames.mesh_generation.INPUTDATAFILE.resource_id = 'node-ds'
        realization.input_file.run_parameters.time_variables.STARTDATE = start_date
        realization.input_file.run_parameters.time_variables.SPOPINTRVL = spopintrvl
        dataset.linked_realizations = [realization]
    return dataset


def _session_with_node_file_dataset():
    node_file_dataset = mock.MagicMock()
    session = mock.MagicMock()
    session.query.return_value.get.return_value = node_file_dataset
    return session, node_file_dataset


def _gltf_meta(*entries):
    return dict(gltfs=[], origin=[-105.0, 40.0, 1500.0], extents=[-105.1, 39.9, -104.9, 40.1], files=list(entries))


def _patch_tin_layer_writer(mocker, *entries):
    """Replace create_tribs_tin_layer with a spy that writes the (empty) files its metadata names into the output
    dataset's ``gltf`` directory, as the real writer does, and returns that metadata."""
    meta = _gltf_meta(*entries)

    def write(node_file_dataset, mesh_epsg, output_dataset=None, output_variables=None, variable_kind=None):
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
        node_file_dataset, mesh_epsg=26913, output_dataset=dataset, variable_kind='integrated'
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


def test_create_layer_for_legacy_time_dynamic_dataset_has_no_variable_table(tsm, tmp_path, mocker):
    dataset = _output_dataset(tmp_path, dataset_type=DatasetTypes.TRIBS_OUT_TIME_DYNAMIC,
                              start_date=datetime.datetime(2004, 6, 1))
    session, node_file_dataset = _session_with_node_file_dataset()
    create = _patch_tin_layer_writer(mocker, _file_entry('Nwt', 0, kind='d'))

    tsm.create_layer_for_dataset(dataset, 26913, session)

    create.assert_called_once_with(node_file_dataset, mesh_epsg=26913, output_dataset=dataset, variable_kind=None)
    (nwt,) = _viz_set_on(dataset)['variables']
    assert (nwt['name'], nwt['label'], nwt['units'], nwt['tier']) == ('Nwt', 'Nwt', None, None)


def test_create_layer_for_output_dataset_requires_a_linked_realization(tsm, tmp_path, mocker):
    dataset = _output_dataset(tmp_path, linked=False)
    session, _ = _session_with_node_file_dataset()
    create = mocker.patch.object(TribsSpatialManager, 'create_tribs_tin_layer')

    with pytest.raises(ValueError, match='requires a linked Realization.*ds-1'):
        tsm.create_layer_for_dataset(dataset, 26913, session)

    create.assert_not_called()
    dataset.set_attribute.assert_not_called()
    session.commit.assert_not_called()


# --- create_tribs_czml_layer: per-variable metadata ------------------------------------------------------------------
# Real mrf/qout/pixel files from the czml_converters fixtures; the CZML generators are spies, so the tests check which
# variables become layers, how each is described, and the legend factor each generator is given.

SIMPLE_FILES = os.path.join('czml_converters', 'simple_files')


def _czml_dataset(path, files_dir, dataset_type, data_file):
    shutil.copy(files_dir / SIMPLE_FILES / data_file, path / data_file)
    dataset = mock.MagicMock()
    dataset.id = 'ds-1'
    dataset.dataset_type = dataset_type
    dataset.file_collection_client.path = str(path)
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


def _generated(spy):
    """(variable, czml file name, legend_factor) of each CZML the spy was asked to write, in order."""
    return [(c.args[7], os.path.basename(c.args[5]), c.kwargs['legend_factor']) for c in spy.call_args_list]


def test_create_tribs_czml_layer_for_mrf_offers_the_sheet_variables(tsm, tmp_path, files_dir, mocker):
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_MRF, 'simple.mrf')
    (tmp_path / 'czml').mkdir()  # a previous visualization
    generate = mocker.patch.object(tsm_module, 'generate_czml_for_mrf_and_rft_files')

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
    # One CZML per offered variable, legend ticks in display units
    assert _generated(generate) == [
        ('MAP', 'ds-1-MAP.czml', 1.0), ('MSMRt', 'ds-1-MSMRt.czml', 100.0), ('MDGW', 'ds-1-MDGW.czml', 0.001),
        ('Srf', 'ds-1-Srf.czml', 1.0), ('MSM100', 'ds-1-MSM100.czml', 100.0), ('MSMU', 'ds-1-MSMU.czml', 100.0),
    ]
    assert all(c.kwargs['srid'] == 32612 and c.args[6] == 'ds-1' for c in generate.call_args_list)
    # The old czml directory is replaced and the extent comes from the node file
    dataset.file_collection_client.delete_item.assert_called_once_with('czml')
    dataset.file_collection_client.add_item.assert_called_once()
    assert dataset.file_collection_client.add_item.call_args.args[0].endswith('czml')
    assert meta['origin'] is not None and len(meta['extents']) == 4
    json.dumps(meta)


def test_create_tribs_czml_layer_for_qout_keeps_the_unit_suffix_in_the_layer_name(tsm, tmp_path, files_dir, mocker):
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_QOUT, 'simple_Outlet.qout')
    generate = mocker.patch.object(tsm_module, 'generate_czml_for_qout_files')

    meta = tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)

    # Hlev is hidden by the table; the layer keeps the file's column name, the label and units come from the table
    (qstrm,) = meta['variables']
    assert (qstrm['name'], qstrm['label'], qstrm['units'], qstrm['tier'], qstrm['factor']) == \
        ('Qstrm_m3-s', 'Streamflow', 'm³/s', 'priority', 1.0)
    assert _generated(generate) == [('Qstrm_m3-s', 'ds-1-Qstrm_m3-s.czml', 1.0)]
    dataset.file_collection_client.delete_item.assert_not_called()


def test_create_tribs_czml_layer_for_pixel_keeps_every_variable_with_its_unit_token(tsm, tmp_path, files_dir, mocker):
    dataset, session = _czml_dataset(tmp_path, files_dir, DatasetTypes.TRIBS_OUT_PIXEL, 'simple.pixel')
    generate = mocker.patch.object(tsm_module, 'generate_czml_for_pixel_files')

    meta = tsm.create_tribs_czml_layer(dataset, session, os.listdir(tmp_path), 32612)

    # Pixel variables are not in the sheet: all stay visible, named by the header, with the unit token translated
    assert [v['name'] for v in meta['variables']] == ['Nwt_mm', 'Nf_mm', 'Nt_mm', 'Mu_mm', 'Mi_mm']
    assert all((v['tier'], v['factor'], v['description']) == (None, 1.0, '') for v in meta['variables'])
    nwt = meta['variables'][0]
    assert (nwt['label'], nwt['units']) == ('Nwt', 'mm')
    assert [g[0] for g in _generated(generate)] == ['Nwt_mm', 'Nf_mm', 'Nt_mm', 'Mu_mm', 'Mi_mm']
    assert all(g[2] == 1.0 for g in _generated(generate))
