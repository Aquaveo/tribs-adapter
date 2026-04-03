from pathlib import Path
from uuid import UUID
from datetime import datetime

import pytest

from tribs_adapter.io.options import (
    OptBedrock, OptConvertData, OptEvapTrans, OptForecastMode, OptGFlux, OptGraph, OptGroundwater, OptGwFile, OptHeader,
    OptHillAlbedo, OptIntercept, OptInterhydro, OptLanduse, OptLuInterp, OptMeshInput, OptMetData, OptParallelMode,
    OptPercolation, OptRadShelt, OptRainDistribution, OptRainSource, OptReservoir, OptRestartMode, OptRunon, OptSnow,
    OptSoilType, OptSpatial, OptStochasticMode, OptViz, OptWidthInterpolation
)


@pytest.fixture
def files_dir():
    test_dir = Path(__file__).parent
    files_dir = test_dir / 'files'
    return files_dir


@pytest.fixture
def smallbasin_resource_paths():
    return {
        'file_name': 'smallbasin.in',
        'files_and_pathnames': {
            'mesh_generation': {
                'ARCINFOFILENAME': {
                    'file_collection_paths': ['smallbasin'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/ArcFiles/smallbasin',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'INPUTDATAFILE': {
                    'file_collection_paths': ['smallbasin'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Output/Fall1996/voronoi/smallbasin',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'INPUTTIME': 0,
                'POINTFILENAME': {
                    'file_collection_paths': ['small.points'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/PointFiles/small.points',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                }
            },
            'meteorological_data': {
                'GAUGEBASENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'GAUGECONVERT': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'GAUGESTATIONS': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'HYDROMETBASENAME': {
                    'file_collection_paths': ['bfFall1996_dmp.mdf'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Weather/Fall1996/bfFall1996_dmp.mdf',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'HYDROMETCONVERT': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'HYDROMETGRID': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                'HYDROMETSTATIONS': {
                    'file_collection_paths': ['bfFall1996_dmp.sdf'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Weather/Fall1996/bfFall1996_dmp.sdf',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                }
            },
            'reservoir_data': {
                'RESDATA': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                },
                'RESPOLYGONID': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                }
            },
            "output_data": {
                "OUTFILENAME": {
                    'file_database_paths': [],
                    'path': 'Output/Fall1996/voronoi/smallbasin',
                },
                "OUTHYDROFILENAME": {
                    'file_database_paths': [],
                    'path': 'Output/Fall1996/hyd/smallbasin',
                },
                'HYDRONODELIST': {
                    'file_collection_paths': ['hNodes.dat'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/Nodes/hNodes.dat',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'NODEOUTPUTLIST': {
                    'file_collection_paths': ['pNodes.dat'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/Nodes/pNodes.dat',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'OUTHYDROEXTENSION': 'mrf',
                'OUTLETNODELIST': {
                    'file_collection_paths': ['oNodes.dat'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/Nodes/oNodes.dat',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'OPTSPATIAL': OptSpatial.spatialoutputOn,
                'OPTINTERHYDRO': OptInterhydro.intermediatehydrographsOff,
                'OPTHEADER': OptHeader.outputheadersOn,
                'RIBSHYDOUTPUT': 0
            },
            'resampling_grids': {
                'BEDROCKFILE': {
                    'file_collection_paths': ['/'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'DEMFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'DEPTHTOBEDROCK': 10.0,
                'GWATERFILE': {
                    'file_collection_paths': ['smallgw.iwt'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/smallgw.iwt',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'LANDMAPNAME': {
                    'file_collection_paths': ['small.lan'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/small.lan',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'LANDTABLENAME': {
                    'file_collection_paths': ['small.ldt'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/small.ldt',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'LUGRID': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'RAINEXTENSION': 'txt',
                'RAINFILE': {
                    'file_collection_paths': ['p'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Rain/Fall1996/p',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'SOILMAPNAME': {
                    'file_collection_paths': ['small.soi'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/small.soi',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                'SOILTABLENAME': {
                    'file_collection_paths': ['small.sdt'],
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'path': 'Input/small.sdt',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003'),
                },
                "SCGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
            }
        },
        'modes': {
            'parallel': {
                'GRAPHFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'GRAPHOPTION': OptGraph.default,
                'PARALLELMODE': OptParallelMode.parallel
            },
            'rainfall_forecasting': {
                'CLIMATOLOGY': None,
                'FORECASTFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'FORECASTLEADTIME': None,
                'FORECASTLENGTH': None,
                'FORECASTMODE': OptForecastMode.inactive,
                'FORECASTTIME': None,
                'RAINDISTRIBUTION': OptRainDistribution.spatiallyDistRadar
            },
            'restart': {
                'RESTARTDIR': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'RESTARTFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'RESTARTINTRVL': 8760.0,
                'RESTARTMODE': OptRestartMode.inactive
            },
            'stochastic_climate_forcing': {
                'ISTDUR': 0.0,
                'MAXISTDURMN': None,
                'MAXPMEAN': None,
                'MAXSTDURMN': None,
                'PERIOD': None,
                'PMEAN': 0.0,
                'SEED': 0.5,
                'STDUR': 0.0,
                'STOCHASTICMODE': OptStochasticMode.inactive,
                'WEATHERTABLENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                }
            }
        },
        'run_options': {
            'CONVERTDATA': OptConvertData.inactive,
            'GFLUXOPTION': OptGFlux.forceRestore,
            'HILLALBOPT': OptHillAlbedo.snow,
            'METDATAOPTION': OptMetData.stations,
            'OPTBEDROCK': OptBedrock.uniform,
            'OPTEVAPOTRANS': OptEvapTrans.penmanMonteith,
            'OPTGROUNDWATER': OptGroundwater.moduleOn,
            'OPTGWFILE': OptGwFile.grid,
            'OPTINTERCEPT': OptIntercept.canopyWaterBalance,
            'OPTLANDUSE': OptLanduse.static,
            'OPTLUINTERP': OptLuInterp.constant,
            'OPTMESHINPUT': OptMeshInput.pointTriangulator,
            'OPTPERCOLATION': OptPercolation.inactive,
            'OPTRADSHELT': OptRadShelt.local,
            'OPTRESERVOIR': OptReservoir.inactive,
            'OPTRUNON': OptRunon.runon,
            'OPTSNOW': OptSnow.inactive,
            'OPTSOILTYPE': OptSoilType.tabular,
            'RAINSOURCE': OptRainSource.stageIIIRadar,
            'WIDTHINTERPOLATION': OptWidthInterpolation.measuredAndObservered
        },
        'run_parameters': {
            'meteorological_variables': {
                'MINSNTEMP': -27.0,
                'PRECLAPSE': 0.0,
                'SNLIQFRAC': 0.6,
                'TEMPLAPSE': -0.0065,
                'TLINKE': 2.0
            },
            'routing_variables': {
                'BASEFLOW': 0.5,
                'CHANNELROUGHNESS': 0.3,
                'CHANNELWIDTH': 10.0,
                'CHANNELWIDTHCOEFF': 2.3,
                'CHANNELWIDTHEXPNT': 0.5,
                'CHANNELWIDTHFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'FLOWEXP': 0.4,
                'KINEMVELCOEF': 25.0,
                'VELOCITYCOEF': 0.6,
                'VELOCITYRATIO': 70.0
            },
            'time_variables': {
                'ETISTEP': 1.0,
                'GWSTEP': 30.0,
                'INTSTORMMAX': 120.0,
                'METSTEP': 60.0,
                'OPINTRVL': 1.0,
                'RAININTRVL': 1.0,
                'RAINSEARCH': 24.0,
                'RUNTIME': 1800.0,
                'SPOPINTRVL': 180.0,
                'STARTDATE': datetime(1996, 9, 24, 0, 0),
                'TIMESTEP': 3.75
            }
        },
        'visualization': {
            'OPTVIZ': OptViz.inactive,
            'OUTVIZFILENAME': {
                'file_collection_paths': [],
                'file_collection_id': None,
                'path': '',
                'resource_id': None
            }
        }
    }


@pytest.fixture
def smallbasin_raw_paths():
    return {
        'file_name': 'smallbasin.in',
        'files_and_pathnames': {
            'mesh_generation': {
                'ARCINFOFILENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/ArcFiles/smallbasin',
                    'resource_id': None
                },
                'INPUTDATAFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Output/Fall1996/voronoi/smallbasin',
                    'resource_id': None
                },
                'INPUTTIME': 0,
                'POINTFILENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/PointFiles/small.points',
                    'resource_id': None
                }
            },
            'meteorological_data': {
                'GAUGEBASENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'GAUGECONVERT': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'GAUGESTATIONS': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'HYDROMETBASENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/Fall1996/bfFall1996_dmp.mdf',
                    'resource_id': None
                },
                'HYDROMETCONVERT': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'HYDROMETGRID': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'HYDROMETSTATIONS': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/Fall1996/bfFall1996_dmp.sdf',
                    'resource_id': None
                }
            },
            'reservoir_data': {
                'RESDATA': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                },
                'RESPOLYGONID': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                }
            },
            "output_data": {
                "OUTFILENAME": {
                    'file_database_paths': [],
                    'path': 'Output/Fall1996/voronoi/smallbasin',
                },
                "OUTHYDROFILENAME": {
                    'file_database_paths': [],
                    'path': 'Output/Fall1996/hyd/smallbasin',
                },
                'HYDRONODELIST': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/hNodes.dat',
                    'resource_id': None
                },
                'NODEOUTPUTLIST': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/pNodes.dat',
                    'resource_id': None
                },
                'OUTHYDROEXTENSION': 'mrf',
                'OUTLETNODELIST': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/oNodes.dat',
                    'resource_id': None
                },
                'OPTSPATIAL': OptSpatial.spatialoutputOn,
                'OPTINTERHYDRO': OptInterhydro.intermediatehydrographsOff,
                'OPTHEADER': OptHeader.outputheadersOn,
                'RIBSHYDOUTPUT': 0
            },
            'resampling_grids': {
                'BEDROCKFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/',
                    'resource_id': None
                },
                'DEMFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'DEPTHTOBEDROCK': 10.0,
                'GWATERFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/smallgw.iwt',
                    'resource_id': None
                },
                'LANDMAPNAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/small.lan',
                    'resource_id': None
                },
                'LANDTABLENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/small.ldt',
                    'resource_id': None
                },
                'LUGRID': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'RAINEXTENSION': 'txt',
                'RAINFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Rain/Fall1996/p',
                    'resource_id': None
                },
                'SOILMAPNAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/small.soi',
                    'resource_id': None
                },
                'SOILTABLENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/small.sdt',
                    'resource_id': None
                },
                "SCGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
            }
        },
        'modes': {
            'parallel': {
                'GRAPHFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'GRAPHOPTION': OptGraph.default,
                'PARALLELMODE': OptParallelMode.parallel
            },
            'rainfall_forecasting': {
                'CLIMATOLOGY': None,
                'FORECASTFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'FORECASTLEADTIME': None,
                'FORECASTLENGTH': None,
                'FORECASTMODE': OptForecastMode.inactive,
                'FORECASTTIME': None,
                'RAINDISTRIBUTION': OptRainDistribution.spatiallyDistRadar
            },
            'restart': {
                'RESTARTDIR': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'RESTARTFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'RESTARTINTRVL': 8760.0,
                'RESTARTMODE': OptRestartMode.inactive
            },
            'stochastic_climate_forcing': {
                'ISTDUR': 0.0,
                'MAXISTDURMN': None,
                'MAXPMEAN': None,
                'MAXSTDURMN': None,
                'PERIOD': None,
                'PMEAN': 0.0,
                'SEED': 0.5,
                'STDUR': 0.0,
                'STOCHASTICMODE': OptStochasticMode.inactive,
                'WEATHERTABLENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                }
            }
        },
        'run_options': {
            'CONVERTDATA': OptConvertData.inactive,
            'GFLUXOPTION': OptGFlux.forceRestore,
            'HILLALBOPT': OptHillAlbedo.snow,
            'METDATAOPTION': OptMetData.stations,
            'OPTBEDROCK': OptBedrock.uniform,
            'OPTEVAPOTRANS': OptEvapTrans.penmanMonteith,
            'OPTGROUNDWATER': OptGroundwater.moduleOn,
            'OPTGWFILE': OptGwFile.grid,
            'OPTINTERCEPT': OptIntercept.canopyWaterBalance,
            'OPTLANDUSE': OptLanduse.static,
            'OPTLUINTERP': OptLuInterp.constant,
            'OPTMESHINPUT': OptMeshInput.pointTriangulator,
            'OPTPERCOLATION': OptPercolation.inactive,
            'OPTRADSHELT': OptRadShelt.local,
            'OPTRESERVOIR': OptReservoir.inactive,
            'OPTRUNON': OptRunon.runon,
            'OPTSNOW': OptSnow.inactive,
            'OPTSOILTYPE': OptSoilType.tabular,
            'RAINSOURCE': OptRainSource.stageIIIRadar,
            'WIDTHINTERPOLATION': OptWidthInterpolation.measuredAndObservered
        },
        'run_parameters': {
            'meteorological_variables': {
                'MINSNTEMP': -27.0,
                'PRECLAPSE': 0.0,
                'SNLIQFRAC': 0.6,
                'TEMPLAPSE': -0.0065,
                'TLINKE': 2.0
            },
            'routing_variables': {
                'BASEFLOW': 0.5,
                'CHANNELROUGHNESS': 0.3,
                'CHANNELWIDTH': 10.0,
                'CHANNELWIDTHCOEFF': 2.3,
                'CHANNELWIDTHEXPNT': 0.5,
                'CHANNELWIDTHFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'FLOWEXP': 0.4,
                'KINEMVELCOEF': 25.0,
                'VELOCITYCOEF': 0.6,
                'VELOCITYRATIO': 70.0
            },
            'time_variables': {
                'ETISTEP': 1.0,
                'GWSTEP': 30.0,
                'INTSTORMMAX': 120.0,
                'METSTEP': 60.0,
                'OPINTRVL': 1.0,
                'RAININTRVL': 1.0,
                'RAINSEARCH': 24.0,
                'RUNTIME': 1800.0,
                'SPOPINTRVL': 180.0,
                'STARTDATE': datetime(1996, 9, 24, 0, 0),
                'TIMESTEP': 3.75
            }
        },
        'visualization': {
            'OPTVIZ': OptViz.inactive,
            'OUTVIZFILENAME': {
                'file_collection_paths': [],
                'file_collection_id': None,
                'path': '',
                'resource_id': None
            }
        }
    }


@pytest.fixture
def smallbasin_raw_paths_copy_update():
    return {
        'file_name': 'smallbasin.in',
        'files_and_pathnames': {
            'mesh_generation': {
                'ARCINFOFILENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/ArcFiles/smallbasin',
                    'resource_id': None
                },
                'INPUTDATAFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Output/Fall1996/voronoi/smallbasin',
                    'resource_id': None
                },
                'INPUTTIME': 0,
                'POINTFILENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/PointFiles/small.points',
                    'resource_id': None
                }
            },
            'meteorological_data': {
                'GAUGEBASENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'GAUGECONVERT': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'GAUGESTATIONS': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'HYDROMETBASENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/Fall1996/bfFall1996_dmp.mdf',
                    'resource_id': None
                },
                'HYDROMETCONVERT': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'HYDROMETGRID': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'HYDROMETSTATIONS': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/Fall1996/bfFall1996_dmp.sdf',
                    'resource_id': None
                }
            },
            'reservoir_data': {
                'RESDATA': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                },
                'RESPOLYGONID': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                }
            },
            "output_data": {
                "OUTFILENAME": {
                    'file_database_paths': [],
                    'path': 'Output/Fall1996/voronoi/smallbasin',
                },
                "OUTHYDROFILENAME": {
                    'file_database_paths': [],
                    'path': 'Output/Fall1996/hyd/smallbasin',
                },
                'HYDRONODELIST': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/hNodes.dat',
                    'resource_id': None
                },
                'NODEOUTPUTLIST': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/pNodes.dat',
                    'resource_id': None
                },
                'OUTHYDROEXTENSION': 'mrf',
                'OUTLETNODELIST': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/oNodes.dat',
                    'resource_id': None
                },
                'OPTSPATIAL': OptSpatial.spatialoutputOn,
                'OPTINTERHYDRO': OptInterhydro.intermediatehydrographsOff,
                'OPTHEADER': OptHeader.outputheadersOn,
                'RIBSHYDOUTPUT': 0
            },
            'resampling_grids': {
                'BEDROCKFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/',
                    'resource_id': None
                },
                'DEMFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'DEPTHTOBEDROCK': 10.0,
                'GWATERFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/smallgw.iwt',
                    'resource_id': None
                },
                'LANDMAPNAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/small.lan',
                    'resource_id': None
                },
                'LANDTABLENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/small.ldt',
                    'resource_id': None
                },
                'LUGRID': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'RAINEXTENSION': 'txt',
                'RAINFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Rain/Fall1996/p',
                    'resource_id': None
                },
                'SOILMAPNAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/small.soi',
                    'resource_id': None
                },
                'SOILTABLENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/small.sdt',
                    'resource_id': None
                },
                "SCGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
            }
        },
        'modes': {
            'parallel': {
                'GRAPHFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'GRAPHOPTION': OptGraph.reach,
                'PARALLELMODE': OptParallelMode.parallel
            },
            'rainfall_forecasting': {
                'CLIMATOLOGY': None,
                'FORECASTFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'FORECASTLEADTIME': None,
                'FORECASTLENGTH': None,
                'FORECASTMODE': OptForecastMode.inactive,
                'FORECASTTIME': None,
                'RAINDISTRIBUTION': OptRainDistribution.spatiallyDistRadar
            },
            'restart': {
                'RESTARTDIR': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'RESTARTFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'RESTARTINTRVL': 8760.0,
                'RESTARTMODE': OptRestartMode.inactive
            },
            'stochastic_climate_forcing': {
                'ISTDUR': 0.0,
                'MAXISTDURMN': None,
                'MAXPMEAN': None,
                'MAXSTDURMN': None,
                'PERIOD': None,
                'PMEAN': 0.0,
                'SEED': 0.5,
                'STDUR': 0.1,
                'STOCHASTICMODE': OptStochasticMode.inactive,
                'WEATHERTABLENAME': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                }
            }
        },
        'run_options': {
            'CONVERTDATA': OptConvertData.inactive,
            'GFLUXOPTION': OptGFlux.forceRestore,
            'HILLALBOPT': OptHillAlbedo.snow,
            'METDATAOPTION': OptMetData.stations,
            'OPTBEDROCK': OptBedrock.uniform,
            'OPTEVAPOTRANS': OptEvapTrans.penmanMonteith,
            'OPTGROUNDWATER': OptGroundwater.moduleOn,
            'OPTGWFILE': OptGwFile.grid,
            'OPTINTERCEPT': OptIntercept.canopyWaterBalance,
            'OPTLANDUSE': OptLanduse.static,
            'OPTLUINTERP': OptLuInterp.constant,
            'OPTMESHINPUT': OptMeshInput.pointTriangulator,
            'OPTPERCOLATION': OptPercolation.inactive,
            'OPTRADSHELT': OptRadShelt.local,
            'OPTRESERVOIR': OptReservoir.inactive,
            'OPTRUNON': OptRunon.runon,
            'OPTSNOW': OptSnow.inactive,
            'OPTSOILTYPE': OptSoilType.tabular,
            'RAINSOURCE': OptRainSource.stageIIIRadar,
            'WIDTHINTERPOLATION': OptWidthInterpolation.measuredAndObservered
        },
        'run_parameters': {
            'meteorological_variables': {
                'MINSNTEMP': -27.0,
                'PRECLAPSE': 0.0,
                'SNLIQFRAC': 0.6,
                'TEMPLAPSE': -0.0065,
                'TLINKE': 2.0
            },
            'routing_variables': {
                'BASEFLOW': 0.5,
                'CHANNELROUGHNESS': 0.3,
                'CHANNELWIDTH': 10.0,
                'CHANNELWIDTHCOEFF': 2.3,
                'CHANNELWIDTHEXPNT': 0.5,
                'CHANNELWIDTHFILE': {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None
                },
                'FLOWEXP': 0.4,
                'KINEMVELCOEF': 25.0,
                'VELOCITYCOEF': 0.6,
                'VELOCITYRATIO': 70.0
            },
            'time_variables': {
                'ETISTEP': 1.0,
                'GWSTEP': 30.0,
                'INTSTORMMAX': 120.0,
                'METSTEP': 60.0,
                'OPINTRVL': 1.0,
                'RAININTRVL': 2.0,
                'RAINSEARCH': 24.0,
                'RUNTIME': 1800.0,
                'SPOPINTRVL': 180.0,
                'STARTDATE': datetime(2020, 4, 1, 0, 0),
                'TIMESTEP': 3.75
            }
        },
        'visualization': {
            'OPTVIZ': OptViz.inactive,
            'OUTVIZFILENAME': {
                'file_collection_paths': [],
                'file_collection_id': None,
                'path': '',
                'resource_id': None
            }
        }
    }


