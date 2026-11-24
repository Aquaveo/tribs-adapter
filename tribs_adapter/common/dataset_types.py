from enum import auto, unique

from strenum import (
    StrEnum,
)  # TODO: Replace with built-in StrEnum when upgrade to >= Python 3.11


@unique
class DatasetTypes(StrEnum):
    DIRECTORY = auto()
    FEATURES_GEOJSON = auto()
    FEATURES_SHAPEFILE = auto()
    JSON = auto()
    RASTER_CONT_ASCII = auto()
    RASTER_DISC_ASCII = auto()
    RASTER_CONT_ASCII_TIMESERIES = auto()
    RASTER_DISC_ASCII_TIMESERIES = auto()
    RASTER_CONT_GEOTIFF = auto()
    RASTER_DISC_GEOTIFF = auto()
    RASTER_RGB_GEOTIFF = auto()
    RASTER_CONT_GEOTIFF_TIMESERIES = auto()
    RASTER_DISC_GEOTIFF_TIMESERIES = auto()
    SOILGRID_PHYSICAL_SOIL_DATA = auto()
    TIAP_ARCINFO = auto()
    TRIBS_CHANNEL_WIDTH = auto()
    TRIBS_GRAPH = auto()
    TRIBS_GRID_DATA = auto()
    TRIBS_INPUT_FILE_JSON = auto()
    TRIBS_MDF_RAIN_GAUGE = auto()
    TRIBS_MDF_HYDROMET_STATION = auto()
    TRIBS_MDI_RAIN_GAUGE = auto()
    TRIBS_MDI_HYDROMET_STATION = auto()
    TRIBS_NODE_LIST = auto()
    TRIBS_OUT_CNTRL = auto()
    TRIBS_OUT_MRF = auto()
    TRIBS_OUT_RFT = auto()
    TRIBS_OUT_PIXEL = auto()
    TRIBS_OUT_QOUT = auto()
    TRIBS_OUT_TIME_DYNAMIC = auto()
    TRIBS_OUT_TIME_INTEGRATED = auto()
    TRIBS_OUT_STATIONS = auto()
    TRIBS_POINTS = auto()
    TRIBS_RES_POLY = auto()
    TRIBS_RES_DATA = auto()
    TRIBS_SDF_RAIN_GAUGE = auto()
    TRIBS_SDF_HYDROMET_STATION = auto()
    TRIBS_TABLE_LANDUSE = auto()
    TRIBS_TABLE_SOIL = auto()
    TRIBS_TIN = auto()
    TRIBS_METIS = auto()
    GRIDDED_NETCDF = auto()
    GRIDDED_NETCDF_TIMESERIES = auto()
    UNKNOWN = auto()


GltfOutputDatasetTypes = (
    DatasetTypes.TRIBS_OUT_TIME_DYNAMIC,
    DatasetTypes.TRIBS_OUT_TIME_INTEGRATED,
)

CompoundDatasetTypes = (DatasetTypes.TRIBS_GRID_DATA, DatasetTypes.SOILGRID_PHYSICAL_SOIL_DATA)

InputDatasetTypes = (
    DatasetTypes.FEATURES_SHAPEFILE,
    DatasetTypes.RASTER_CONT_ASCII,
    DatasetTypes.RASTER_DISC_ASCII,
    DatasetTypes.RASTER_CONT_ASCII_TIMESERIES,
    DatasetTypes.RASTER_DISC_ASCII_TIMESERIES,
    DatasetTypes.RASTER_CONT_GEOTIFF,
    DatasetTypes.RASTER_DISC_GEOTIFF,
    DatasetTypes.RASTER_RGB_GEOTIFF,
    DatasetTypes.RASTER_CONT_GEOTIFF_TIMESERIES,
    DatasetTypes.RASTER_DISC_GEOTIFF_TIMESERIES,
    DatasetTypes.TRIBS_TIN,
    DatasetTypes.TRIBS_POINTS,
    DatasetTypes.TRIBS_CHANNEL_WIDTH,
    DatasetTypes.TRIBS_GRAPH,
    DatasetTypes.TRIBS_GRID_DATA,
    DatasetTypes.TRIBS_INPUT_FILE_JSON,
    DatasetTypes.TRIBS_MDF_RAIN_GAUGE,
    DatasetTypes.TRIBS_MDF_HYDROMET_STATION,
    DatasetTypes.TRIBS_MDI_RAIN_GAUGE,
    DatasetTypes.TRIBS_MDI_HYDROMET_STATION,
    DatasetTypes.TRIBS_NODE_LIST,
    DatasetTypes.TRIBS_POINTS,
    DatasetTypes.TRIBS_RES_POLY,
    DatasetTypes.TRIBS_RES_DATA,
    DatasetTypes.TRIBS_SDF_RAIN_GAUGE,
    DatasetTypes.TRIBS_SDF_HYDROMET_STATION,
    DatasetTypes.TRIBS_TABLE_LANDUSE,
    DatasetTypes.TRIBS_TABLE_SOIL,
    DatasetTypes.TRIBS_METIS,
    DatasetTypes.GRIDDED_NETCDF,
    DatasetTypes.GRIDDED_NETCDF_TIMESERIES,
)

