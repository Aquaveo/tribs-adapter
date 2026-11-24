from tribs_adapter.common.dataset_types import DatasetTypes, GltfOutputDatasetTypes
from tribs_adapter.common.file_to_dataset import FILE_TO_DATASET, VORONOI_OUTPUT_EXTENSIONS


def test_voronoi_output_extensions_follow_the_output_datasets():
    """The spatial output that is rendered as glTF (time-dynamic _d and time-integrated _i files) gets the _voi file."""
    assert VORONOI_OUTPUT_EXTENSIONS == ('_00d', '_00i')
    assert all(ext in FILE_TO_DATASET['OUTFILENAME']['file_extensions'] for ext in VORONOI_OUTPUT_EXTENSIONS)
    dataset_types = FILE_TO_DATASET['OUTFILENAME']['dataset_type']
    assert all(dataset_types[ext] in GltfOutputDatasetTypes for ext in VORONOI_OUTPUT_EXTENSIONS)
    assert '.pixel' not in VORONOI_OUTPUT_EXTENSIONS


def test_time_dynamic_output_is_a_dataset():
    outfilename = FILE_TO_DATASET['OUTFILENAME']
    assert outfilename['dataset_type']['_00d'] == DatasetTypes.TRIBS_OUT_TIME_DYNAMIC
    assert outfilename['dataset_name']['_00d'] == 'Time-Dynamic Variable Output'