@pytest.fixture
def salas_resource_paths():
    return {
        "file_name": "salas.in",
        "run_parameters": {
            "time_variables": {
                "STARTDATE": datetime(2004, 6, 1, 0, 0),
                "RUNTIME": 700.0,
                "TIMESTEP": 3.75,
                "GWSTEP": 7.5,
                "METSTEP": 60.0,
                "ETISTEP": 60.0,
                "RAININTRVL": 1.0,
                "OPINTRVL": 1.0,
                "SPOPINTRVL": 10.0,
                "INTSTORMMAX": 8760.0,
                "RAINSEARCH": 2400.0
            },
            "routing_variables": {
                "BASEFLOW": 0.01,
                "VELOCITYCOEF": 0.5,
                "VELOCITYRATIO": 5.0,
                "KINEMVELCOEF": 0.1,
                "FLOWEXP": 0.0000001,
                "CHANNELROUGHNESS": 0.15,
                "CHANNELWIDTH": 10.0,
                "CHANNELWIDTHCOEFF": 1.0,
                "CHANNELWIDTHEXPNT": 0.3,
                "CHANNELWIDTHFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
            },
            "meteorological_variables": {
                "MINSNTEMP": -27.0,
                "PRECLAPSE": 0.0,
                "SNLIQFRAC": 0.6,
                "TEMPLAPSE": -0.0065,
                "TLINKE": 2.0
            }
        },
        "run_options": {
            "OPTMESHINPUT": OptMeshInput.points,
            "RAINSOURCE": OptRainSource.wsiRadar,
            "OPTEVAPOTRANS": OptEvapTrans.penmanMonteith,
            "OPTINTERCEPT": OptIntercept.canopyWaterBalance,
            "GFLUXOPTION": OptGFlux.forceRestore,
            "METDATAOPTION": OptMetData.stations,
            "CONVERTDATA": OptConvertData.inactive,
            "OPTBEDROCK": OptBedrock.uniform,
            'OPTGROUNDWATER': OptGroundwater.moduleOn,
            "WIDTHINTERPOLATION": OptWidthInterpolation.measuredAndObservered,
            "OPTGWFILE": OptGwFile.grid,
            "OPTRUNON": OptRunon.noRunon,
            'HILLALBOPT': OptHillAlbedo.dynamic,
            'OPTLANDUSE': OptLanduse.dynamic,
            'OPTLUINTERP': OptLuInterp.constant,
            'OPTPERCOLATION': OptPercolation.inactive,
            'OPTRADSHELT': OptRadShelt.local,
            'OPTRESERVOIR': OptReservoir.inactive,
            'OPTSOILTYPE': OptSoilType.tabular,
            "OPTSNOW": OptSnow.singleLayer,
        },
        "files_and_pathnames": {
            "mesh_generation": {
                "INPUTDATAFILE": {
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'file_collection_paths': ["salas"],
                    'path': 'Output/voronoi/salas',
                    'resource_id': UUID('b5fbf7f8-bff5-4d3f-adec-7721854aa813')
                },
                "POINTFILENAME": {
                    'file_collection_id': UUID('7254e912-7f6a-412b-9f44-f2906f9536a0'),
                    'file_collection_paths': ["salas.points"],
                    'path': 'Input/salas.points',
                    'resource_id': UUID('b5fbf7f8-bff5-4d3f-adec-7721854aa813')
                },
                "ARCINFOFILENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "INPUTTIME": 0
            },
            "resampling_grids": {
                "SOILTABLENAME": {
                    'file_collection_id': UUID('26e77327-cc83-41f7-8bfb-98fe609bbd09'),
                    'file_collection_paths': ["salas.sdt"],
                    'path': 'Input/salas.sdt',
                    'resource_id': UUID('2abd7b95-cf27-485c-a568-3a04bc5a2f23')
                },
                "SOILMAPNAME": {
                    'file_collection_id': UUID('8b504df2-281f-407b-ac9e-db225f6b3d4f'),
                    'file_collection_paths': ["salas.soi"],
                    'path': 'Input/salas.soi',
                    'resource_id': UUID('5b2c674c-11bd-40ba-ac48-96b46d145003')
                },
                "SCGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "LANDTABLENAME": {
                    'file_collection_id': UUID('e4f8494b-086c-41f2-9ea8-ca1685ab06bb'),
                    'file_collection_paths': ["salas.ldt"],
                    'path': 'Input/salas.ldt',
                    'resource_id': UUID('4168e694-5f55-4b35-9d9e-7d82b3fede07')
                },
                "LANDMAPNAME": {
                    'file_collection_id': UUID('a1f06946-1e98-4462-94a8-ae5af735cf6d'),
                    'file_collection_paths': ["salas.lan"],
                    'path': 'Input/salas.lan',
                    'resource_id': UUID('9721c551-cdac-44fc-8964-8b09627eafad')
                },
                "LUGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "GWATERFILE": {
                    'file_collection_id': UUID('2eaf95fb-3334-47a8-9748-2126484e9f7c'),
                    'file_collection_paths': ["salas.iwt"],
                    'path': 'Input/salas.iwt',
                    'resource_id': UUID('31689c77-e222-4b96-96a6-8aa9a96a27fb')
                },
                "RAINFILE": {
                    'file_collection_id': UUID('5eacb619-2caf-46a6-be95-a27f5e878a60'),
                    'file_collection_paths': ["p"],
                    'path': 'Rain/p',
                    'resource_id': UUID('c16429ab-c561-4961-8e43-a245f20f6f86')
                },
                "RAINEXTENSION": "txt",
                "DEPTHTOBEDROCK": 5.0,
                "BEDROCKFILE": {
                    'file_collection_id': UUID('d42476e8-6a51-4010-8329-e14a29338b00'),
                    'file_collection_paths': ["Input/salas.brd"],
                    'path': 'salas.brd',
                    'resource_id': UUID('ed0d5767-5148-4269-8adb-bd9b417d5c01')
                },
                "DEMFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
            },
            "meteorological_data": {
                "HYDROMETSTATIONS": {
                    'file_collection_id': UUID('882226c1-8975-4c8f-8fc4-0fad36275864'),
                    'file_collection_paths': ["weatherC1601_2004.sdf"],
                    'path': 'Weather/weatherC1601_2004.sdf',
                    'resource_id': UUID('1e40a35b-9908-49bf-b9a6-5cf469a7fa9e')
                },
                "HYDROMETGRID": {
                    'file_collection_paths': ["/"],
                    'file_collection_id': None,
                    'path': 'Weather/',
                    'resource_id': None,
                },
                "HYDROMETCONVERT": {
                    'file_collection_paths': ["/"],
                    'file_collection_id': None,
                    'path': 'Weather/',
                    'resource_id': None,
                },
                "HYDROMETBASENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/weatherField',
                    'resource_id': None,
                },
                "GAUGESTATIONS": {
                    'file_collection_id': UUID('d8d6ed7d-84c6-4a8e-8007-b1468d6749db'),
                    'file_collection_paths': ["rainGauge.sdf"],
                    'path': 'Rain/rainGauge.sdf',
                    'resource_id': UUID('7a283cc5-3644-4f1b-907d-5b000681e6a9')
                },
                "GAUGEBASENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "GAUGECONVERT": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
            },
            'reservoir_data': {
                'RESDATA': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                },
                'RESPOLYGONID': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                }
            },
            "output_data": {
                "OUTFILENAME": {
                    'file_database_paths': [],
                    'path': 'voronoi/salas',
                },
                "OUTHYDROFILENAME": {
                    'file_database_paths': [],
                    'path': 'hyd/salas',
                },
                "OUTHYDROEXTENSION": "mrf",
                "RIBSHYDOUTPUT": 0,
                "NODEOUTPUTLIST": {
                    'file_collection_id': UUID('d9fa7eaa-08c9-4e97-92f6-12e8b9877bdd'),
                    'file_collection_paths': ["pNodes.dat"],
                    'path': 'Input/Nodes/pNodes.dat',
                    'resource_id': UUID('83cc5ebf-91ef-4cdf-95ba-9954c290daff')
                },
                "HYDRONODELIST": {
                    'file_collection_id': UUID('b7bd66c6-2517-4a21-90ee-2c0428f2ece4'),
                    'file_collection_paths': ["hNodes.dat"],
                    'path': 'Input/Nodes/hNodes.dat',
                    'resource_id': UUID('208e2489-7455-432e-b929-4ecdcdb9b114')
                },
                "OUTLETNODELIST": {
                    'file_collection_id': UUID('35963f8b-98a7-4dfd-8df0-859378dc856d'),
                    'file_collection_paths': ["oNodes.dat"],
                    'path': 'Input/Nodes/oNodes.dat',
                    'resource_id': UUID('10383a86-f327-4aed-8b13-20c1b98105b6')
                },
                'OPTSPATIAL': OptSpatial.spatialoutputOn,
                'OPTINTERHYDRO': OptInterhydro.intermediatehydrographsOff,
                'OPTHEADER': OptHeader.outputheadersOn,
            },
        },
        "modes": {
            "rainfall_forecasting": {
                "FORECASTMODE": OptForecastMode.inactive,
                "FORECASTLEADTIME": None,
                "FORECASTLENGTH": None,
                "FORECASTTIME": None,
                "FORECASTFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "CLIMATOLOGY": None,
                "RAINDISTRIBUTION": OptRainDistribution.spatiallyDistRadar,
            },
            "stochastic_climate_forcing": {
                "STOCHASTICMODE": OptStochasticMode.inactive,
                "PMEAN": 0.0,
                "STDUR": 0.0,
                "ISTDUR": 0.0,
                "SEED": 11.0,
                "PERIOD": 0.0,
                "MAXPMEAN": 0.0,
                "MAXSTDURMN": 0.0,
                "MAXISTDURMN": 0.0,
                "WEATHERTABLENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/pramsWG.T',
                    'resource_id': None,
                },
            },
            "parallel": {
                "GRAPHFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "GRAPHOPTION": OptGraph.default,
                "PARALLELMODE": OptParallelMode.parallel
            },
            "restart": {
                "RESTARTMODE": OptRestartMode.writeOnly,
                "RESTARTDIR": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "RESTARTFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "RESTARTINTRVL": 8760.0,
            }
        },
        "visualization": {
            "OPTVIZ": OptViz.inactive,
            "OUTVIZFILENAME": {
                'file_collection_paths': [],
                'file_collection_id': None,
                'path': '',
                'resource_id': None,
            }
        }
    }


