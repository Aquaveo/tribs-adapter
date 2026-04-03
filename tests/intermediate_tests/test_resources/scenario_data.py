from tribs_adapter.common.dataset_types import DatasetTypes

expected_file_fields_salas = {
    "CHANNELWIDTHFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "OUTVIZFILENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "DEMFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "LANDMAPNAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.lan',
        'file_collection_paths': ['salas.lan']
    },
    "LUGRID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "LANDTABLENAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.ldt',
        'file_collection_paths': ['salas.ldt']
    },
    "SOILTABLENAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.sdt',
        'file_collection_paths': ['salas.sdt']
    },
    "SCGRID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "GWATERFILE": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.iwt',
        'file_collection_paths': ['salas.iwt']
    },
    "RAINFILE": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Rain/p',
        'file_collection_paths': ['p0630200417.txt', 'p0531200418.txt']
    },
    "SOILMAPNAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.soi',
        'file_collection_paths': ['salas.soi']
    },
    "BEDROCKFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Input/salas.brd',
        'file_collection_paths': []
    },
    "HYDROMETBASENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Weather/weatherField',
        'file_collection_paths': []
    },
    "HYDROMETSTATIONS": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Weather/weatherC1601_2004.sdf',
        'file_collection_paths': ['weatherC1601_2004.sdf', 'weatherC1601_2004.mdf']
    },
    "GAUGEBASENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "HYDROMETGRID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Weather/',
        'file_collection_paths': []
    },
    "HYDROMETCONVERT": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Weather/',
        'file_collection_paths': []
    },
    "GAUGECONVERT": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "GAUGESTATIONS": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Rain/rainGauge.sdf',
        'file_collection_paths': []
    },
    "INPUTDATAFILE": {
        'has_resource_id':
            True,
        'has_file_collection_id':
            True,
        'path':
            'Output/voronoi/salas',
        'file_collection_paths': [
            'salas.z', 'salas_voi', 'salas_width', 'salas.tri', 'salas_area', 'salas.nodes', 'salas_reach',
            'salas.edges'
        ]
    },
    "ARCINFOFILENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "POINTFILENAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.points',
        'file_collection_paths': ['salas.points']
    },
    "NODEOUTPUTLIST": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/Nodes/pNodes.dat',
        'file_collection_paths': ['pNodes.dat']
    },
    "OUTLETNODELIST": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/Nodes/oNodes.dat',
        'file_collection_paths': ['oNodes.dat']
    },
    "HYDRONODELIST": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/Nodes/hNodes.dat',
        'file_collection_paths': ['hNodes.dat']
    },
    "RESTARTFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "RESTARTDIR": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "GRAPHFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "WEATHERTABLENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Input/pramsWG.T',
        'file_collection_paths': []
    },
    "FORECASTFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "OUTFILENAME": {
        'path': 'Output/voronoi/salas',
        'file_database_paths': []
    },
    "OUTHYDROFILENAME": {
        'path': 'Output/hyd/salas',
        'file_database_paths': []
    },
    "RESPOLYGONID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "RESDATA": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
}

expected_datasets_salas = [
    {
        'name': 'Groundwater Grid',
        'type': DatasetTypes.RASTER_CONT_ASCII,
        'description': 'Groundwater Grid for Test Scenario.'
    },
    {
        'name': 'Hydromet Station Data',
        'type': DatasetTypes.TRIBS_SDF_HYDROMET_STATION,
        'description': 'Hydromet Station Data for Test Scenario.'
    },
    {
        'name': 'Interior Node Output List',
        'type': DatasetTypes.TRIBS_NODE_LIST,
        'description': 'Interior Node Output List for Test Scenario.'
    },
    {
        'name': 'Land Use Grid',
        'type': DatasetTypes.RASTER_DISC_ASCII,
        'description': 'Land Use Grid for Test Scenario.'
    },
    {
        'name': 'Land Use Reclassification Table',
        'type': DatasetTypes.TRIBS_TABLE_LANDUSE,
        'description': 'Land Use Reclassification Table for Test Scenario.'
    },
    {
        'name': 'Node Output List',
        'type': DatasetTypes.TRIBS_NODE_LIST,
        'description': 'Node Output List for Test Scenario.'
    },
    {
        'name': 'Point File',
        'type': DatasetTypes.TRIBS_POINTS,
        'description': 'Point File for Test Scenario.'
    },
    {
        'name': 'Runtime Node Output List',
        'type': DatasetTypes.TRIBS_NODE_LIST,
        'description': 'Runtime Node Output List for Test Scenario.'
    },
    {
        'name': 'Soil Grid',
        'type': DatasetTypes.RASTER_DISC_ASCII,
        'description': 'Soil Grid for Test Scenario.'
    },
    {
        'name': 'Soil Reclassification Table',
        'type': DatasetTypes.TRIBS_TABLE_SOIL,
        'description': 'Soil Reclassification Table for Test Scenario.'
    },
    {
        'name': 'TIN',
        'type': DatasetTypes.TRIBS_TIN,
        'description': 'TIN for Test Scenario.'
    },
    {
        'name': 'Radar Rainfall Grids',
        'type': DatasetTypes.RASTER_CONT_ASCII_TIMESERIES,
        'description': 'Radar Rainfall Grids for Test Scenario.'
    },
]

