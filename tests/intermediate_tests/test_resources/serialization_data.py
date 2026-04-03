import datetime
from enum import Enum
import re
from uuid import UUID

from pytest_unordered import unordered

from tribs_adapter.io.options import (
    OptBedrock, OptConvertData, OptEvapTrans, OptForecastMode, OptGFlux, OptGraph, OptGroundwater, OptGwFile, OptHeader,
    OptHillAlbedo, OptIntercept, OptInterhydro, OptLanduse, OptLuInterp, OptMeshInput, OptMetData, OptParallelMode,
    OptPercolation, OptRadShelt, OptRainDistribution, OptRainSource, OptReservoir, OptRestartMode, OptRunon, OptSnow,
    OptSoilType, OptSpatial, OptStochasticMode, OptViz, OptWidthInterpolation
)


def replace_enum_reprs(s: str) -> str:
    OPT_ENUM_PATTERN = re.compile('<Opt[a-zA-Z.]+: ([0-9+])>')
    s, _ = OPT_ENUM_PATTERN.subn('\\1', s)
    return s


def replace_enum_int(obj: dict):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, Enum):
                obj[key] = obj[key].value
            else:
                replace_enum_int(value)

    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            if isinstance(value, Enum):
                obj[i] = obj[i].value
            else:
                replace_enum_int(value)


def replace_random_vals(obj: dict | list):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, UUID):
                obj[key] = '00000000-0000-0000-0000-000000000000'
            elif isinstance(value, datetime.datetime):
                obj[key] = '0000-00-00T00:00:00+00:00'
            else:
                replace_random_vals(value)

    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            if isinstance(value, UUID):
                obj[i] = '00000000-0000-0000-0000-000000000000'
            elif isinstance(value, datetime.datetime):
                obj[i] = '0000-00-00T00:00:00+00:00'
            else:
                replace_random_vals(value)


def replace_random_vals_str(s: str) -> str:
    UUID_PATTERN = re.compile('[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}', re.IGNORECASE)
    ISO_DATE_PATTERN = re.compile(
        '(?:\\d{4})-(?:\\d{2})-(?:\\d{2})T(?:\\d{2}):(?:\\d{2}):(?:\\d{2}(?:\\.\\d*)?)(?:(?:-(?:\\d{2}):(?:\\d{2})|Z)?)'
    )
    s, _ = UUID_PATTERN.subn('00000000-0000-0000-0000-000000000000', s)
    s, _ = ISO_DATE_PATTERN.subn('0000-00-00T00:00:00+00:00', s)
    return s


