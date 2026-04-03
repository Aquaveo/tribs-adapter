import pytest
from datetime import datetime
from tribs_adapter.io.util import datetime_from_str, parse_in_file


@pytest.mark.parametrize(
    's,expected', [
        (datetime(2004, 6, 1), datetime(2004, 6, 1)),
        ('06/01', '06/01'),
        ('06/01/2004', datetime(2004, 6, 1)),
        ('06/01/2004/00', datetime(2004, 6, 1, 0)),
        ('06/01/2004/00/30', datetime(2004, 6, 1, 0, 30)),
    ]
)
def test_datetime_from_str(s, expected):
    assert datetime_from_str(s) == expected


def test_parse_in_file(input_files_dir):
    in_file_path = input_files_dir / 'salas.in'

    ret = parse_in_file(in_file_path)

    assert ret == {
        'STARTDATE': '06/01/2004/00',
        'RUNTIME': '700',
        'TIMESTEP': '3.75',
        'GWSTEP': '7.5',
        'METSTEP': '60.0',
        'ETISTEP': '60.0',
        'RAININTRVL': '1',
        'OPINTRVL': '1',
        'SPOPINTRVL': '10',
        'INTSTORMMAX': '8760',
        'RAINSEARCH': '2400',
        'BASEFLOW': '0.01',
        'VELOCITYCOEF': '0.5',
        'VELOCITYRATIO': '5',
        'KINEMVELCOEF': '0.1',
        'FLOWEXP': '0.0000001',
        'CHANNELROUGHNESS': '0.15',
        'CHANNELWIDTH': '10',
        'CHANNELWIDTHCOEFF': '1.0',
        'CHANNELWIDTHEXPNT': '0.3',
        'TLINKE': '2.5',
        'OPTMESHINPUT': '2',
        'RAINSOURCE': '2',
        'OPTEVAPOTRANS': '1',
        'OPTINTERCEPT': '2',
        'GFLUXOPTION': '2',
        'METDATAOPTION': '1',
        'CONVERTDATA': '0',
        'OPTBEDROCK': '0',
        'WIDTHINTERPOLATION': '0',
        'OPTGWFILE': '0',
        'OPTRUNON': '0',
        'INPUTDATAFILE': 'Output/voronoi/salas',
        'POINTFILENAME': 'Input/salas.points',
        'SOILTABLENAME': 'Input/salas.sdt',
        'SOILMAPNAME': 'Input/salas.soi',
        'LANDTABLENAME': 'Input/salas.ldt',
        'LANDMAPNAME': 'Input/salas.lan',
        'GWATERFILE': 'Input/salas.iwt',
        'RAINFILE': 'Rain/p',
        'RAINEXTENSION': 'txt',
        'DEPTHTOBEDROCK': '5',
        'BEDROCKFILE': 'Input/salas.brd',
        'HYDROMETSTATIONS': 'Weather/weatherC1601_2004.sdf',
        'HYDROMETGRID': 'Weather/',
        'HYDROMETCONVERT': 'Weather/',
        'HYDROMETBASENAME': 'Weather/weatherField',
        'GAUGESTATIONS': 'Rain/rainGauge.sdf',
        'OUTFILENAME': 'Output/voronoi/salas',
        'OUTHYDROFILENAME': 'Output/hyd/salas',
        'OUTHYDROEXTENSION': 'mrf',
        'RIBSHYDOUTPUT': '0',
        'NODEOUTPUTLIST': 'Input/Nodes/pNodes.dat',
        'HYDRONODELIST': 'Input/Nodes/hNodes.dat',
        'OUTLETNODELIST': 'Input/Nodes/oNodes.dat',
        'FORECASTMODE': '0',
        'RAINDISTRIBUTION': '0',
        'STOCHASTICMODE': '0',
        'PMEAN': '0.0',
        'STDUR': '0.0',
        'ISTDUR': '0.0',
        'SEED': '11',
        'PERIOD': '0',
        'MAXPMEAN': '0',
        'MAXSTDURMN': '0',
        'MAXISTDURMN': '0',
        'WEATHERTABLENAME': 'Input/pramsWG.T'
    }