expected_file_fields_examplebasin = {
    "CHANNELWIDTHFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "OUTVIZFILENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "DEMFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "LANDMAPNAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/examplebasin.lan',
        'file_collection_paths': ['examplebasin.lan']
    },
    "LUGRID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "LANDTABLENAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/examplebasin.ldt',
        'file_collection_paths': ['examplebasin.ldt']
    },
    "SOILTABLENAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/examplebasin.sdt',
        'file_collection_paths': ['examplebasin.sdt']
    },
    "SCGRID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "GWATERFILE": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/examplebasingw.iwt',
        'file_collection_paths': ['examplebasingw.iwt']
    },
    "RAINFILE": {
        'has_resource_id':
            True,
        'has_file_collection_id':
            True,
        'path':
            'Rain/Fall1996/p',
        'file_collection_paths': [
            'p0920199603.txt',
            'p0920199609.txt',
            'p0920199607.txt',
            'p0920199612.txt',
            'p0920199601.txt',
            'p0920199611.txt',
            'p0920199610.txt',
            'p0920199608.txt',
            'p0920199600.txt',
            'p0920199602.txt',
            'p0920199605.txt',
            'p0920199604.txt',
            'p0920199606.txt',
        ]
    },
    "SOILMAPNAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/examplebasin.soi',
        'file_collection_paths': ['examplebasin.soi']
    },
    "BEDROCKFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Input/',
        'file_collection_paths': []
    },
    "HYDROMETBASENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Weather/Fall1996/bfFall1996_dmp.mdf',
        'file_collection_paths': []
    },
    "HYDROMETSTATIONS": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Weather/Fall1996/bfFall1996_dmp.sdf',
        'file_collection_paths': ['bfFall1996_dmp.sdf', 'bfFall1996_dmp.mdf']
    },
    "GAUGEBASENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "HYDROMETGRID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "HYDROMETCONVERT": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "GAUGECONVERT": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "GAUGESTATIONS": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "INPUTDATAFILE": {
        'has_resource_id':
            True,
        'has_file_collection_id':
            True,
        'path':
            'Output/Fall1996/voronoi/examplebasin',
        'file_collection_paths': [
            'examplebasin_area', 'examplebasin.edges', 'examplebasin.nodes', 'examplebasin.z', 'examplebasin_reach',
            'examplebasin.tri', 'examplebasin_voi', 'examplebasin_width'
        ]
    },
    "ARCINFOFILENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Input/ArcFiles/examplebasin',
        'file_collection_paths': []
    },
    "POINTFILENAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/PointFiles/examplebasin.points',
        'file_collection_paths': ['examplebasin.points']
    },
    "NODEOUTPUTLIST": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/Nodes/pNodes.dat',
        'file_collection_paths': ['pNodes.dat']
    },
    "OUTLETNODELIST": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/Nodes/oNodes.dat',
        'file_collection_paths': ['oNodes.dat']
    },
    "HYDRONODELIST": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/Nodes/hNodes.dat',
        'file_collection_paths': ['hNodes.dat']
    },
    "RESTARTFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "RESTARTDIR": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "GRAPHFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "WEATHERTABLENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "FORECASTFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "OUTFILENAME": {
        'path': 'Output/Fall1996/voronoi/examplebasin',
        'file_database_paths': []
    },
    "OUTHYDROFILENAME": {
        'path': 'Output/Fall1996/hyd/examplebasin',
        'file_database_paths': []
    },
    "RESPOLYGONID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "RESDATA": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
}