serialized_project = {
    'id':
        '00000000-0000-0000-0000-000000000000',
    'attributes': {},
    'created_by':
        '_staff',
    'date_created':
        '0000-00-00T00:00:00+00:00',
    'description':
        'Initialized Project with File Database.',
    'display_type_plural':
        'Projects',
    'display_type_singular':
        'Project',
    'locked':
        False,
    'name':
        'Test FDB Project',
    'organizations': [],
    'public':
        False,
    'slug':
        'projects',
    'status':
        None,
    'type':
        'project_resource',
    'datasets':
        unordered([{
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Runtime Node Output List for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Runtime Node Output List',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_node_list'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Interior Node Output List for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Interior Node Output List',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_node_list'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Node Output List for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Node Output List',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_node_list'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'TIN for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'TIN',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_tin'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Point File for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Point File',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_points'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Land Use Reclassification Table for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Land Use Reclassification Table',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_table_landuse'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Land Use Grid for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Land Use Grid',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'raster_disc_ascii'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Soil Grid for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Soil Grid',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'raster_disc_ascii'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Soil Reclassification Table for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Soil Reclassification Table',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_table_soil'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Groundwater Grid for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Groundwater Grid',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'raster_disc_ascii'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Radar Rainfall Grids for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Radar Rainfall Grids',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'raster_cont_ascii_timeseries'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Hydromet Station Data for Salas.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Hydromet Station Data',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_sdf_hydromet_station'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Basin Averaged Hydrograph File for Salas Run 10-20-30.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Basin Averaged Hydrograph File',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_out_mrf'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Control File for Salas Run 10-20-30.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Control File',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_out_cntrl'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Hydrograph Runoff Types File for Salas Run 10-20-30.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Hydrograph Runoff Types File',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_out_rft'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Qout File for Salas Run 10-20-30.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Qout File',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_out_qout'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Time-Dynamic Variable Output for Salas Run 10-20-30.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Time-Dynamic Variable Output',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_out_time_dynamic'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Time-Integrated Variable Output for Salas Run 10-20-30.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Time-Integrated Variable Output',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_out_time_integrated'
        }, {
            'id': '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by': '_staff',
            'date_created': '0000-00-00T00:00:00+00:00',
            'description': 'Node Dynamic Output for Salas Run 10-20-30.',
            'display_type_plural': 'Datasets',
            'display_type_singular': 'Dataset',
            'locked': False,
            'name': 'Node Dynamic Output',
            'organizations': [],
            'public': False,
            'slug': 'datasets',
            'status': None,
            'type': 'dataset_resource',
            'dataset_type': 'tribs_out_pixel'
        }]),
    'scenarios':
        unordered([{
            'id':
                '00000000-0000-0000-0000-000000000000',
            'attributes': {},
            'created_by':
                '_staff',
            'date_created':
                '0000-00-00T00:00:00+00:00',
            'description':
                'Fully populated scenario for testing.',
            'display_type_plural':
                'Scenarios',
            'display_type_singular':
                'Scenario',
            'locked':
                False,
            'name':
                'Salas',
            'organizations': [],
            'public':
                False,
            'slug':
                'scenarios',
            'status':
                None,
            'type':
                'scenario_resource',
            'input_file': {
                'file_name': 'salas.in',
                'run_parameters': {
                    'time_variables': {
                        'STARTDATE': '0000-00-00T00:00:00+00:00',
                        'RUNTIME': 700.0,
                        'TIMESTEP': 3.75,
                        'GWSTEP': 7.5,
                        'METSTEP': 60.0,
                        'ETISTEP': 60.0,
                        'RAININTRVL': 1.0,
                        'OPINTRVL': 1.0,
                        'SPOPINTRVL': 10.0,
                        'INTSTORMMAX': 8760.0,
                        'RAINSEARCH': 2400.0
                    },
                    'routing_variables': {
                        'BASEFLOW': 0.01,
                        'VELOCITYCOEF': 0.5,
                        'VELOCITYRATIO': 5.0,
                        'KINEMVELCOEF': 0.1,
                        'FLOWEXP': 1e-07,
                        'CHANNELROUGHNESS': 0.15,
                        'CHANNELWIDTH': 10.0,
                        'CHANNELWIDTHCOEFF': 1.0,
                        'CHANNELWIDTHEXPNT': 0.3,
                        'CHANNELWIDTHFILE': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        }
                    },
                    'meteorological_variables': {
                        'TLINKE': 2.0,
                        'MINSNTEMP': -27.0,
                        'TEMPLAPSE': -0.0065,
                        'PRECLAPSE': 0.0,
                        'SNLIQFRAC': 0.6
                    }
                },
                'run_options': {
                    'OPTMESHINPUT': OptMeshInput.points,
                    'RAINSOURCE': OptRainSource.wsiRadar,
                    'OPTEVAPOTRANS': OptEvapTrans.penmanMonteith,
                    'OPTSNOW': OptSnow.singleLayer,
                    'HILLALBOPT': OptHillAlbedo.dynamic,
                    'OPTRADSHELT': OptRadShelt.local,
                    'OPTINTERCEPT': OptIntercept.canopyWaterBalance,
                    'OPTLANDUSE': OptLanduse.dynamic,
                    'OPTLUINTERP': OptLuInterp.linear,
                    'GFLUXOPTION': OptGFlux.forceRestore,
                    'METDATAOPTION': OptMetData.stations,
                    'CONVERTDATA': OptConvertData.inactive,
                    'OPTBEDROCK': OptBedrock.uniform,
                    'OPTGROUNDWATER': OptGroundwater.moduleOn,
                    'WIDTHINTERPOLATION': OptWidthInterpolation.measuredAndObservered,
                    'OPTGWFILE': OptGwFile.grid,
                    'OPTRUNON': OptRunon.noRunon,
                    'OPTRESERVOIR': OptReservoir.inactive,
                    'OPTSOILTYPE': OptSoilType.tabular,
                    'OPTPERCOLATION': OptPercolation.inactive
                },
                'files_and_pathnames': {
                    'mesh_generation': {
                        'INPUTDATAFILE': {
                            'resource_id':
                                '00000000-0000-0000-0000-000000000000',
                            'file_collection_id':
                                '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths':
                                unordered([
                                    'salas.z', 'salas_voi', 'salas_width', 'salas.tri', 'salas_area', 'salas.nodes',
                                    'salas_reach', 'salas.edges'
                                ]),
                            'path':
                                'Output/voronoi/salas'
                        },
                        'POINTFILENAME': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': ['salas.points'],
                            'path': 'Input/salas.points'
                        },
                        'INPUTTIME': 0,
                        'ARCINFOFILENAME': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        }
                    },
                    'resampling_grids': {
                        'SOILTABLENAME': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': ['salas.sdt'],
                            'path': 'Input/salas.sdt'
                        },
                        'SOILMAPNAME': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': ['salas.soi'],
                            'path': 'Input/salas.soi'
                        },
                        'LANDTABLENAME': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': ['salas.ldt'],
                            'path': 'Input/salas.ldt'
                        },
                        'LANDMAPNAME': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': ['salas.lan'],
                            'path': 'Input/salas.lan'
                        },
                        'GWATERFILE': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': ['salas.iwt'],
                            'path': 'Input/salas.iwt'
                        },
                        'DEMFILE': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        },
                        'RAINFILE': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': unordered(['p0630200417.txt', 'p0531200418.txt']),
                            'path': 'Rain/p'
                        },
                        'RAINEXTENSION': 'txt',
                        'DEPTHTOBEDROCK': 5.0,
                        'BEDROCKFILE': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': 'Input/salas.brd'
                        },
                        'LUGRID': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        },
                        'SCGRID': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        }
                    },
                    'meteorological_data': {
                        'HYDROMETSTATIONS': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': unordered(['weatherC1601_2004.mdf', 'weatherC1601_2004.sdf']),
                            'path': 'Weather/weatherC1601_2004.sdf'
                        },
                        'HYDROMETGRID': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': 'Weather/'
                        },
                        'HYDROMETCONVERT': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': 'Weather/'
                        },
                        'HYDROMETBASENAME': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': 'Weather/weatherField'
                        },
                        'GAUGESTATIONS': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': 'Rain/rainGauge.sdf'
                        },
                        'GAUGECONVERT': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        },
                        'GAUGEBASENAME': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        }
                    },
                    'output_data': {
                        'OUTFILENAME': {
                            'file_database_paths': [],
                            'path': 'Output/voronoi/salas'
                        },
                        'OUTHYDROFILENAME': {
                            'file_database_paths': [],
                            'path': 'Output/hyd/salas'
                        },
                        'OUTHYDROEXTENSION': 'mrf',
                        'RIBSHYDOUTPUT': 0,
                        'NODEOUTPUTLIST': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': ['pNodes.dat'],
                            'path': 'Input/Nodes/pNodes.dat'
                        },
                        'HYDRONODELIST': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': ['hNodes.dat'],
                            'path': 'Input/Nodes/hNodes.dat'
                        },
                        'OUTLETNODELIST': {
                            'resource_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                            'file_collection_paths': ['oNodes.dat'],
                            'path': 'Input/Nodes/oNodes.dat'
                        },
                        'OPTSPATIAL': OptSpatial.spatialoutputOn,
                        'OPTINTERHYDRO': OptInterhydro.intermediatehydrographsOff,
                        'OPTHEADER': OptHeader.outputheadersOn,
                    },
                    'reservoir_data': {
                        'RESPOLYGONID': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        },
                        'RESDATA': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        }
                    }
                },
                'modes': {
                    'rainfall_forecasting': {
                        'FORECASTMODE': OptForecastMode.inactive,
                        'FORECASTTIME': None,
                        'FORECASTLEADTIME': None,
                        'FORECASTLENGTH': None,
                        'FORECASTFILE': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        },
                        'CLIMATOLOGY': None,
                        'RAINDISTRIBUTION': OptRainDistribution.spatiallyDistRadar
                    },
                    'stochastic_climate_forcing': {
                        'STOCHASTICMODE': OptStochasticMode.inactive,
                        'PMEAN': 0.0,
                        'STDUR': 0.0,
                        'ISTDUR': 0.0,
                        'SEED': 11.0,
                        'PERIOD': 0.0,
                        'MAXPMEAN': 0.0,
                        'MAXSTDURMN': 0.0,
                        'MAXISTDURMN': 0.0,
                        'WEATHERTABLENAME': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': 'Input/pramsWG.T'
                        }
                    },
                    'restart': {
                        'RESTARTMODE': OptRestartMode.writeOnly,
                        'RESTARTINTRVL': 8760.0,
                        'RESTARTDIR': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        },
                        'RESTARTFILE': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        }
                    },
                    'parallel': {
                        'PARALLELMODE': OptParallelMode.parallel,
                        'GRAPHOPTION': OptGraph.default,
                        'GRAPHFILE': {
                            'resource_id': None,
                            'file_collection_id': None,
                            'file_collection_paths': [],
                            'path': ''
                        }
                    }
                },
                'visualization': {
                    'OPTVIZ': OptViz.inactive,
                    'OUTVIZFILENAME': {
                        'resource_id': None,
                        'file_collection_id': None,
                        'file_collection_paths': [],
                        'path': ''
                    }
                }
            },
            'linked_datasets':
                unordered([{
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Runtime Node Output List'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Interior Node Output List'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Node Output List'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'TIN'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Point File'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Land Use Reclassification Table'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Land Use Grid'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Soil Grid'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Soil Reclassification Table'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Groundwater Grid'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Radar Rainfall Grids'
                }, {
                    'id': '00000000-0000-0000-0000-000000000000',
                    'name': 'Hydromet Station Data'
                }]),
            'realizations':
                unordered([{
                    'id':
                        '00000000-0000-0000-0000-000000000000',
                    'attributes': {},
                    'created_by':
                        '_staff',
                    'date_created':
                        '0000-00-00T00:00:00+00:00',
                    'description':
                        'Results from run of Salas scenario.',
                    'display_type_plural':
                        'Realizations',
                    'display_type_singular':
                        'Realization',
                    'locked':
                        False,
                    'name':
                        'Salas Run 10-20-30',
                    'organizations': [],
                    'public':
                        False,
                    'slug':
                        'realizations',
                    'status':
                        None,
                    'type':
                        'realization_resource',
                    'input_file': {
                        'file_name': 'salas.in',
                        'run_parameters': {
                            'time_variables': {
                                'STARTDATE': '0000-00-00T00:00:00+00:00',
                                'RUNTIME': 700.0,
                                'TIMESTEP': 3.75,
                                'GWSTEP': 7.5,
                                'METSTEP': 60.0,
                                'ETISTEP': 60.0,
                                'RAININTRVL': 1.0,
                                'OPINTRVL': 1.0,
                                'SPOPINTRVL': 10.0,
                                'INTSTORMMAX': 8760.0,
                                'RAINSEARCH': 2400.0
                            },
                            'routing_variables': {
                                'BASEFLOW': 0.01,
                                'VELOCITYCOEF': 0.5,
                                'VELOCITYRATIO': 5.0,
                                'KINEMVELCOEF': 0.1,
                                'FLOWEXP': 1e-07,
                                'CHANNELROUGHNESS': 0.15,
                                'CHANNELWIDTH': 10.0,
                                'CHANNELWIDTHCOEFF': 1.0,
                                'CHANNELWIDTHEXPNT': 0.3,
                                'CHANNELWIDTHFILE': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                }
                            },
                            'meteorological_variables': {
                                'TLINKE': 2.0,
                                'MINSNTEMP': -27.0,
                                'TEMPLAPSE': -0.0065,
                                'PRECLAPSE': 0.0,
                                'SNLIQFRAC': 0.6
                            }
                        },
                        'run_options': {
                            'OPTMESHINPUT': OptMeshInput.points,
                            'RAINSOURCE': OptRainSource.wsiRadar,
                            'OPTEVAPOTRANS': OptEvapTrans.penmanMonteith,
                            'OPTSNOW': OptSnow.singleLayer,
                            'HILLALBOPT': OptHillAlbedo.dynamic,
                            'OPTRADSHELT': OptRadShelt.local,
                            'OPTINTERCEPT': OptIntercept.canopyWaterBalance,
                            'OPTLANDUSE': OptLanduse.dynamic,
                            'OPTLUINTERP': OptLuInterp.linear,
                            'GFLUXOPTION': OptGFlux.forceRestore,
                            'METDATAOPTION': OptMetData.stations,
                            'CONVERTDATA': OptConvertData.inactive,
                            'OPTBEDROCK': OptBedrock.uniform,
                            'OPTGROUNDWATER': OptGroundwater.moduleOn,
                            'WIDTHINTERPOLATION': OptWidthInterpolation.measuredAndObservered,
                            'OPTGWFILE': OptGwFile.grid,
                            'OPTRUNON': OptRunon.noRunon,
                            'OPTRESERVOIR': OptReservoir.inactive,
                            'OPTSOILTYPE': OptSoilType.tabular,
                            'OPTPERCOLATION': OptPercolation.inactive
                        },
                        'files_and_pathnames': {
                            'mesh_generation': {
                                'INPUTDATAFILE': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': [
                                        'salas.z', 'salas_voi', 'salas_width', 'salas.tri', 'salas_area', 'salas.nodes',
                                        'salas_reach', 'salas.edges'
                                    ],
                                    'path': 'Output/voronoi/salas'
                                },
                                'POINTFILENAME': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['salas.points'],
                                    'path': 'Input/salas.points'
                                },
                                'INPUTTIME': 0,
                                'ARCINFOFILENAME': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                }
                            },
                            'resampling_grids': {
                                'SOILTABLENAME': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['salas.sdt'],
                                    'path': 'Input/salas.sdt'
                                },
                                'SOILMAPNAME': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['salas.soi'],
                                    'path': 'Input/salas.soi'
                                },
                                'LANDTABLENAME': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['salas.ldt'],
                                    'path': 'Input/salas.ldt'
                                },
                                'LANDMAPNAME': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['salas.lan'],
                                    'path': 'Input/salas.lan'
                                },
                                'GWATERFILE': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['salas.iwt'],
                                    'path': 'Input/salas.iwt'
                                },
                                'DEMFILE': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                },
                                'RAINFILE': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['p0630200417.txt', 'p0531200418.txt'],
                                    'path': 'Rain/p'
                                },
                                'RAINEXTENSION': 'txt',
                                'DEPTHTOBEDROCK': 5.0,
                                'BEDROCKFILE': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': 'Input/salas.brd'
                                },
                                'LUGRID': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                },
                                'SCGRID': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                }
                            },
                            'meteorological_data': {
                                'HYDROMETSTATIONS': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['weatherC1601_2004.mdf', 'weatherC1601_2004.sdf'],
                                    'path': 'Weather/weatherC1601_2004.sdf'
                                },
                                'HYDROMETGRID': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': 'Weather/'
                                },
                                'HYDROMETCONVERT': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': 'Weather/'
                                },
                                'HYDROMETBASENAME': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': 'Weather/weatherField'
                                },
                                'GAUGESTATIONS': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': 'Rain/rainGauge.sdf'
                                },
                                'GAUGECONVERT': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                },
                                'GAUGEBASENAME': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                }
                            },
                            'output_data': {
                                'OUTFILENAME': {
                                    'file_database_paths':
                                        unordered([{
                                            'resource_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_paths': [
                                                'salas.0000_00d', 'salas.0010_00d', 'salas.0700_00d'
                                            ],
                                            'path': ''
                                        }, {
                                            'resource_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_paths': ['salas.0000_00i', 'salas.0700_00i'],
                                            'path': ''
                                        }, {
                                            'resource_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_paths': ['salas0.pixel'],
                                            'path': ''
                                        }]),
                                    'path':
                                        'Output/voronoi/salas'
                                },
                                'OUTHYDROFILENAME': {
                                    'file_database_paths':
                                        unordered([{
                                            'resource_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_paths': ['salas0700_00.mrf'],
                                            'path': ''
                                        }, {
                                            'resource_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_paths': ['salas.cntrl'],
                                            'path': ''
                                        }, {
                                            'resource_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_paths': ['salas0700_00.rft'],
                                            'path': ''
                                        }, {
                                            'resource_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                            'file_collection_paths': ['salas_Outlet.qout'],
                                            'path': ''
                                        }]),
                                    'path':
                                        'Output/hyd/salas'
                                },
                                'OUTHYDROEXTENSION': 'mrf',
                                'RIBSHYDOUTPUT': 0,
                                'NODEOUTPUTLIST': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['pNodes.dat'],
                                    'path': 'Input/Nodes/pNodes.dat'
                                },
                                'HYDRONODELIST': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['hNodes.dat'],
                                    'path': 'Input/Nodes/hNodes.dat'
                                },
                                'OUTLETNODELIST': {
                                    'resource_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_id': '00000000-0000-0000-0000-000000000000',
                                    'file_collection_paths': ['oNodes.dat'],
                                    'path': 'Input/Nodes/oNodes.dat'
                                },
                                'OPTSPATIAL': OptSpatial.spatialoutputOn,
                                'OPTINTERHYDRO': OptInterhydro.intermediatehydrographsOff,
                                'OPTHEADER': OptHeader.outputheadersOn,
                            },
                            'reservoir_data': {
                                'RESPOLYGONID': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                },
                                'RESDATA': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                }
                            }
                        },
                        'modes': {
                            'rainfall_forecasting': {
                                'FORECASTMODE': OptForecastMode.inactive,
                                'FORECASTTIME': None,
                                'FORECASTLEADTIME': None,
                                'FORECASTLENGTH': None,
                                'FORECASTFILE': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                },
                                'CLIMATOLOGY': None,
                                'RAINDISTRIBUTION': OptRainDistribution.spatiallyDistRadar
                            },
                            'stochastic_climate_forcing': {
                                'STOCHASTICMODE': OptStochasticMode.inactive,
                                'PMEAN': 0.0,
                                'STDUR': 0.0,
                                'ISTDUR': 0.0,
                                'SEED': 11.0,
                                'PERIOD': 0.0,
                                'MAXPMEAN': 0.0,
                                'MAXSTDURMN': 0.0,
                                'MAXISTDURMN': 0.0,
                                'WEATHERTABLENAME': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': 'Input/pramsWG.T'
                                }
                            },
                            'restart': {
                                'RESTARTMODE': OptRestartMode.writeOnly,
                                'RESTARTINTRVL': 8760.0,
                                'RESTARTDIR': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                },
                                'RESTARTFILE': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                }
                            },
                            'parallel': {
                                'PARALLELMODE': OptParallelMode.parallel,
                                'GRAPHOPTION': OptGraph.default,
                                'GRAPHFILE': {
                                    'resource_id': None,
                                    'file_collection_id': None,
                                    'file_collection_paths': [],
                                    'path': ''
                                }
                            }
                        },
                        'visualization': {
                            'OPTVIZ': OptViz.inactive,
                            'OUTVIZFILENAME': {
                                'resource_id': None,
                                'file_collection_id': None,
                                'file_collection_paths': [],
                                'path': ''
                            }
                        }
                    },
                    'linked_datasets':
                        unordered([{
                            'id': '00000000-0000-0000-0000-000000000000',
                            'name': 'Basin Averaged Hydrograph File'
                        }, {
                            'id': '00000000-0000-0000-0000-000000000000',
                            'name': 'Control File'
                        }, {
                            'id': '00000000-0000-0000-0000-000000000000',
                            'name': 'Hydrograph Runoff Types File'
                        }, {
                            'id': '00000000-0000-0000-0000-000000000000',
                            'name': 'Qout File'
                        }, {
                            'id': '00000000-0000-0000-0000-000000000000',
                            'name': 'Time-Dynamic Variable Output'
                        }, {
                            'id': '00000000-0000-0000-0000-000000000000',
                            'name': 'Time-Integrated Variable Output'
                        }, {
                            'id': '00000000-0000-0000-0000-000000000000',
                            'name': 'Node Dynamic Output'
                        }])
                }])
        }])
}
