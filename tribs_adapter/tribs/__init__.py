from pathlib import Path


def get_tribs_path(parallel=True) -> Path:
    """Get the path to the tRIBS executable that is shipped with tribs-adapter.

    Args:
        parallel (bool, optional): Return the path to the parallel version of tRIBS. Defaults to True.
    """
    tribs_dir = Path(__file__).resolve().parent
    if not parallel:
        return tribs_dir / 'tRIBS'
    return tribs_dir / 'tRIBSpar'