expected_datasets_examplebasin = [
    {
        'name': 'Groundwater Grid',
        'type': DatasetTypes.RASTER_CONT_ASCII,
        'description': 'Groundwater Grid for Test Scenario.'
    },
    {
        'name': 'Hydromet Station Data',
        'type': DatasetTypes.TRIBS_SDF_HYDROMET_STATION,
        'description': 'Hydromet Station Data for Test Scenario.'
    },
    {
        'name': 'Interior Node Output List',
        'type': DatasetTypes.TRIBS_NODE_LIST,
        'description': 'Interior Node Output List for Test Scenario.'
    },
    {
        'name': 'Land Use Grid',
        'type': DatasetTypes.RASTER_DISC_ASCII,
        'description': 'Land Use Grid for Test Scenario.'
    },
    {
        'name': 'Land Use Reclassification Table',
        'type': DatasetTypes.TRIBS_TABLE_LANDUSE,
        'description': 'Land Use Reclassification Table for Test Scenario.'
    },
    {
        'name': 'Node Output List',
        'type': DatasetTypes.TRIBS_NODE_LIST,
        'description': 'Node Output List for Test Scenario.'
    },
    {
        'name': 'Point File',
        'type': DatasetTypes.TRIBS_POINTS,
        'description': 'Point File for Test Scenario.'
    },
    {
        'name': 'Runtime Node Output List',
        'type': DatasetTypes.TRIBS_NODE_LIST,
        'description': 'Runtime Node Output List for Test Scenario.'
    },
    {
        'name': 'Soil Grid',
        'type': DatasetTypes.RASTER_DISC_ASCII,
        'description': 'Soil Grid for Test Scenario.'
    },
    {
        'name': 'Soil Reclassification Table',
        'type': DatasetTypes.TRIBS_TABLE_SOIL,
        'description': 'Soil Reclassification Table for Test Scenario.'
    },
    {
        'name': 'Radar Rainfall Grids',
        'type': DatasetTypes.RASTER_CONT_ASCII_TIMESERIES,
        'description': 'Radar Rainfall Grids for Test Scenario.'
    },
    {
        'name': 'TIN',
        'type': DatasetTypes.TRIBS_TIN,
        'description': 'TIN for Test Scenario.'
    },
]

