import copy
from enum import auto, unique
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Tuple
import warnings

from pydantic import UUID4, BaseModel, BeforeValidator, model_validator
from strenum import StrEnum  # TODO: Replace with built-in StrEnum when upgrade to >= Python 3.11
from typing_extensions import Annotated

from tribs_adapter.io.options import (
    OptBedrock, OptConvertData, OptEvapTrans, OptForecastMode, OptGFlux, OptGraph, OptGroundwater, OptGwFile, OptHeader,
    OptHillAlbedo, OptIntercept, OptInterhydro, OptLanduse, OptLuInterp, OptMeshInput, OptMetData, OptParallelMode,
    OptPercolation, OptRadShelt, OptRainDistribution, OptRainSource, OptSpatial, OptReservoir, OptRestartMode, OptRunon,
    OptSnow, OptSoilType, OptStochasticMode, OptViz, OptWidthInterpolation
)
import tribs_adapter.io.renderer as renderer
from tribs_adapter.io.util import datetime_from_str, parse_in_file
from tribs_adapter.common.file_to_dataset import FILE_TO_DATASET

# Supporting Types and Models ---------------------------------------------------------------------------------------- #
TribsDatetime = Annotated[datetime, BeforeValidator(lambda v: datetime_from_str(v))]


class FileDatabasePath(BaseModel):
    resource_id: UUID4 | list[UUID4] | None = None
    file_collection_id: UUID4 | list[UUID4] | None = None
    file_collection_paths: list[str] | list[list[str]] = list()
    path: str = ""

    @model_validator(mode='before')
    def validate_model(cls, data: str | dict[str, Any]):
        if isinstance(data, str):
            return {
                "resource_id": None,
                "file_collection_id": None,
                "file_collection_paths": list(),
                "path": data,
            }
        elif isinstance(data, dict):
            # Set empty string values for IDs to None
            if data.get('resource_id', "") == "":
                data['resource_id'] = None
            if data.get('file_collection_id', "") == "":
                data['file_collection_id'] = None
            return data
        raise TypeError(f'Expected str or dict, got "{type(data).__name__}" instead.')


class FileDatabasePathCollection(BaseModel):
    file_database_paths: list[FileDatabasePath] = list()
    path: str = ""

    @model_validator(mode='before')
    def validate_model(cls, data: str | dict[str, Any]):
        if isinstance(data, str):
            return {
                "file_database_paths": list(),
                "path": data,
            }
        elif isinstance(data, dict):
            return data
        raise TypeError(f'Expected str or dict, got "{type(data).__name__}" instead.')


class TimeVariables(BaseModel):
    STARTDATE: TribsDatetime | None = datetime.now()
    RUNTIME: float = 1440.0
    TIMESTEP: float = 3.75
    GWSTEP: float = 30.0
    METSTEP: float = 60.0
    ETISTEP: float = 1.0
    RAININTRVL: float = 1.0
    OPINTRVL: float = 1.0
    SPOPINTRVL: float = 168.0
    INTSTORMMAX: float = 1000.0
    RAINSEARCH: float = 24.0


class RoutingVariables(BaseModel):
    BASEFLOW: float = 0.01
    VELOCITYCOEF: float = 0.6
    VELOCITYRATIO: float = 70.0
    KINEMVELCOEF: float = 25.0
    FLOWEXP: float = 0.4
    CHANNELROUGHNESS: float = 0.3
    CHANNELWIDTH: float = 10.0
    CHANNELWIDTHCOEFF: float = 2.3
    CHANNELWIDTHEXPNT: float = 0.5
    CHANNELWIDTHFILE: FileDatabasePath = FileDatabasePath()


class MeteorologicalVariables(BaseModel):
    TLINKE: float = 2.0
    MINSNTEMP: float = -27.0
    TEMPLAPSE: float = -0.0065
    PRECLAPSE: float = 0.0
    SNLIQFRAC: float = 0.6


class RunParameters(BaseModel):
    time_variables: TimeVariables = TimeVariables()
    routing_variables: RoutingVariables = RoutingVariables()
    meteorological_variables: MeteorologicalVariables = MeteorologicalVariables()


