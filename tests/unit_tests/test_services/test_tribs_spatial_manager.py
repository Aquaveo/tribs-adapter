import datetime
import json
import os

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
    assert parse(None) == [8081, 8082, 8083, 8084]
    assert parse('not json') == [8081, 8082, 8083, 8084]
    assert parse('["a"]') == [8081, 8082, 8083, 8084]


def _file_entry(variable, hours, kind='d', legend=True):
    stamp = f'{int(hours):04d}_00{kind}' if hours is not None else None
    name = f'abc-salas_salas-{stamp}_{variable}' if stamp else 'abc-salas'
    return dict(
        variable=variable, output_file=f'/out/salas.{stamp}' if stamp else None, hours=hours, kind=kind,
        gltf=f'/tmp/x/gltf/{name}.glb', legend=f'/tmp/x/gltf/{name}_legend.png' if legend else None,
    )


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
        name='Elevation', start=None, end=None, step_hours=None,
        timesteps=[dict(hours=None, time=None, url='fdb/fc/gltf/abc-salas.glb',
                        legend='fdb/fc/gltf/abc-salas_legend.png')],
    )]
    assert TribsSpatialManager._build_gltf_variables([], URL_DIR) == []


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
    assert s['timesteps'][0]['legend'] == 'fdb/fc/gltf/abc-salas_salas-0000_00d_S_legend.png'
    assert all(os.path.exists(tmp_path / os.path.basename(t['url'])) for t in s['timesteps'])