expected_file_fields_salas_issues = {
    "CHANNELWIDTHFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "OUTVIZFILENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "DEMFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "LANDMAPNAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Input/salas.foo',
        'file_collection_paths': []
    },
    "LUGRID": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'LandCover/salas.gdf',
        'file_collection_paths': ['salas.ltf', 'salas.lvh', 'salas.gdf', 'salas.lal']
    },
    "LANDTABLENAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.ldt',
        'file_collection_paths': ['salas.ldt']
    },
    "SOILTABLENAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.sdt',
        'file_collection_paths': ['salas.sdt']
    },
    "SCGRID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "GWATERFILE": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.iwt',
        'file_collection_paths': ['salas.iwt']
    },
    "RAINFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Rain/p',
        'file_collection_paths': []
    },
    "SOILMAPNAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.soi',
        'file_collection_paths': ['salas.soi']
    },
    "BEDROCKFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Input/salas.brd',
        'file_collection_paths': []
    },
    "HYDROMETBASENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Weather/weatherField',
        'file_collection_paths': []
    },
    "HYDROMETSTATIONS": {
        'has_resource_id':
            True,
        'has_file_collection_id':
            True,
        'path':
            'Weather/weatherC1601_2004.sdf',
        'file_collection_paths': [
            'weatherC1601_2004.sdf', 'weatherC1601_2004.mdf', 'Nested/weatherCNested1801_2004.mdf'
        ]
    },
    "GAUGEBASENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "HYDROMETGRID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Weather/',
        'file_collection_paths': []
    },
    "HYDROMETCONVERT": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Weather/',
        'file_collection_paths': []
    },
    "GAUGECONVERT": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "GAUGESTATIONS": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Rain/rainGauge.sdf',
        'file_collection_paths': []
    },
    "INPUTDATAFILE": {
        'has_resource_id':
            True,
        'has_file_collection_id':
            True,
        'path':
            'Output/voronoi/salas',
        'file_collection_paths': [
            'salas.z', 'salas_voi', 'salas_width', 'salas.tri', 'salas_area', 'salas.nodes', 'salas_reach',
            'salas.edges'
        ]
    },
    "ARCINFOFILENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "POINTFILENAME": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/salas.points',
        'file_collection_paths': ['salas.points']
    },
    "NODEOUTPUTLIST": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/Nodes/pNodes.dat',
        'file_collection_paths': ['pNodes.dat']
    },
    "OUTLETNODELIST": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/Nodes/oNodes.dat',
        'file_collection_paths': ['oNodes.dat']
    },
    "HYDRONODELIST": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Input/Nodes/hNodes.dat',
        'file_collection_paths': ['hNodes.dat']
    },
    "RESTARTFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "RESTARTDIR": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "GRAPHFILE": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "WEATHERTABLENAME": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': 'Input/pramsWG.T',
        'file_collection_paths': []
    },
    "FORECASTFILE": {
        'has_resource_id': True,
        'has_file_collection_id': True,
        'path': 'Forecast/',
        'file_collection_paths': ['forecast.fake', 'Nested/nested_forecast.fake']
    },
    "OUTFILENAME": {
        'path': 'Output/voronoi/salas',
        'file_database_paths': []
    },
    "OUTHYDROFILENAME": {
        'path': 'Output/hyd/salas',
        'file_database_paths': []
    },
    "RESPOLYGONID": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
    "RESDATA": {
        'has_resource_id': False,
        'has_file_collection_id': False,
        'path': '',
        'file_collection_paths': []
    },
}

expected_datasets_salas_issues = [
    {
        'name': 'Groundwater Grid',
        'type': DatasetTypes.RASTER_CONT_ASCII,
        'description': 'Groundwater Grid for Test Scenario.'
    },
    {
        'name': 'Hydromet Station Data',
        'type': DatasetTypes.TRIBS_SDF_HYDROMET_STATION,
        'description': 'Hydromet Station Data for Test Scenario.'
    },
    {
        'name': 'Interior Node Output List',
        'type': DatasetTypes.TRIBS_NODE_LIST,
        'description': 'Interior Node Output List for Test Scenario.'
    },
    {
        'name': 'Land Use Reclassification Table',
        'type': DatasetTypes.TRIBS_TABLE_LANDUSE,
        'description': 'Land Use Reclassification Table for Test Scenario.'
    },
    {
        'name': 'Land Use Grid Data',
        'type': DatasetTypes.TRIBS_GRID_DATA,
        'description': 'Land Use Grid Data for Test Scenario.'
    },
    {
        'name': 'Node Output List',
        'type': DatasetTypes.TRIBS_NODE_LIST,
        'description': 'Node Output List for Test Scenario.'
    },
    {
        'name': 'Point File',
        'type': DatasetTypes.TRIBS_POINTS,
        'description': 'Point File for Test Scenario.'
    },
    {
        'name': 'Runtime Node Output List',
        'type': DatasetTypes.TRIBS_NODE_LIST,
        'description': 'Runtime Node Output List for Test Scenario.'
    },
    {
        'name': 'Soil Grid',
        'type': DatasetTypes.RASTER_DISC_ASCII,
        'description': 'Soil Grid for Test Scenario.'
    },
    {
        'name': 'Soil Reclassification Table',
        'type': DatasetTypes.TRIBS_TABLE_SOIL,
        'description': 'Soil Reclassification Table for Test Scenario.'
    },
    {
        'name': 'TIN',
        'type': DatasetTypes.TRIBS_TIN,
        'description': 'TIN for Test Scenario.'
    },
    {
        'name': 'Forecast Directory',
        'type': DatasetTypes.DIRECTORY,
        'description': 'Forecast Directory for Test Scenario.'
    },
]
