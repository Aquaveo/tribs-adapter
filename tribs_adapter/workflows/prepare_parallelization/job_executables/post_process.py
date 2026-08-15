#!/opt/tethys-python
"""
********************************************************************************
* Name: draw_graphs.py
* Author: ysun
* Created On: Aug 21, 2025
* Copyright: (c) Aquaveo 2025
********************************************************************************
"""
import os
import tempfile
import pandas as pd
from tribs_adapter.resources.dataset import Dataset
from tethysext.atcore.services.resource_workflows.decorators import workflow_step_job


@workflow_step_job
def main(
    resource_db_session, model_db_session, resource, workflow, step, gs_private_url, gs_public_url, resource_class,
    workflow_class, params_json, params_file, cmd_args, extra_args
):
    stream_dataset_name, stream_dataset_id = extra_args
    if stream_dataset_name == 'None':
        stream_dataset = None
    else:
        stream_dataset = resource_db_session.query(Dataset).get(stream_dataset_id)
        if not stream_dataset:
            raise RuntimeError(f"Dataset with id {stream_dataset_id} not found.")

    metis_dataset_id = workflow.get_attribute('metis_dataset_id')
    metis_dataset = resource_db_session.query(Dataset).get(metis_dataset_id)
    if not metis_dataset:
        raise RuntimeError(f"Dataset with id {metis_dataset_id} not found")  # TODO find a better error type
    metis_dataset_client = metis_dataset.file_collection_client

    metis_temp_dir = tempfile.TemporaryDirectory(prefix='tribs_parallel_plots_')
    plot_file_path, map_file_path, reach_file_path = '', '', ''
    for file in metis_dataset_client.files:
        found = True
        if file.endswith('procs_plot.csv'):
            plot_file_path = os.path.join(metis_temp_dir.name, file)
        elif file == 'voronoi_geo.meshb':
            map_file_path = os.path.join(metis_temp_dir.name, file)
        elif file.endswith('.reach'):
            reach_file_path = os.path.join(metis_temp_dir.name, file)
        else:
            found = False
        if found:
            metis_dataset_client.export_item(item=file, target=metis_temp_dir.name)
    if not plot_file_path:
        raise RuntimeError(f'The dataset {metis_dataset_id} doesn\'t have a plot file!')
    if not map_file_path:
        raise RuntimeError(f'The dataset {metis_dataset_id} doesn\'t have a voronoi file!')
    if not reach_file_path:
        raise RuntimeError(f'The dataset {metis_dataset_id} doesn\'t have a reach file!')

    # Draw the plot
    df = pd.read_csv(plot_file_path)
    plot_result = step.result.get_result_by_codename('output_plot')
    plot_result.reset()
    plot_result.plot_from_dataframe(df)

    # Draw the stream layer
    map_result = step.result.get_result_by_codename('output_map')
    viz = metis_dataset.get_attribute('viz')
    map_result.reset()
    if stream_dataset:
        stream_viz = stream_dataset.get_attribute('viz')
        map_result.add_wms_layer(
            endpoint=stream_viz['url'],
            layer_name=stream_viz['layer'],
            layer_title='Streams',
            layer_variable='stream',
            extent=stream_viz['extent'],
            geometry_attribute='the_geom',
            use_geoserver_legend=False,
            geoserver_legend_params={
                'legend_options': 'hideEmptyRules:true',
                'transparent': 'true'
            },
            visible=False
        )

    # Draw the partition graph
    map_result.add_wms_layer(
        endpoint=viz['url'],
        layer_name=viz['layer'],
        layer_title='Partition Graph',
        layer_variable='partition',
        extent=viz['extent'],
        selectable=True,
        geometry_attribute='the_geom',
        use_geoserver_legend=True,
        geoserver_legend_params={
            'legend_options': 'hideEmptyRules:true',
            'transparent': 'true'
        }
    )

    resource_db_session.commit()
