from tribs_adapter.tribs import get_tribs_path


def test_get_tribs_path_parallel():
    path = get_tribs_path(parallel=True)
    assert path.exists()


def test_get_tribs_path_serial():
    path = get_tribs_path(parallel=False)
    assert path.exists()
