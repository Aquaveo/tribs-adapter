"""
********************************************************************************
* Name: read_write_soil_file.py
* Author: EJones
* Created On: April 23, 2024
* Copyright: (c) Aquaveo 2024
********************************************************************************
"""
import os
from pytRIBS.classes import Soil
import pandas as pd
from tribs_adapter.resources.dataset import Dataset


def read_soil_data_to_df(request, session, resource, work_step, *args, **kwargs):
    """
    Read the soil data from the file and return as a pandas DataFrame.
    """
    # Post process the dataset
    soil = Soil()

    soil_table_dataset_id = work_step.workflow.get_attribute('soil_table_dataset_id')
    if soil_table_dataset_id is None:
        return None

    dataset = session.query(Dataset).get(soil_table_dataset_id)
    client = dataset.file_collection_client

    soil_table_file = 'soils.sdt'
    file_path = os.path.join(client.path, soil_table_file)
    data = soil.read_soil_table(textures=True, file_path=file_path)

    nodata = '9999.99'
    data_dict = []
    for texture_row in data:
        as_value = 0.0 if texture_row['As'] == 'undefined' or texture_row['As'] == nodata else texture_row['As']
        au_value = 0.0 if texture_row['Au'] == 'undefined' or texture_row['Au'] == nodata else texture_row['Au']
        n_value = 0.0 if texture_row['n'] == 'undefined' or texture_row['n'] == nodata else texture_row['n']
        ks_value = 0.0 if texture_row['ks'] == 'undefined' or texture_row['ks'] == nodata else texture_row['ks']
        cs_value = 0.0 if texture_row['Cs'] == 'undefined' or texture_row['Cs'] == nodata else texture_row['Cs']

        data_dict.append({
            'Soil Texture Class': texture_row['Texture'],
            'Saturated Anisotropy Ratio (As)': as_value,
            'Unsaturated Anisotropy Ratio (Au)': au_value,
            'Porosity (n)': n_value,
            'Volumetric Heat Conductivity (ks) (J/msK)': ks_value,
            'Soil Heat Capacity (Cs) (J/m^3K)': cs_value,
        })

    # Save dataset as new pandas DataFrame
    dataset = pd.DataFrame(data=data_dict)
    return dataset
