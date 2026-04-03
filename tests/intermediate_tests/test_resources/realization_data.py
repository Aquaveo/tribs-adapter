from tribs_adapter.common.dataset_types import DatasetTypes

expected_file_fields_salas = {
    "OUTFILENAME": {
        'fdps': [['salas.0000_00d', 'salas.0010_00d', 'salas.0700_00d'], ['salas.0000_00i', 'salas.0700_00i'],
                 ['salas0.pixel']],
        'path': 'Output/voronoi/salas',
    },
    "OUTHYDROFILENAME": {
        'fdps': [['salas0700_00.mrf'], ['salas.cntrl'], ['salas0700_00.rft'], ['salas_Outlet.qout']],
        'path': 'Output/hyd/salas',
    },
}

expected_datasets_salas = [
    {
        'name': 'Time-Dynamic Variable Output',
        'type': DatasetTypes.TRIBS_OUT_TIME_DYNAMIC,
        'description': 'Time-Dynamic Variable Output for Test Realization.'
    },
    {
        'name': 'Time-Integrated Variable Output',
        'type': DatasetTypes.TRIBS_OUT_TIME_INTEGRATED,
        'description': 'Time-Integrated Variable Output for Test Realization.'
    },
    {
        'name': 'Node Dynamic Output',
        'type': DatasetTypes.TRIBS_OUT_PIXEL,
        'description': 'Node Dynamic Output for Test Realization.'
    },
    {
        'name': 'Basin Averaged Hydrograph File',
        'type': DatasetTypes.TRIBS_OUT_MRF,
        'description': 'Basin Averaged Hydrograph File for Test Realization.'
    },
    {
        'name': 'Hydrograph Runoff Types File',
        'type': DatasetTypes.TRIBS_OUT_RFT,
        'description': 'Hydrograph Runoff Types File for Test Realization.'
    },
    {
        'name': 'Control File',
        'type': DatasetTypes.TRIBS_OUT_CNTRL,
        'description': 'Control File for Test Realization.'
    },
    {
        'name': 'Qout File',
        'type': DatasetTypes.TRIBS_OUT_QOUT,
        'description': 'Qout File for Test Realization.'
    },
]

expected_file_fields_examplebasin = {
    "OUTFILENAME": {
        'fdps': [['examplebasin.0010_00d', 'examplebasin.0000_00d'], ['examplebasin.0000_00i', 'examplebasin.0010_00i'],
                 ['examplebasin948.pixel', 'examplebasin72.pixel', 'examplebasin1156.pixel']],
        'path': 'Output/Fall1996/voronoi/examplebasin',
    },
    "OUTHYDROFILENAME": {
        'fdps': [['examplebasin0010_00.mrf'], ['examplebasin.cntrl'], ['examplebasin0010_00.rft'],
                 ['examplebasin_1166.qout', 'examplebasin_Outlet.qout', 'examplebasin_1148.qout']],
        'path': 'Output/Fall1996/hyd/examplebasin',
    },
}

expected_datasets_examplebasin = [
    {
        'name': 'Time-Dynamic Variable Output',
        'type': DatasetTypes.TRIBS_OUT_TIME_DYNAMIC,
        'description': 'Time-Dynamic Variable Output for Test Realization.'
    },
    {
        'name': 'Time-Integrated Variable Output',
        'type': DatasetTypes.TRIBS_OUT_TIME_INTEGRATED,
        'description': 'Time-Integrated Variable Output for Test Realization.'
    },
    {
        'name': 'Node Dynamic Output',
        'type': DatasetTypes.TRIBS_OUT_PIXEL,
        'description': 'Node Dynamic Output for Test Realization.'
    },
    {
        'name': 'Basin Averaged Hydrograph File',
        'type': DatasetTypes.TRIBS_OUT_MRF,
        'description': 'Basin Averaged Hydrograph File for Test Realization.'
    },
    {
        'name': 'Hydrograph Runoff Types File',
        'type': DatasetTypes.TRIBS_OUT_RFT,
        'description': 'Hydrograph Runoff Types File for Test Realization.'
    },
    {
        'name': 'Control File',
        'type': DatasetTypes.TRIBS_OUT_CNTRL,
        'description': 'Control File for Test Realization.'
    },
    {
        'name': 'Qout File',
        'type': DatasetTypes.TRIBS_OUT_QOUT,
        'description': 'Qout File for Test Realization.'
    },
]

expected_file_fields_salas_issues = {
    "OUTFILENAME": {
        'fdps': [],
        'path': 'Output/voronoi/salas',
    },
    "OUTHYDROFILENAME": {
        'fdps': [],
        'path': 'Output/hyd/salas',
    },
}

expected_datasets_salas_issues = []
