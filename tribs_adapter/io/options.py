from enum import IntEnum


class OptMeshInput(IntEnum):
    """Options for OPTMESHINPUT"""
    tMesh = 1
    points = 2
    arcGridRandom = 3
    arcGridHex = 4
    pointsNet = 5
    pointsLinPnt = 6
    scratch = 7
    pointTriangulator = 8
    largeDomain = 9


class OptRainSource(IntEnum):
    """Options for RAINSOURCE"""
    stageIIIRadar = 1
    wsiRadar = 2
    rainGauges = 3


class OptRainDistribution(IntEnum):
    """Options for RAINDISTRIBUTION"""
    spatiallyDistRadar = 0
    meanArealPrecipRadar = 1


class OptEvapTrans(IntEnum):
    """Options for OPTEVAPOTRANS"""
    inactive = 0
    penmanMonteith = 1
    deardorff = 2
    priestlyTaylor = 3
    panEvaporation = 4


class OptSnow(IntEnum):
    """Options for OPTSNOW"""
    inactive = 0
    singleLayer = 1


class OptHillAlbedo(IntEnum):
    """Options for HILLALBOPT"""
    snow = 0
    landuse = 1
    dynamic = 2


class OptRadShelt(IntEnum):
    """Options for OPTRADSHELT"""
    local = 0
    remoteDiffuse = 1
    remoteEntire = 2
    noSheltering = 3


class OptIntercept(IntEnum):
    """Options for OPTINTERCEPT"""
    inactive = 0
    canopyStorage = 1
    canopyWaterBalance = 2


class OptLanduse(IntEnum):
    """Options for OPTLANDUSE"""
    static = 0
    dynamic = 1


class OptLuInterp(IntEnum):
    """Options for OPTLUINTERP"""
    constant = 0
    linear = 1


class OptGFlux(IntEnum):
    """Options for GFLUXOPTION"""
    inactive = 0
    tempGradient = 1
    forceRestore = 2


class OptMetData(IntEnum):
    """Options for METDATAOPTION"""
    inactive = 0
    stations = 1
    hydroMetGrid = 2


class OptConvertData(IntEnum):
    """Options for CONVERTDATA"""
    inactive = 0
    hydroMet = 1
    rainGauge = 2
    dmip = 3


class OptBedrock(IntEnum):
    """Options for OPTBEDROCK"""
    uniform = 0
    gridded = 1


class OptGroundwater(IntEnum):
    """Options for OPTGROUNDWATER"""
    moduleOff = 0
    moduleOn = 1


class OptWidthInterpolation(IntEnum):
    """Options for WIDTHINTERPOLATION"""
    measuredAndObservered = 0
    measuredOnly = 1


class OptGwFile(IntEnum):
    """Options for OPTGWFILE"""
    grid = 0
    voronoi = 1


class OptRunon(IntEnum):
    """Options for OPTRUNON"""
    noRunon = 0
    runon = 1


class OptSoilType(IntEnum):
    """Options for OPTSOILTYPE"""
    tabular = 0
    gridded = 1


class OptStochasticMode(IntEnum):
    """Options for STOCHASTICMODE"""
    inactive = 0
    mean = 1
    random = 2
    sinusoidal = 3
    meanSine = 4
    randomSine = 5
    weatherGenerator = 6


class OptReservoir(IntEnum):
    """Options for OPTRESERVOIR"""
    inactive = 0
    active = 1


class OptPercolation(IntEnum):
    """Options for OPTPERCOLATION"""
    inactive = 0
    constantLoss = 1
    constantLossTransient = 2
    greenAmpt = 3


class OptForecastMode(IntEnum):
    """Options for FORECASTMODE"""
    inactive = 0
    qpf = 1
    persistence = 2
    climatological = 3


class OptRestartMode(IntEnum):
    """Options for RESTARTMODE"""
    inactive = 0
    writeOnly = 1
    readOnly = 2
    readAndWrite = 3


class OptParallelMode(IntEnum):
    """Options for PARALLELMODE"""
    serial = 0
    parallel = 1


class OptGraph(IntEnum):
    """Options for GRAPHOPTION"""
    default = 0
    reach = 1
    outlet = 2


class OptViz(IntEnum):
    """Options for OPTVIZ"""
    inactive = 0
    binary = 1


class OptSpatial(IntEnum):
    """Options for OPTSPATIAL"""
    spatialoutputOff = 0
    spatialoutputOn = 1


class OptInterhydro(IntEnum):
    """Options for OPTINTERHYDRO"""
    intermediatehydrographsOff = 0
    intermediatehydrographsOn = 1


class OptHeader(IntEnum):
    """Options for OPTHEADER"""
    outputheadersOff = 0
    outputheadersOn = 1