@pytest.fixture
def salas_raw_paths():
    return {
        "file_name": "salas.in",
        "run_parameters": {
            "time_variables": {
                "STARTDATE": datetime(2004, 6, 1, 0),
                "RUNTIME": 700.0,
                "TIMESTEP": 3.75,
                "GWSTEP": 7.5,
                "METSTEP": 60.0,
                "ETISTEP": 60.0,
                "RAININTRVL": 1.0,
                "OPINTRVL": 1.0,
                "SPOPINTRVL": 10.0,
                "INTSTORMMAX": 8760.0,
                "RAINSEARCH": 2400.0
            },
            "routing_variables": {
                "BASEFLOW": 0.01,
                "VELOCITYCOEF": 0.5,
                "VELOCITYRATIO": 5.0,
                "KINEMVELCOEF": 0.1,
                "FLOWEXP": 0.0000001,
                "CHANNELROUGHNESS": 0.15,
                "CHANNELWIDTH": 10.0,
                "CHANNELWIDTHCOEFF": 1.0,
                "CHANNELWIDTHEXPNT": 0.3,
                "CHANNELWIDTHFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                }
            },
            "meteorological_variables": {
                "MINSNTEMP": -27.0,
                "PRECLAPSE": 0.0,
                "SNLIQFRAC": 0.6,
                "TEMPLAPSE": -0.0065,
                "TLINKE": 2.0
            }
        },
        "run_options": {
            "OPTMESHINPUT": OptMeshInput.points,
            "RAINSOURCE": OptRainSource.wsiRadar,
            "OPTEVAPOTRANS": OptEvapTrans.penmanMonteith,
            "OPTINTERCEPT": OptIntercept.canopyWaterBalance,
            "GFLUXOPTION": OptGFlux.forceRestore,
            "METDATAOPTION": OptMetData.stations,
            "CONVERTDATA": OptConvertData.inactive,
            "OPTBEDROCK": OptBedrock.uniform,
            'OPTGROUNDWATER': OptGroundwater.moduleOn,
            "WIDTHINTERPOLATION": OptWidthInterpolation.measuredAndObservered,
            "OPTGWFILE": OptGwFile.grid,
            "OPTRUNON": OptRunon.noRunon,
            'HILLALBOPT': OptHillAlbedo.dynamic,
            'OPTLANDUSE': OptLanduse.dynamic,
            'OPTLUINTERP': OptLuInterp.constant,
            'OPTPERCOLATION': OptPercolation.inactive,
            'OPTRADSHELT': OptRadShelt.local,
            'OPTRESERVOIR': OptReservoir.inactive,
            'OPTSOILTYPE': OptSoilType.tabular,
            "OPTSNOW": OptSnow.singleLayer,
        },
        "files_and_pathnames": {
            "mesh_generation": {
                "INPUTDATAFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Output/voronoi/salas',
                    'resource_id': None,
                },
                "POINTFILENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.points',
                    'resource_id': None,
                },
                "ARCINFOFILENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "INPUTTIME": 0
            },
            "resampling_grids": {
                "SOILTABLENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.sdt',
                    'resource_id': None,
                },
                "SOILMAPNAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.soi',
                    'resource_id': None,
                },
                "SCGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "LANDTABLENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.ldt',
                    'resource_id': None,
                },
                "LANDMAPNAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.lan',
                    'resource_id': None,
                },
                "LUGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "GWATERFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.iwt',
                    'resource_id': None,
                },
                "RAINFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Rain/p',
                    'resource_id': None,
                },
                "RAINEXTENSION": "txt",
                "DEPTHTOBEDROCK": 5.0,
                "BEDROCKFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.brd',
                    'resource_id': None,
                },
                "DEMFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
            },
            "meteorological_data": {
                "HYDROMETSTATIONS": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/weatherC1601_2004.sdf',
                    'resource_id': None,
                },
                "HYDROMETGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/',
                    'resource_id': None,
                },
                "HYDROMETCONVERT": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/',
                    'resource_id': None,
                },
                "HYDROMETBASENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/weatherField',
                    'resource_id': None,
                },
                "GAUGESTATIONS": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Rain/rainGauge.sdf',
                    'resource_id': None,
                },
                "GAUGEBASENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "GAUGECONVERT": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
            },
            'reservoir_data': {
                'RESDATA': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                },
                'RESPOLYGONID': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                }
            },
            "output_data": {
                "OUTFILENAME": {
                    'file_database_paths': [],
                    'path': "Output/voronoi/salas",
                },
                "OUTHYDROFILENAME": {
                    'file_database_paths': [],
                    'path': "Output/hyd/salas",
                },
                "OUTHYDROEXTENSION": "mrf",
                "RIBSHYDOUTPUT": 0,
                "NODEOUTPUTLIST": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/pNodes.dat',
                    'resource_id': None,
                },
                "HYDRONODELIST": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/hNodes.dat',
                    'resource_id': None,
                },
                "OUTLETNODELIST": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/oNodes.dat',
                    'resource_id': None,
                },
                'OPTSPATIAL': OptSpatial.spatialoutputOn,
                'OPTINTERHYDRO': OptInterhydro.intermediatehydrographsOff,
                'OPTHEADER': OptHeader.outputheadersOn,
            }
        },
        "modes": {
            "rainfall_forecasting": {
                "FORECASTMODE": OptForecastMode.inactive,
                "FORECASTLEADTIME": None,
                "FORECASTLENGTH": None,
                "FORECASTTIME": None,
                "FORECASTFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "CLIMATOLOGY": None,
                "RAINDISTRIBUTION": OptRainDistribution.spatiallyDistRadar,
            },
            "stochastic_climate_forcing": {
                "STOCHASTICMODE": OptStochasticMode.inactive,
                "PMEAN": 0.0,
                "STDUR": 0.0,
                "ISTDUR": 0.0,
                "SEED": 11.0,
                "PERIOD": 0.0,
                "MAXPMEAN": 0.0,
                "MAXSTDURMN": 0.0,
                "MAXISTDURMN": 0.0,
                "WEATHERTABLENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/pramsWG.T',
                    'resource_id': None,
                },
            },
            "parallel": {
                "GRAPHFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "GRAPHOPTION": OptGraph.default,
                "PARALLELMODE": OptParallelMode.parallel
            },
            "restart": {
                "RESTARTMODE": OptRestartMode.inactive,
                "RESTARTDIR": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "RESTARTFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "RESTARTINTRVL": 8760.0,
            }
        },
        "visualization": {
            "OPTVIZ": OptViz.inactive,
            "OUTVIZFILENAME": {
                'file_collection_paths': [],
                'file_collection_id': None,
                'path': '',
                'resource_id': None,
            }
        }
    }