# Run Options -------------------------------------------------------------------------------------------------------- #
class RunOptions(BaseModel):
    OPTMESHINPUT: OptMeshInput = OptMeshInput.tMesh
    RAINSOURCE: OptRainSource = OptRainSource.rainGauges
    OPTEVAPOTRANS: OptEvapTrans = OptEvapTrans.penmanMonteith
    OPTSNOW: OptSnow = OptSnow.singleLayer
    HILLALBOPT: OptHillAlbedo = OptHillAlbedo.dynamic
    OPTRADSHELT: OptRadShelt = OptRadShelt.local
    OPTINTERCEPT: OptIntercept = OptIntercept.canopyWaterBalance
    OPTLANDUSE: OptLanduse = OptLanduse.dynamic
    OPTLUINTERP: OptLuInterp = OptLuInterp.constant
    GFLUXOPTION: OptGFlux = OptGFlux.forceRestore
    METDATAOPTION: OptMetData = OptMetData.hydroMetGrid
    CONVERTDATA: OptConvertData = OptConvertData.inactive
    OPTBEDROCK: OptBedrock = OptBedrock.gridded
    OPTGROUNDWATER: OptGroundwater = OptGroundwater.moduleOn
    WIDTHINTERPOLATION: OptWidthInterpolation = OptWidthInterpolation.measuredAndObservered
    OPTGWFILE: OptGwFile = OptGwFile.grid
    OPTRUNON: OptRunon = OptRunon.noRunon
    OPTRESERVOIR: OptReservoir = OptReservoir.inactive
    OPTSOILTYPE: OptSoilType = OptSoilType.tabular
    OPTPERCOLATION: OptPercolation = OptPercolation.inactive


# Files and Pathnames ------------------------------------------------------------------------------------------------ #
class MeshGeneration(BaseModel):
    INPUTDATAFILE: FileDatabasePath = FileDatabasePath()
    POINTFILENAME: FileDatabasePath = FileDatabasePath()
    INPUTTIME: int = 0
    ARCINFOFILENAME: FileDatabasePath = FileDatabasePath()


class ResamplingGrids(BaseModel):
    SOILTABLENAME: FileDatabasePath = FileDatabasePath()
    SOILMAPNAME: FileDatabasePath = FileDatabasePath()
    LANDTABLENAME: FileDatabasePath = FileDatabasePath()
    LANDMAPNAME: FileDatabasePath = FileDatabasePath()
    GWATERFILE: FileDatabasePath = FileDatabasePath()
    DEMFILE: FileDatabasePath = FileDatabasePath()
    RAINFILE: FileDatabasePath = FileDatabasePath()
    RAINEXTENSION: str = ""
    DEPTHTOBEDROCK: float = 10.0
    BEDROCKFILE: FileDatabasePath = FileDatabasePath()
    LUGRID: FileDatabasePath = FileDatabasePath()
    SCGRID: FileDatabasePath = FileDatabasePath()


class MeteorologicalData(BaseModel):
    HYDROMETSTATIONS: FileDatabasePath = FileDatabasePath()
    HYDROMETGRID: FileDatabasePath = FileDatabasePath()
    HYDROMETCONVERT: FileDatabasePath = FileDatabasePath()
    HYDROMETBASENAME: FileDatabasePath = FileDatabasePath()
    GAUGESTATIONS: FileDatabasePath = FileDatabasePath()
    GAUGECONVERT: FileDatabasePath = FileDatabasePath()
    GAUGEBASENAME: FileDatabasePath = FileDatabasePath()


class ReservoirData(BaseModel):
    RESPOLYGONID: FileDatabasePath = FileDatabasePath()
    RESDATA: FileDatabasePath = FileDatabasePath()


class OutputData(BaseModel):
    OUTFILENAME: FileDatabasePathCollection = FileDatabasePathCollection()
    OUTHYDROFILENAME: FileDatabasePathCollection = FileDatabasePathCollection()
    OUTHYDROEXTENSION: str = "mrf"
    RIBSHYDOUTPUT: int = 0
    NODEOUTPUTLIST: FileDatabasePath = FileDatabasePath()
    HYDRONODELIST: FileDatabasePath = FileDatabasePath()
    OUTLETNODELIST: FileDatabasePath = FileDatabasePath()
    OPTSPATIAL: OptSpatial = OptSpatial.spatialoutputOn
    OPTINTERHYDRO: OptInterhydro = OptInterhydro.intermediatehydrographsOff
    OPTHEADER: OptHeader = OptHeader.outputheadersOn


