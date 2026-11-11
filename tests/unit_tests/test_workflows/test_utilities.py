import os
import subprocess
from unittest import mock

import pytest

from tribs_adapter.workflows import utilities


def _fake_mpi_runtime(root, with_lib=True):
    """Lay out ``<root>/bin/mpirun`` (and ``<root>/lib``) like an MPI install; return the mpirun path."""
    (root / 'bin').mkdir(parents=True)
    mpirun = root / 'bin' / 'mpirun'
    mpirun.write_text('')
    if with_lib:
        (root / 'lib').mkdir()
    return mpirun


def test_get_mpi_launcher_finds_mpirun_on_the_path(tmp_path, monkeypatch):
    mpirun = _fake_mpi_runtime(tmp_path / 'openmpi')
    monkeypatch.setattr(utilities.shutil, 'which', lambda name: str(mpirun) if name == 'mpirun' else None)
    monkeypatch.delenv('LD_LIBRARY_PATH', raising=False)

    found, env = utilities.get_mpi_launcher()

    assert found == str(mpirun)
    assert env['LD_LIBRARY_PATH'] == str((tmp_path / 'openmpi' / 'lib').resolve())
    assert 'LD_LIBRARY_PATH' not in os.environ  # the caller's environment is copied, not changed


def test_get_mpi_launcher_prepends_the_runtime_lib_dir(tmp_path, monkeypatch):
    mpirun = _fake_mpi_runtime(tmp_path / 'openmpi')
    monkeypatch.setattr(utilities.shutil, 'which', lambda name: str(mpirun))
    monkeypatch.setenv('LD_LIBRARY_PATH', '/usr/local/lib')

    _, env = utilities.get_mpi_launcher()

    lib_dir = str((tmp_path / 'openmpi' / 'lib').resolve())
    assert env['LD_LIBRARY_PATH'] == os.pathsep.join([lib_dir, '/usr/local/lib'])


def test_get_mpi_launcher_leaves_ld_library_path_without_a_lib_dir(tmp_path, monkeypatch):
    mpirun = _fake_mpi_runtime(tmp_path / 'usr', with_lib=False)
    monkeypatch.setattr(utilities.shutil, 'which', lambda name: str(mpirun))
    monkeypatch.setenv('LD_LIBRARY_PATH', '/usr/local/lib')

    found, env = utilities.get_mpi_launcher()

    assert found == str(mpirun)
    assert env['LD_LIBRARY_PATH'] == '/usr/local/lib'


def test_get_mpi_launcher_falls_back_to_the_interpreter_dir(tmp_path, monkeypatch):
    """Condor jobs may run without a usable PATH: mpirun next to the Python interpreter (same conda env) is used."""
    mpirun = _fake_mpi_runtime(tmp_path / 'env')
    monkeypatch.setattr(utilities.shutil, 'which', lambda name: None)
    monkeypatch.setattr(utilities.sys, 'executable', str(tmp_path / 'env' / 'bin' / 'python'))
    monkeypatch.delenv('LD_LIBRARY_PATH', raising=False)

    found, env = utilities.get_mpi_launcher()

    assert found == str(mpirun)
    assert env['LD_LIBRARY_PATH'] == str((tmp_path / 'env' / 'lib').resolve())


def test_get_mpi_launcher_raises_when_mpirun_is_missing(tmp_path, monkeypatch):
    (tmp_path / 'env' / 'bin').mkdir(parents=True)  # an interpreter directory without mpirun
    monkeypatch.setattr(utilities.shutil, 'which', lambda name: None)
    monkeypatch.setattr(utilities.sys, 'executable', str(tmp_path / 'env' / 'bin' / 'python'))

    with pytest.raises(FileNotFoundError, match='mpirun was not found'):
        utilities.get_mpi_launcher()


def test_run_tribs_launches_with_the_resolved_mpirun_and_environment(tmp_path, monkeypatch):
    mpi_env = {'PATH': '/opt/env/bin', 'LD_LIBRARY_PATH': '/opt/env/lib'}
    monkeypatch.setattr(utilities, 'get_mpi_launcher', lambda: ('/opt/env/bin/mpirun', mpi_env))
    run = mock.Mock(return_value=subprocess.CompletedProcess(['mpirun'], 0, stdout='done\n', stderr=''))
    monkeypatch.setattr(utilities.subprocess, 'run', run)

    result = utilities.run_tribs(str(tmp_path), 'salas.in', tribs_executable='tRIBSpar', silent=True)

    run.assert_called_once_with(
        ['/opt/env/bin/mpirun', os.path.join(str(tmp_path), 'tRIBSpar'), 'salas.in'],
        capture_output=True, universal_newlines=True, cwd=str(tmp_path), env=mpi_env,
    )
    assert result.returncode == 0


def test_run_tribs_fails_before_launching_when_mpirun_is_missing(tmp_path, monkeypatch):
    def no_launcher():
        raise FileNotFoundError('mpirun was not found')

    monkeypatch.setattr(utilities, 'get_mpi_launcher', no_launcher)
    run = mock.Mock()
    monkeypatch.setattr(utilities.subprocess, 'run', run)

    with pytest.raises(FileNotFoundError):
        utilities.run_tribs(str(tmp_path), 'salas.in', tribs_executable='tRIBSpar')
    run.assert_not_called()