OutputDatsetTypes = (
    DatasetTypes.TRIBS_OUT_CNTRL,
    DatasetTypes.TRIBS_OUT_MRF,
    DatasetTypes.TRIBS_OUT_RFT,
    DatasetTypes.TRIBS_OUT_PIXEL,
    DatasetTypes.TRIBS_OUT_QOUT,
    DatasetTypes.TRIBS_OUT_TIME_DYNAMIC,
    DatasetTypes.TRIBS_OUT_TIME_INTEGRATED,
    DatasetTypes.TRIBS_OUT_STATIONS,
)

SpatialDatasetTypes = (
    DatasetTypes.FEATURES_GEOJSON,
    DatasetTypes.FEATURES_SHAPEFILE,
    DatasetTypes.RASTER_CONT_ASCII,
    DatasetTypes.RASTER_DISC_ASCII,
    DatasetTypes.RASTER_CONT_ASCII_TIMESERIES,
    DatasetTypes.RASTER_DISC_ASCII_TIMESERIES,
    DatasetTypes.RASTER_CONT_GEOTIFF,
    DatasetTypes.RASTER_DISC_GEOTIFF,
    DatasetTypes.RASTER_RGB_GEOTIFF,
    DatasetTypes.RASTER_CONT_GEOTIFF_TIMESERIES,
    DatasetTypes.RASTER_DISC_GEOTIFF_TIMESERIES,
    DatasetTypes.TRIBS_TIN,
    DatasetTypes.TRIBS_POINTS,
    DatasetTypes.TRIBS_OUT_TIME_DYNAMIC,
    DatasetTypes.TRIBS_OUT_TIME_INTEGRATED,
    DatasetTypes.TRIBS_OUT_PIXEL,
    DatasetTypes.TRIBS_OUT_MRF,
    DatasetTypes.TRIBS_OUT_RFT,
    DatasetTypes.TRIBS_SDF_HYDROMET_STATION,
    DatasetTypes.TRIBS_SDF_RAIN_GAUGE,
    DatasetTypes.TRIBS_OUT_QOUT,
)

WMSDatasetTypes = (
    DatasetTypes.FEATURES_SHAPEFILE,
    DatasetTypes.RASTER_CONT_ASCII,
    DatasetTypes.RASTER_DISC_ASCII,
    DatasetTypes.RASTER_CONT_GEOTIFF,
    DatasetTypes.RASTER_DISC_GEOTIFF,
    DatasetTypes.RASTER_RGB_GEOTIFF,
    DatasetTypes.RASTER_CONT_ASCII_TIMESERIES,
    DatasetTypes.RASTER_DISC_ASCII_TIMESERIES,
    DatasetTypes.RASTER_CONT_GEOTIFF_TIMESERIES,
    DatasetTypes.RASTER_DISC_GEOTIFF_TIMESERIES,
    DatasetTypes.TRIBS_METIS,
)

RasterDatasetTypes = (
    DatasetTypes.RASTER_CONT_ASCII, DatasetTypes.RASTER_DISC_ASCII, DatasetTypes.RASTER_CONT_GEOTIFF,
    DatasetTypes.RASTER_DISC_GEOTIFF, DatasetTypes.RASTER_RGB_GEOTIFF, DatasetTypes.RASTER_CONT_ASCII_TIMESERIES,
    DatasetTypes.RASTER_DISC_ASCII_TIMESERIES, DatasetTypes.RASTER_CONT_GEOTIFF_TIMESERIES,
    DatasetTypes.RASTER_DISC_GEOTIFF_TIMESERIES, DatasetTypes.SOILGRID_PHYSICAL_SOIL_DATA
)

GisDatasetTypes = (DatasetTypes.FEATURES_SHAPEFILE, )

SdfDatasetTypes = (
    DatasetTypes.TRIBS_SDF_RAIN_GAUGE,
    DatasetTypes.TRIBS_SDF_HYDROMET_STATION,
)

NoEnvStrDatasetTypes = (
    DatasetTypes.RASTER_DISC_ASCII, DatasetTypes.RASTER_DISC_ASCII_TIMESERIES, DatasetTypes.RASTER_DISC_GEOTIFF,
    DatasetTypes.RASTER_DISC_GEOTIFF_TIMESERIES, DatasetTypes.FEATURES_SHAPEFILE, DatasetTypes.RASTER_RGB_GEOTIFF,
    DatasetTypes.TRIBS_METIS
)