class FilesAndPathnames(BaseModel):
    mesh_generation: MeshGeneration = MeshGeneration()
    resampling_grids: ResamplingGrids = ResamplingGrids()
    meteorological_data: MeteorologicalData = MeteorologicalData()
    output_data: OutputData = OutputData()
    reservoir_data: ReservoirData = ReservoirData()


# Modes -------------------------------------------------------------------------------------------------------------- #
class RainfallForecasting(BaseModel):
    FORECASTMODE: OptForecastMode = OptForecastMode.inactive
    FORECASTTIME: float | None = None
    FORECASTLEADTIME: float | None = None
    FORECASTLENGTH: float | None = None
    FORECASTFILE: FileDatabasePath = FileDatabasePath()
    CLIMATOLOGY: float | None = None
    RAINDISTRIBUTION: OptRainDistribution = OptRainDistribution.spatiallyDistRadar


class StochasticClimateForcing(BaseModel):
    STOCHASTICMODE: OptStochasticMode = OptStochasticMode.inactive
    PMEAN: float = 0
    STDUR: float = 0
    ISTDUR: float = 0
    SEED: float = 0.5
    PERIOD: float | None = None
    MAXPMEAN: float | None = None
    MAXSTDURMN: float | None = None
    MAXISTDURMN: float | None = None
    WEATHERTABLENAME: FileDatabasePath = FileDatabasePath()


class RestartMode(BaseModel):
    RESTARTMODE: OptRestartMode = OptRestartMode.inactive
    RESTARTINTRVL: float = 8760.0
    RESTARTDIR: FileDatabasePath = FileDatabasePath()
    RESTARTFILE: FileDatabasePath = FileDatabasePath()


class ParallelMode(BaseModel):
    PARALLELMODE: OptParallelMode = OptParallelMode.parallel
    GRAPHOPTION: OptGraph = OptGraph.default
    GRAPHFILE: FileDatabasePath = FileDatabasePath()


class Modes(BaseModel):
    rainfall_forecasting: RainfallForecasting = RainfallForecasting()
    stochastic_climate_forcing: StochasticClimateForcing = StochasticClimateForcing()
    restart: RestartMode = RestartMode()
    parallel: ParallelMode = ParallelMode()


class VisualizationOptions(BaseModel):
    OPTVIZ: OptViz = OptViz.inactive
    OUTVIZFILENAME: FileDatabasePath = FileDatabasePath()


