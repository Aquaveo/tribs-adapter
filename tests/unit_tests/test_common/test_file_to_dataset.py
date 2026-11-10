from tribs_adapter.common.dataset_types import DatasetTypes, GltfOutputDatasetTypes
from tribs_adapter.common.file_to_dataset import FILE_TO_DATASET, VORONOI_OUTPUT_EXTENSIONS


def test_voronoi_output_extensions_follow_the_output_datasets():
    """Only the spatial output that is rendered as glTF (time-integrated _i files) gets the _voi file."""
    assert VORONOI_OUTPUT_EXTENSIONS == ('_00i',)
    assert all(ext in FILE_TO_DATASET['OUTFILENAME']['file_extensions'] for ext in VORONOI_OUTPUT_EXTENSIONS)
    dataset_types = FILE_TO_DATASET['OUTFILENAME']['dataset_type']
    assert all(dataset_types[ext] in GltfOutputDatasetTypes for ext in VORONOI_OUTPUT_EXTENSIONS)
    # The time-dynamic output is no longer a dataset at all
    assert DatasetTypes.TRIBS_OUT_TIME_DYNAMIC not in FILE_TO_DATASET['OUTFILENAME']['dataset_type'].values()
    assert '.pixel' not in VORONOI_OUTPUT_EXTENSIONS