@pytest.fixture
def salas_raw_paths_copy_update():
    return {
        "file_name": "salas.in",
        "run_parameters": {
            "time_variables": {
                "STARTDATE": datetime(2020, 4, 1, 0, 0),
                "RUNTIME": 700.0,
                "TIMESTEP": 3.75,
                "GWSTEP": 7.5,
                "METSTEP": 60.0,
                "ETISTEP": 60.0,
                "RAININTRVL": 2.0,
                "OPINTRVL": 1.0,
                "SPOPINTRVL": 10.0,
                "INTSTORMMAX": 8760.0,
                "RAINSEARCH": 2400.0
            },
            "routing_variables": {
                "BASEFLOW": 0.01,
                "VELOCITYCOEF": 0.5,
                "VELOCITYRATIO": 5.0,
                "KINEMVELCOEF": 0.1,
                "FLOWEXP": 0.0000001,
                "CHANNELROUGHNESS": 0.15,
                "CHANNELWIDTH": 10.0,
                "CHANNELWIDTHCOEFF": 1.0,
                "CHANNELWIDTHEXPNT": 0.3,
                "CHANNELWIDTHFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                }
            },
            "meteorological_variables": {
                "MINSNTEMP": -27.0,
                "PRECLAPSE": 0.0,
                "SNLIQFRAC": 0.6,
                "TEMPLAPSE": -0.0065,
                "TLINKE": 2.0
            }
        },
        "run_options": {
            "OPTMESHINPUT": OptMeshInput.points,
            "RAINSOURCE": OptRainSource.wsiRadar,
            "OPTEVAPOTRANS": OptEvapTrans.penmanMonteith,
            "OPTINTERCEPT": OptIntercept.canopyWaterBalance,
            "GFLUXOPTION": OptGFlux.forceRestore,
            "METDATAOPTION": OptMetData.stations,
            "CONVERTDATA": OptConvertData.inactive,
            "OPTBEDROCK": OptBedrock.uniform,
            'OPTGROUNDWATER': OptGroundwater.moduleOn,
            "WIDTHINTERPOLATION": OptWidthInterpolation.measuredAndObservered,
            "OPTGWFILE": OptGwFile.grid,
            "OPTRUNON": OptRunon.noRunon,
            'HILLALBOPT': OptHillAlbedo.dynamic,
            'OPTLANDUSE': OptLanduse.dynamic,
            'OPTLUINTERP': OptLuInterp.constant,
            'OPTPERCOLATION': OptPercolation.inactive,
            'OPTRADSHELT': OptRadShelt.local,
            'OPTRESERVOIR': OptReservoir.inactive,
            'OPTSOILTYPE': OptSoilType.tabular,
            "OPTSNOW": OptSnow.singleLayer,
        },
        "files_and_pathnames": {
            "mesh_generation": {
                "INPUTDATAFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Output/voronoi/salas',
                    'resource_id': None,
                },
                "POINTFILENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.points',
                    'resource_id': None,
                },
                "ARCINFOFILENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "INPUTTIME": 0
            },
            "resampling_grids": {
                "SOILTABLENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.sdt',
                    'resource_id': None,
                },
                "SOILMAPNAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.soi',
                    'resource_id': None,
                },
                "SCGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "LANDTABLENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.ldt',
                    'resource_id': None,
                },
                "LANDMAPNAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.lan',
                    'resource_id': None,
                },
                "LUGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "GWATERFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.iwt',
                    'resource_id': None,
                },
                "RAINFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Rain/p',
                    'resource_id': None,
                },
                "RAINEXTENSION": "txt",
                "DEPTHTOBEDROCK": 5.0,
                "BEDROCKFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/salas.brd',
                    'resource_id': None,
                },
                "DEMFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
            },
            "meteorological_data": {
                "HYDROMETSTATIONS": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/weatherC1601_2004.sdf',
                    'resource_id': None,
                },
                "HYDROMETGRID": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/',
                    'resource_id': None,
                },
                "HYDROMETCONVERT": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/',
                    'resource_id': None,
                },
                "HYDROMETBASENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Weather/weatherField',
                    'resource_id': None,
                },
                "GAUGESTATIONS": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Rain/rainGauge.sdf',
                    'resource_id': None,
                },
                "GAUGEBASENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "GAUGECONVERT": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
            },
            'reservoir_data': {
                'RESDATA': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                },
                'RESPOLYGONID': {
                    'file_collection_id': None,
                    'file_collection_paths': [],
                    'path': '',
                    'resource_id': None
                }
            },
            "output_data": {
                "OUTFILENAME": {
                    'file_database_paths': [],
                    'path': "Output/voronoi/salas",
                },
                "OUTHYDROFILENAME": {
                    'file_database_paths': [],
                    'path': "Output/hyd/salas",
                },
                "OUTHYDROEXTENSION": "mrf",
                "RIBSHYDOUTPUT": 0,
                "NODEOUTPUTLIST": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/pNodes.dat',
                    'resource_id': None,
                },
                "HYDRONODELIST": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/hNodes.dat',
                    'resource_id': None,
                },
                "OUTLETNODELIST": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/Nodes/oNodes.dat',
                    'resource_id': None,
                },
                'OPTSPATIAL': OptSpatial.spatialoutputOn,
                'OPTINTERHYDRO': OptInterhydro.intermediatehydrographsOff,
                'OPTHEADER': OptHeader.outputheadersOn,
            }
        },
        "modes": {
            "rainfall_forecasting": {
                "FORECASTMODE": OptForecastMode.inactive,
                "FORECASTLEADTIME": None,
                "FORECASTLENGTH": None,
                "FORECASTTIME": None,
                "FORECASTFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "CLIMATOLOGY": None,
                "RAINDISTRIBUTION": OptRainDistribution.spatiallyDistRadar,
            },
            "stochastic_climate_forcing": {
                "STOCHASTICMODE": OptStochasticMode.inactive,
                "PMEAN": 0.0,
                "STDUR": 0.1,
                "ISTDUR": 0.0,
                "SEED": 11.0,
                "PERIOD": 0.0,
                "MAXPMEAN": 0.0,
                "MAXSTDURMN": 0.0,
                "MAXISTDURMN": 0.0,
                "WEATHERTABLENAME": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': 'Input/pramsWG.T',
                    'resource_id': None,
                },
            },
            "parallel": {
                "GRAPHFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "GRAPHOPTION": OptGraph.reach,
                "PARALLELMODE": OptParallelMode.parallel
            },
            "restart": {
                "RESTARTMODE": OptRestartMode.inactive,
                "RESTARTDIR": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "RESTARTFILE": {
                    'file_collection_paths': [],
                    'file_collection_id': None,
                    'path': '',
                    'resource_id': None,
                },
                "RESTARTINTRVL": 8760.0,
            }
        },
        "visualization": {
            "OPTVIZ": OptViz.inactive,
            "OUTVIZFILENAME": {
                'file_collection_paths': [],
                'file_collection_id': None,
                'path': '',
                'resource_id': None,
            }
        }
    }