# Base Model --------------------------------------------------------------------------------------------------------- #
class tRIBSInput(BaseModel):
    file_name: str = ""
    run_parameters: RunParameters = RunParameters()
    run_options: RunOptions = RunOptions()
    files_and_pathnames: FilesAndPathnames = FilesAndPathnames()
    modes: Modes = Modes()
    visualization: VisualizationOptions = VisualizationOptions()

    @unique
    class FilesMode(StrEnum):
        """tRIBS Model Input File Mode Flags."""
        ALL_FILES = auto()
        INPUT_ONLY = auto()
        OUTPUT_ONLY = auto()

    @property
    def input_file_cards(self):
        """Returns a list of all the cards associated with input files."""
        if not getattr(self, '_input_file_cards', None):
            self._input_file_cards = [c for c in FILE_TO_DATASET.keys() if FILE_TO_DATASET[c]['is_input'] is True]
        return self._input_file_cards

    @property
    def output_file_cards(self):
        """Returns a list of all the cards associated with output files."""
        if not getattr(self, '_output_file_cards', None):
            self._output_file_cards = [c for c in FILE_TO_DATASET.keys() if FILE_TO_DATASET[c]['is_output'] is True]
        return self._output_file_cards

    @property
    def xdf_cards(self):
        """Returns a list of all the cards that point to SDF and GDF files."""
        if not getattr(self, '_xdf_cards', None):
            self._xdf_cards = ['HYDROMETSTATIONS', 'GAUGESTATIONS', 'HYDROMETGRID', 'LUGRID', 'SCGRID']
        return self._xdf_cards

    @classmethod
    def from_input_file(cls, input_file: Path | str) -> "tRIBSInput":
        """Create a new tRIBSInput instance from the contents of the given tRIBS Model Input File (*.in)."""
        flat_dict = parse_in_file(input_file)
        input_file_name = Path(input_file).name
        return cls.from_flat_dict(flat_dict, input_file_name)

    @classmethod
    def from_flat_dict(cls, flat_dict: dict[str, Any], input_file_name: str) -> "tRIBSInput":
        """Create a new tRIBSInput instance from the given flat dictionary of tRIBS Model Input File data."""
        # Run Parameters
        time_variables = TimeVariables(**flat_dict)
        routing_variables = RoutingVariables(**flat_dict)
        run_parameters = RunParameters(time_variables=time_variables, routing_variables=routing_variables)

        # Run Options
        run_options = RunOptions(**flat_dict)

        # Files and Pathnames
        mesh_generation = MeshGeneration(**flat_dict)
        resampling_grids = ResamplingGrids(**flat_dict)
        meteorological_data = MeteorologicalData(**flat_dict)
        reservoir_data = ReservoirData(**flat_dict)
        output_data = OutputData(**flat_dict)
        files_and_pathnames = FilesAndPathnames(
            mesh_generation=mesh_generation,
            resampling_grids=resampling_grids,
            meteorological_data=meteorological_data,
            reservoir_data=reservoir_data,
            output_data=output_data
        )

        # Modes
        rainfall_forecasting = RainfallForecasting(**flat_dict)
        stochastic_climate_forcing = StochasticClimateForcing(**flat_dict)
        restart_mode = RestartMode(**flat_dict)
        parallel_mode = ParallelMode(**flat_dict)
        modes = Modes(
            rainfall_forecasting=rainfall_forecasting,
            stochastic_climate_forcing=stochastic_climate_forcing,
            restart=restart_mode,
            parallel=parallel_mode
        )

        # Visualization
        visualization_options = VisualizationOptions(**flat_dict)

        tribs_input = cls(
            file_name=input_file_name,
            run_parameters=run_parameters,
            run_options=run_options,
            files_and_pathnames=files_and_pathnames,
            modes=modes,
            visualization=visualization_options
        )

        return tribs_input

    def copy_update(self, update_dict: dict) -> "tRIBSInput":
        """Returns a new instance of the tRIBSInput with values updated from the given dictionary."""
        def flatten(d):
            def _flatten(d):
                file_collection_keys = ['file_database_paths', 'resource_id', 'file_collection_id']
                items = []
                for k, v in d.items():
                    if isinstance(v, dict) and not any([i in v for i in file_collection_keys]):
                        items.extend(_flatten(v))
                    else:
                        items.append((k, v))
                return items

            return dict(_flatten(d))

        self_dict = self.model_dump()
        self_flat = flatten(self_dict)
        update_flat = flatten(update_dict)
        self_flat.update(update_flat)
        return tRIBSInput.from_flat_dict(self_flat, self_flat["file_name"])

    def to_input_file(self, path: Path | str) -> Path:
        """Export this tRIBSInput instance to the tRIBS Model Input File format (*.in).

        Args:
            path: File path or directory to write the tRIBS Model Input File to.

        Returns:
            Path to the written tRIBS Model Input File.
        """
        # Ensure path is a Path object
        path = Path(path)

        # Existing directory given
        if path.exists() and path.is_dir():
            path = path / self.file_name if self.file_name else path / "tRIBS.in"

        # Non-existing directory given
        elif not path.exists() and not path.suffix:
            path.mkdir(parents=True, exist_ok=True)
            path = path / self.file_name if self.file_name else path / "tRIBS.in"

        # Export model data to Python dict for template context
        context = self.model_dump()
        rendered = renderer.render('input_file.in.jinja', context)
        with open(path, 'w') as f:
            f.write(rendered)
        return path

    def files(self, /, mode: FilesMode = FilesMode.ALL_FILES) -> Generator[Tuple[str, FileDatabasePath], None, None]:
        """Generator that yields all file fields referenced in the tRIBS Model Input File.

        Args:
            mode: Mode flag to filter the yielded file fields by. Defaults to FilesMode.ALL_FILES.
        """

        # Recursively yield all FileDatabasePath fields in the model
        def _yield_file_fields(model: BaseModel) -> Generator[FileDatabasePath, None, None]:
            # Note: model_fields_set only yields fields that were set during initialization
            for card in model.model_fields_set:
                field = getattr(model, card)
                if isinstance(field, (FileDatabasePath, FileDatabasePathCollection)):
                    if mode == self.FilesMode.INPUT_ONLY and card not in self.input_file_cards:
                        continue  # Skip non-input file fields
                    elif mode == self.FilesMode.OUTPUT_ONLY and card not in self.output_file_cards:
                        continue  # Skip non-output file fields
                    yield card, field
                elif isinstance(field, BaseModel):
                    yield from _yield_file_fields(field)

        yield from _yield_file_fields(self)

    def get_value(self, card: str, default: Any = None) -> str | Any:
        """Get the value of the given card.

        Args:
            card: The card to get the value of.

        Returns:
            The value of the given card.
        """

        # Recursively yield all FileDatabasePath fields in the model
        def _get_card_value(model: BaseModel, card: str) -> str | None:
            # Note: model_fields_set only yields fields that were set during initialization
            for c in model.model_fields_set:
                field = getattr(model, c)
                if c == card:
                    return field
                elif isinstance(field, BaseModel):
                    val = _get_card_value(field, card)
                    if val is not None:
                        return val
            return None

        val = _get_card_value(self, card)

        return val if val is not None else default

    def set_value(self, card: str, value: Any) -> None:
        """Set the value of the given card.

        Args:
            card: The card to set the value of.
            value: The value to set the card to.

        Returns:
            The updated tRIBSInput instance.
        """

        # Recursively yield all FileDatabasePath fields in the model
        def _set_card_value(model: BaseModel, card: str, value: Any) -> None:
            # Note: model_fields_set only yields fields that were set during initialization
            for c in model.model_fields_set:
                field = getattr(model, c)
                if c == card:
                    setattr(model, c, value)
                elif isinstance(field, BaseModel):
                    _set_card_value(field, card, value)

        _set_card_value(self, card, value)
        return self

    def get_expected_file_extensions(self, card: str) -> list[str]:
        """Get the expected file extensions for the given card.

        Args:
            card: The card to get the expected file extensions for.

        Returns:
            The expected file extensions for the given card.
        """
        dataset_attrs = FILE_TO_DATASET.get(card, None)
        if dataset_attrs is None:
            raise ValueError(f"Invalid card: card must be one of: {list(FILE_TO_DATASET.keys())}")

        file_extensions = copy.deepcopy(dataset_attrs.get('file_extensions', []))
        for i, file_extension in enumerate(file_extensions):
            # Look up extension from specified card value (e.g.: "card:OUTHYDROEXTENSION")
            if file_extension.startswith("card:"):
                file_extension_card = file_extension.split(":")[1]
                file_extension_card_value = self.get_value(file_extension_card)
                if file_extension_card_value:
                    # Replace the "card:<extensioncard>" with the actual extension value
                    file_extensions[i] = file_extension_card_value
                else:
                    # No value provided in extension card, so remove "card:<extensioncard>"
                    file_extensions.pop(i)
        return file_extensions

    def expand_paths(self, card: str, model_root: Path | str, only_existing: bool = True) -> list[Path]:
        """Expand basename and directory paths and validate file paths for a given file card.

        Args:
            card: The card to expand paths for.

        Returns:
            A list of expanded file paths.
        """
        dataset_attrs = FILE_TO_DATASET.get(card, None)
        if dataset_attrs is None:
            raise ValueError(f"Invalid card: card must be one of: {list(FILE_TO_DATASET.keys())}")

        # Determine expected file_extensions
        expected_file_extensions = self.get_expected_file_extensions(card)

        # Get file path / pattern that is specified in the input file
        file_path = Path(model_root) / self.get_value(card).path
        expanded_file_paths = []
        file_expected = not dataset_attrs.get('is_directory', False) and not dataset_attrs.get('is_basename', False)

        # File cards
        if file_expected:
            if file_path.is_dir():
                warnings.warn(
                    f'Card "{card}" expects file value to be a file path, '
                    f'but value "{file_path}" is a directory. Skipping.',
                    stacklevel=2
                )
                return []
            elif expected_file_extensions and not any([file_path.name.endswith(e) for e in expected_file_extensions]):
                warnings.warn(
                    f'Card "{card}" expects a file with one of the following extensions: '
                    f'{", ".join(expected_file_extensions)}, but value is "{str(file_path)}". Skipping.',
                    stacklevel=2
                )
                return []
            expanded_file_paths = [file_path]

        # Expand directory
        elif dataset_attrs.get('is_directory', False):
            for e in expected_file_extensions:
                expanded_file_paths.extend([p for p in file_path.glob(f'**/*{e}')])

        # Expand basename
        else:
            path_dir = file_path.parent
            basename = file_path.name
            for e in expected_file_extensions:
                expanded_file_paths.extend(path_dir.glob(f'{basename}*{e}'))

        # Collect only existing files
        if not only_existing:
            return expanded_file_paths

        existing_file_paths = []
        for f in expanded_file_paths:
            if f.exists():
                existing_file_paths.append(f)
            else:
                warnings.warn(f'Card "{card}" expects file "{f}", but it does not exist.', stacklevel=2)

        # Handle files listed in SDF and GDF files
        if card in self.xdf_cards and len(existing_file_paths) >= 1:
            for f in existing_file_paths:
                existing_file_paths.extend(self.paths_from_xdf(model_root, f))

        # Handle group by file extension
        if dataset_attrs.get('group_by_file_extension', False):
            grouped_file_paths = {}
            for e in expected_file_extensions:
                grouped_file_paths[e] = [p for p in existing_file_paths if p.name.endswith(e)]
            existing_file_paths = grouped_file_paths

        return existing_file_paths

    def paths_from_xdf(self, model_root: Path | str, file_path: Path | str) -> list[Path]:
        """Extact a list of files from an SDF or GDF file.

        Args:
            model_root: The root directory of the model files.
            file_path: The path to the SDF or GDF file.

        Returns:
            A list of paths to files listed in the SDF or GDF file.
        """
        GDF = '.gdf'
        SDF = '.sdf'
        paths = []
        model_root = Path(model_root)
        file_path = Path(file_path)

        with file_path.open() as f:
            lines = f.readlines()

        # Skip lines that don't list files
        if file_path.suffix == SDF:
            lines = lines[1:]  # First line
        elif file_path.suffix == GDF:
            lines = lines[2:]  # First two lines

        for line in lines:
            cols = line.split()

            # SDF: StationID FilePath Param1 or GDF: ParamN or Param GridFilePath GridExtension
            nested_file_path = model_root / Path(cols[1])

            if file_path.suffix == SDF:
                if not nested_file_path.exists():
                    warnings.warn(
                        f'File "{file_path.name}" expects file "{nested_file_path}", '
                        'but it does not exist.',
                        stacklevel=2
                    )
                    continue
                paths.append(nested_file_path)

            if file_path.suffix == GDF:
                # File
                if nested_file_path.is_file():
                    paths.append(nested_file_path)
                    continue
                # Directory
                elif nested_file_path.is_dir():
                    nested_file_paths = [p for p in nested_file_path.glob(f'*{cols[2]}')]
                # Basename
                else:
                    nested_file_paths = [p for p in nested_file_path.parent.glob(f'{nested_file_path.name}*{cols[2]}')]

                if nested_file_paths:
                    for n in nested_file_paths:
                        paths.append(n)
                else:
                    warnings.warn(
                        f'GDF file "{file_path.name}" expects file "{nested_file_path}" with extension "{cols[2]}", '
                        'but it could not be found.',
                        stacklevel=2
                    )

        return paths
