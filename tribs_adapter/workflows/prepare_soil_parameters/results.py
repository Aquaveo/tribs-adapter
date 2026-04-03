from tethysext.atcore.models.resource_workflow_results import (
    SpatialWorkflowResult, DatasetWorkflowResult, PlotWorkflowResult
)


def build_rosetta3_results_tabs(geoserver_name, map_manager, spatial_manager):
    """
    Define the tabs for the results step.

    Returns:
        list<ResourceWorkflowResult>: Results definitions.
    """
    soil_grid_map_result = SpatialWorkflowResult(
        name='Soil Grids',
        codename='soil_grids',
        description='View generated tRIBS soil grids.',
        order=10,
        options={
            'layer_group_title': 'Soil Grids',
            'layer_group_control': 'checkbox'
        },
        geoserver_name=geoserver_name,
        map_manager=map_manager,
        spatial_manager=spatial_manager
    )

    texture_classes_result = DatasetWorkflowResult(
        name='Texture Classes',
        codename='texture_classes',
        description='Table of texture classes in .soi file.',
        order=20,
        options={
            'data_table_kwargs': {
                'paging': True,
            },
            'no_dataset_message': 'No texture classes found.'
        },
    )
    return [soil_grid_map_result, texture_classes_result]


def build_results_tabs(geoserver_name, map_manager, spatial_manager):
    """
    Define the tabs for the results step.

    Returns:
        list<ResourceWorkflowResult>: Results definitions.
    """
    generic_map_result = SpatialWorkflowResult(
        name='Generic Map',
        codename='generic_map',
        description='Generic data at each point location specified.',
        order=10,
        options={
            'layer_group_title': 'Points',
            'layer_group_control': 'checkbox'
        },
        geoserver_name=geoserver_name,
        map_manager=map_manager,
        spatial_manager=spatial_manager
    )

    generic_table_result = DatasetWorkflowResult(
        name='Generic Table',
        codename='generic_table',
        description='Generic table dataset result.',
        order=20,
        options={
            'data_table_kwargs': {
                'paging': True,
            },
            'no_dataset_message': 'No peak flows found.'
        },
    )

    generic_plot_result = PlotWorkflowResult(
        name='Generic Plot',
        codename='generic_plot',
        description='Generic plot dataset result.',
        order=30,
        options={
            'renderer': 'plotly',
            'axes': [],
            'plot_type': 'lines',
            'axis_labels': ['x', 'y'],
            'line_shape': 'linear',
            'x_axis_type': 'datetime',
            'no_dataset_message': 'No dataset found.'
        },
    )

    return [generic_map_result, generic_table_result, generic_plot_result]
