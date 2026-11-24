"""Metadata for tRIBS output variables: friendly labels, display units and the priority tier of each column.

Generated from the scientist's sheet ``tRIBS_v5.3.1_output_variables.xlsx`` (streamflow ``.qout``, basin averages
``.mrf``, integrated spatial ``_i`` and dynamic spatial ``_d`` files); names, labels and descriptions are the sheet's
text. Pixel, ``.rft`` and station variables are not covered yet: they keep their raw names and all stay visible.

Lookups are by exact column name or one of the explicit ``aliases`` seen in real files (older tRIBS builds wrote
``MGW`` for ``MDGW`` and ``Aspct`` for ``Aspect``); nothing is matched fuzzily.
"""
from dataclasses import dataclass
from enum import Enum

from tribs_adapter.common.dataset_types import DatasetTypes


class Tier(str, Enum):
    """How prominently a variable is offered: PRIORITY first, SECONDARY in a collapsed group, HIDE/IGNORE not at all."""
    PRIORITY = 'priority'
    SECONDARY = 'secondary'
    HIDE = 'hide'
    IGNORE = 'ignore'
    INDEX = 'index'  # Time, node ID: not a variable


@dataclass(frozen=True)
class OutputVariable:
    name: str  # canonical column name
    label: str
    file_units: str | None  # as written in the file
    display_units: str | None  # as shown to users; display value = file value * factor
    tier: Tier
    factor: float = 1.0
    description: str = ''
    aliases: tuple = ()  # other column names used for this variable in real files


@dataclass(frozen=True)
class DerivedVariable:
    """A variable that is not a column of the file but the sum of some of its columns, each times a factor.

    The factors convert to display units, so the result has ``factor`` 1. A term marked ``per_met_step`` is a depth
    accumulated over one meteorological time step (METSTEP); its factor gives the depth per hour for a step of one
    hour and is divided by the length of the step in hours (see ``derived_terms``).
    """
    name: str  # layer name; never the name of a column tRIBS writes
    label: str
    display_units: str | None
    tier: Tier
    description: str
    terms: tuple  # ((column, factor, per_met_step), ...)
    factor: float = 1.0
    aliases: tuple = ()

    @property
    def sources(self):
        """The columns the variable is computed from. They are not offered by themselves when it is."""
        return tuple(column for column, _, _ in self.terms)


QOUT = 'qout'
MRF = 'mrf'
INTEGRATED = 'integrated'
DYNAMIC = 'dynamic'

KIND_BY_DATASET_TYPE = {
    DatasetTypes.TRIBS_OUT_QOUT: QOUT,
    DatasetTypes.TRIBS_OUT_MRF: MRF,
    DatasetTypes.TRIBS_OUT_TIME_INTEGRATED: INTEGRATED,
    DatasetTypes.TRIBS_OUT_TIME_DYNAMIC: DYNAMIC,
}

# Header unit tokens of pixel/qout files (``Nwt_mm``, ``Qstrm_m3-s``) as shown to users; ``[]`` means no units.
UNIT_TOKEN_NAMES = {
    '[]': None,
    'mm': 'mm',
    'm': 'm',
    'm3-h': 'm³/hr',
    'm3-s': 'm³/s',
    'm2-s': 'm²/s',
    'W-m2': 'W/m²',
    'oC': '°C',
    'd-l': 'd/L',
    'm-s': 'm/s',
    'mm-h': 'mm/hr',
    'mm-hr': 'mm/hr',
    'Pa': 'Pa',
}

OUTPUT_VARIABLES = {
    QOUT: (
        OutputVariable(
            'Time',
            'Time',
            'hr',
            'hr',
            Tier.INDEX,
            description=(
                'Elapsed simulation time since model start, in decimal hours. Timestamp marks the END of the model '
                'time step.'
            ),
        ),
        OutputVariable(
            'Qstrm',
            'Streamflow',
            'm3/s',
            'm³/s',
            Tier.PRIORITY,
            description=(
                'Routed channel discharge at the node (basin outlet for _Outlet.qout, or the interior node for '
                '<base>_<NodeID>.qout).'
            ),
        ),
        OutputVariable('Hlev', 'Stream Stage (Flow Depth)', 'm', None, Tier.HIDE),
    ),
    MRF: (
        OutputVariable(
            'Time',
            'Time',
            'hr',
            'hr',
            Tier.INDEX,
            description=('Simulation time at the END of each output interval (OPINTRVL).'),
        ),
        OutputVariable(
            'Srf',
            'Basin Runoff Discharge',
            'm3/s',
            'm³/s',
            Tier.SECONDARY,
            description=('Basin runoff hydrograph at the outlet from the flow-results accumulator.'),
        ),
        OutputVariable(
            'MAP',
            'Mean Areal Precipitation',
            'mm/hr',
            'mm/hr',
            Tier.PRIORITY,
            description=('Basin-average precipitation rate.'),
        ),
        OutputVariable('RainMax', 'Maximum Precipitation Rate', 'mm/hr', None, Tier.IGNORE, aliases=('Max', )),
        OutputVariable('RainMin', 'Minimum Precipitation Rate', 'mm/hr', None, Tier.IGNORE, aliases=('Min', )),
        OutputVariable('FState', 'Forecast State', 'flag', None, Tier.IGNORE),
        OutputVariable(
            'MSM100',
            'Surface Soil Moisture (Top 10 cm)',
            '[-]',
            '% saturation',
            Tier.SECONDARY,
            factor=100.0,
            description=('Basin-average relative saturation (θ/θs) of the top 100 mm of soil.'),
        ),
        OutputVariable(
            'MSMRt',
            'Root-Zone Soil Moisture',
            '[-]',
            '% saturation',
            Tier.PRIORITY,
            factor=100.0,
            description=('Basin-average relative saturation (θ/θs) of the top 1m of soil.'),
        ),
        OutputVariable(
            'MSMU',
            'Unsaturated-Zone Soil Moisture',
            '[-]',
            '% saturation',
            Tier.SECONDARY,
            factor=100.0,
            description=(
                'Basin-average relative saturation of the whole unsaturated zone (surface down to the water table).'
            ),
        ),
        OutputVariable(
            'MDGW',
            'Depth to Groundwater',
            'mm',
            'm',
            Tier.PRIORITY,
            factor=0.001,
            aliases=('MGW', ),
            description=('Basin-average depth from the land surface to the water table (vertical). Larger = deeper.'),
        ),
        OutputVariable(
            'MET',
            'Evapotranspiration',
            'mm/hr',
            'mm/hr',
            Tier.PRIORITY,
            description=('Basin-average total evapotranspiration rate.'),
        ),
        OutputVariable('SatPercent', 'Saturated Area Fraction', '[-]', None, Tier.HIDE, aliases=('%Sat', )),
        OutputVariable('RainPercent', 'Raining Area Fraction', '[-]', None, Tier.HIDE, aliases=('%Rain', )),
        OutputVariable(
            'AvSWE',
            'Snow Water Equivalent',
            'cm',
            'mm',
            Tier.PRIORITY,
            factor=10.0,
            description=('Basin-average snow water equivalent (ice + liquid) of the snowpack.'),
        ),
        OutputVariable(
            'AvMelt',
            'Snowmelt',
            'cm',
            'mm',
            Tier.SECONDARY,
            factor=10.0,
            description=('Basin-average liquid water released from the snowpack, per snow model time step.'),
        ),
        OutputVariable(
            'AvSnSub',
            'Snowpack Sublimation',
            '-cm',
            'mm',
            Tier.PRIORITY,
            factor=-10.0,
            description=('Basin-average sublimation from the snowpack.'),
        ),
        OutputVariable(
            'AvSnEvap',
            'Snowpack Evaporation',
            '-cm',
            'mm',
            Tier.PRIORITY,
            factor=-10.0,
            description=('Basin-average evaporation of liquid water from the snowpack.'),
        ),
        OutputVariable('AvSTC', 'Snowpack Temperature', '°C', None, Tier.IGNORE),
        OutputVariable('AvDUInt', 'Snowpack Energy Change', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSLHF', 'Snow Latent Heat Flux', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSSHF', 'Snow Sensible Heat Flux', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSPHF', 'Snow Precipitation Heat Flux', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSGHF', 'Snow Ground Heat Flux', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSRLI', 'Snow Incoming Longwave', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSRLO', 'Snow Outgoing Longwave', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSRSI', 'Snow Incoming Shortwave', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvInSn', 'Canopy-Intercepted Snow', 'cm', None, Tier.HIDE),
        OutputVariable(
            'AvInSu',
            'Canopy Snow Sublimation',
            '-cm',
            'mm',
            Tier.PRIORITY,
            factor=-10.0,
            description=('Basin-average sublimation of canopy-intercepted snow.'),
        ),
        OutputVariable('AvInUn', 'Canopy Snow Unloading', 'cm', None, Tier.HIDE),
        OutputVariable(
            'SCA',
            'Snow-Covered Area Fraction',
            '[-]',
            '% of basin',
            Tier.SECONDARY,
            factor=100.0,
            description=('Fraction of basin area covered by snow.'),
        ),
        OutputVariable('ChannelPercolation', 'Channel Transmission Loss', 'm3', None, Tier.HIDE),
        OutputVariable('Qunsat', 'Net Lateral Unsaturated Flow', 'mm/hr', None, Tier.HIDE),
    ),
    INTEGRATED: (
        OutputVariable(
            'ID',
            'Node ID',
            None,
            None,
            Tier.INDEX,
            description=('Mesh node ID. Join to the Voronoi polygons in the _voi file to map.'),
        ),
        OutputVariable('BndCd', 'Boundary Code', 'code', None, Tier.HIDE),
        OutputVariable(
            'Z',
            'Elevation',
            'm',
            'm',
            Tier.PRIORITY,
            description=('Node elevation.'),
        ),
        OutputVariable('VAr', 'Cell Area', 'm2', None, Tier.HIDE),
        OutputVariable(
            'CAr',
            'Contributing Area',
            'km2',
            'km²',
            Tier.SECONDARY,
            description=('Upslope drainage area flowing through the node.'),
        ),
        OutputVariable('Curv', 'Curvature', 'model-internal', None, Tier.HIDE),
        OutputVariable('EdgL', 'Flow Edge Length', 'm', None, Tier.HIDE),
        OutputVariable('Slp', 'Slope', 'm/m', None, Tier.HIDE),
        OutputVariable('FWidth', 'Flow Width', 'm', None, Tier.HIDE),
        OutputVariable('Aspect', 'Aspect', 'radians', None, Tier.HIDE, aliases=('Aspct', )),
        OutputVariable('SV', 'Sky View Factor', '[-]', None, Tier.HIDE),
        OutputVariable('LV', 'Land View Factor', '[-]', None, Tier.HIDE),
        OutputVariable(
            'AvSM',
            'Mean Surface Soil Moisture (Top 10 cm)',
            '[-]',
            '% saturation',
            Tier.PRIORITY,
            factor=100.0,
            description=('Time-averaged relative saturation (θ/θs) of the top 100 mm over the run.'),
        ),
        OutputVariable(
            'AvRtM',
            'Mean Root-Zone Soil Moisture',
            '[-]',
            '% saturation',
            Tier.PRIORITY,
            factor=100.0,
            description=('Time-averaged relative saturation (θ/θs) of the root zone over the run.'),
        ),
        OutputVariable(
            'HOccr',
            'Infiltration-Excess Runoff Occurrences',
            'count',
            'time steps',
            Tier.SECONDARY,
            description=('Number of model time steps with infiltration-excess (Hortonian) runoff.'),
        ),
        OutputVariable(
            'HRt',
            'Mean Infiltration-Excess Runoff Rate',
            'mm/hr',
            'mm/hr',
            Tier.SECONDARY,
            description=('Mean infiltration-excess runoff rate during the time steps when it occurred.'),
        ),
        OutputVariable(
            'SbOccr',
            'Saturation-Excess Runoff Occurrences',
            'count',
            'time steps',
            Tier.SECONDARY,
            description=('Number of model time steps with saturation-excess runoff.'),
        ),
        OutputVariable(
            'SbRt',
            'Mean Saturation-Excess Runoff Rate',
            'mm/hr',
            'mm/hr',
            Tier.SECONDARY,
            description=('Mean saturation-excess runoff rate during the time steps when it occurred.'),
        ),
        OutputVariable('POccr', 'Perched Return-Flow Occurrences', 'count', None, Tier.HIDE),
        OutputVariable('PRt', 'Mean Perched Return-Flow Rate', 'mm/hr', None, Tier.HIDE),
        OutputVariable('SatOccr', 'Groundwater Exfiltration Occurrences', 'count', None, Tier.HIDE),
        OutputVariable('SatRt', 'Mean Groundwater Exfiltration Rate', 'mm/hr', None, Tier.HIDE),
        OutputVariable('SoiSatOccr', 'Surface Saturation Occurrences', 'count', None, Tier.HIDE),
        OutputVariable('RchDsch', 'Cumulative Net Recharge', 'm', None, Tier.HIDE),
        OutputVariable('AvET', 'Mean Evapotranspiration Rate', 'mm/hr', None, Tier.HIDE),
        OutputVariable(
            'EvpFrct',
            'Mean Evaporative Fraction',
            '[-]',
            None,
            Tier.SECONDARY,
            description=('Time-averaged evaporative fraction (share of available energy used for evaporation).'),
        ),
        OutputVariable(
            'cET',
            'Cumulative Evapotranspiration',
            'mm',
            'mm',
            Tier.PRIORITY,
            description=('Total evapotranspiration over the run.'),
        ),
        OutputVariable(
            'cEsoil',
            'Cumulative Soil Evaporation',
            'mm',
            'mm',
            Tier.PRIORITY,
            description=('Total bare-soil evaporation over the run.'),
        ),
        OutputVariable('cLHF', 'Cumulative Snow Latent Heat', 'kJ/m2', None, Tier.HIDE),
        OutputVariable(
            'cMelt',
            'Cumulative Snowmelt',
            'cm',
            'mm',
            Tier.SECONDARY,
            factor=10.0,
            description=('Total liquid water released from the snowpack over the run.'),
        ),
        OutputVariable('cSHF', 'Cumulative Snow Sensible Heat', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cPHF', 'Cumulative Snow Precipitation Heat', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cRLIn', 'Cumulative Incoming Longwave (Snow)', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cRLo', 'Cumulative Outgoing Longwave (Snow)', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cRSIn', 'Cumulative Incoming Shortwave', 'mixed', None, Tier.HIDE),
        OutputVariable('cGHF', 'Cumulative Snow Ground Heat', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cUErr', 'Cumulative Snow Energy Error', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cHrsSun', 'Cumulative Sunlit Hours', 'hr', None, Tier.HIDE),
        OutputVariable('cHrsSnow', 'Snow-Covered Hours', 'hr', None, Tier.HIDE),
        OutputVariable('persTime', 'Longest Continuous Snow Cover', 'hr', None, Tier.HIDE),
        OutputVariable(
            'peakWE',
            'Peak Snow Water Equivalent',
            'cm',
            'mm',
            Tier.PRIORITY,
            factor=10.0,
            description=('Maximum SWE reached at the node during the run.'),
        ),
        OutputVariable('initTime', 'Snow Cover Start Time', 'hr', None, Tier.HIDE),
        OutputVariable('peakTime', 'Peak SWE Time', 'hr', None, Tier.HIDE),
        OutputVariable('cIntSub', 'Cumulative Canopy Snow Sublimation', 'cm', None, Tier.HIDE),
        OutputVariable(
            'cSnSub',
            'Cumulative Snowpack Sublimation',
            'cm',
            'mm',
            Tier.PRIORITY,
            factor=10.0,
            description=('Total sublimation from the ground snowpack.'),
        ),
        OutputVariable(
            'cSnEvap',
            'Cumulative Snowpack Evaporation',
            'cm',
            'mm',
            Tier.PRIORITY,
            factor=10.0,
            description=('Total evaporation of liquid water from the snowpack.'),
        ),
        OutputVariable('cIntUnl', 'Cumulative Canopy Snow Unloading', 'cm', None, Tier.HIDE),
        OutputVariable('AvCanStorParam', 'Canopy Storage Parameter', 'mm', None, Tier.HIDE),
        OutputVariable('AvIntercCoeff', 'Interception Coefficient', '[-]', None, Tier.HIDE),
        OutputVariable('AvTF', 'Free Throughfall Coefficient', '[-]', None, Tier.HIDE),
        OutputVariable('AvCanFieldCap', 'Canopy Field Capacity', 'mm', None, Tier.HIDE),
        OutputVariable('AvDrainCoeff', 'Canopy Drainage Coefficient', 'mm/hr', None, Tier.HIDE),
        OutputVariable('AvDrainExpPar', 'Canopy Drainage Exponent', '1/mm', None, Tier.HIDE),
        OutputVariable('AvLUAlb', 'Surface Albedo', '[-]', None, Tier.HIDE),
        OutputVariable('AvVegHeight', 'Vegetation Height', 'm', None, Tier.HIDE),
        OutputVariable('AvOTCoeff', 'Optical Transmission Coefficient', '[-]', None, Tier.HIDE),
        OutputVariable('AvStomRes', 'Stomatal Resistance', 's/m', None, Tier.HIDE),
        OutputVariable(
            'AvVegFract',
            'Vegetation Fraction',
            '[-]',
            '%',
            Tier.SECONDARY,
            factor=100.0,
            description=('Fraction of the cell covered by vegetation.'),
        ),
        OutputVariable(
            'AvLeafAI',
            'Leaf Area Index',
            'm2/m2',
            'm²/m²',
            Tier.SECONDARY,
            description=('Leaf area index.'),
        ),
        OutputVariable('AvEvapThresh', 'Soil Evaporation Threshold', '[-]', None, Tier.HIDE),
        OutputVariable('AvTransThresh', 'Transpiration Threshold', '[-]', None, Tier.HIDE),
        OutputVariable('Bedrock_Depth_mm', 'Depth to Bedrock', 'mm', None, Tier.HIDE),
        OutputVariable('Ks', 'Saturated Hydraulic Conductivity', 'mm/hr', None, Tier.HIDE),
        OutputVariable('ThetaS', 'Saturated Water Content', '[-]', None, Tier.HIDE),
        OutputVariable('ThetaR', 'Residual Water Content', '[-]', None, Tier.HIDE),
        OutputVariable('PoreSize', 'Pore-Size Distribution Index', '[-]', None, Tier.HIDE),
        OutputVariable('AirEBubPress', 'Air Entry Bubbling Pressure', 'mm', None, Tier.HIDE),
        OutputVariable('DecayF', 'Conductivity Decay Parameter', '1/mm', None, Tier.HIDE),
        OutputVariable('SatAnRatio', 'Saturated Anisotropy Ratio', '[-]', None, Tier.HIDE),
        OutputVariable('UnsatAnRatio', 'Unsaturated Anisotropy Ratio', '[-]', None, Tier.HIDE),
        OutputVariable('Porosity', 'Porosity', '[-]', None, Tier.HIDE),
        OutputVariable('VolHeatCond', 'Soil Thermal Conductivity', 'J/(m·s·K)', None, Tier.HIDE),
        OutputVariable('SoilHeatCap', 'Soil Heat Capacity', 'J/(m³·K)', None, Tier.HIDE),
        OutputVariable('SoilID', 'Soil Class', 'class ID', None, Tier.HIDE),
        OutputVariable('LandUseID', 'Land-Use Class', 'class ID', None, Tier.HIDE),
    ),
    DYNAMIC: (
        OutputVariable(
            'ID',
            'Node ID',
            None,
            None,
            Tier.INDEX,
            description=('Mesh node ID. Join to the Voronoi polygons in the _voi file to map.'),
        ),
        OutputVariable(
            'Nwt',
            'Depth to Groundwater',
            'mm',
            'm',
            Tier.PRIORITY,
            factor=0.001,
            description=('Depth from the land surface to the water table (vertical). Larger = deeper.'),
        ),
        OutputVariable('Mu', 'Unsaturated-Zone Water Storage', 'mm', None, Tier.HIDE),
        OutputVariable('Mi', 'Initial Unsaturated-Zone Storage', 'mm', None, Tier.IGNORE),
        OutputVariable('Nf', 'Wetting Front Depth', 'mm', None, Tier.HIDE),
        OutputVariable('Nt', 'Top Front Depth', 'mm', None, Tier.HIDE),
        OutputVariable('Qpout', 'Lateral Unsaturated Outflow', 'mm/hr', None, Tier.HIDE),
        OutputVariable('Qpin', 'Lateral Unsaturated Inflow', 'mm/hr', None, Tier.HIDE),
        OutputVariable(
            'Srf',
            'Surface Runoff',
            'mm',
            'mm',
            Tier.SECONDARY,
            description=(
                'Runoff generated at the cell (all mechanisms) since the last ET time step boundary (ETISTEP, '
                'usually 1 hr). Depth for the last ETISTEP only, not a total since the previous file.'
            ),
        ),
        OutputVariable(
            'Rain',
            'Precipitation',
            'mm/hr',
            'mm/hr',
            Tier.PRIORITY,
            description=(
                'Precipitation rate at the cell (rain or snow). Rate at the time of output, not a total since the'
                ' previous file.'
            ),
        ),
        OutputVariable('ST', 'Snowpack Temperature', '°C', None, Tier.IGNORE),
        OutputVariable(
            'IWE',
            'Snowpack Ice',
            'cm',
            'mm',
            Tier.PRIORITY,
            factor=10.0,
            description=('Ice portion of the snow water equivalent. Snow water equivalent (SWE) = IWE + LWE.'),
        ),
        OutputVariable(
            'LWE',
            'Snowpack Liquid Water',
            'cm',
            'mm',
            Tier.PRIORITY,
            factor=10.0,
            description=('Liquid portion of the snow water equivalent. Snow water equivalent (SWE) = IWE + LWE.'),
        ),
        OutputVariable(
            'SnSub',
            'Snowpack Sublimation',
            '-cm',
            'mm',
            Tier.PRIORITY,
            factor=-10.0,
            description=(
                'Sublimation from the ground snowpack. Value for the last met time step only (METSTEP, usually 1 '
                'hr), not a total since the previous file.'
            ),
        ),
        OutputVariable(
            'SnEvap',
            'Snowpack Evaporation',
            '-cm',
            'mm',
            Tier.PRIORITY,
            factor=-10.0,
            description=(
                'Evaporation of liquid water from the ground snowpack. Value for the last met time step only '
                '(METSTEP, usually 1 hr), not a total since the previous file.'
            ),
        ),
        OutputVariable(
            'SnMelt',
            'Snowmelt',
            'cm',
            'mm',
            Tier.SECONDARY,
            factor=10.0,
            description=(
                'Liquid water released from the snowpack. Value for the last met time step only (METSTEP, usually'
                ' 1 hr), not a total since the previous file.'
            ),
        ),
        OutputVariable('Upack', 'Snowpack Internal Energy', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('sLHF', 'Snow Latent Heat Flux', 'W/m2', None, Tier.IGNORE),
        OutputVariable('sSHF', 'Snow Sensible Heat Flux', 'W/m2', None, Tier.IGNORE),
        OutputVariable('sGHF', 'Snow Ground Heat Flux', 'W/m2', None, Tier.IGNORE),
        OutputVariable('sPHF', 'Snow Precipitation Heat Flux', 'W/m2', None, Tier.IGNORE),
        OutputVariable('sRLo', 'Snow Outgoing Longwave', 'W/m2', None, Tier.IGNORE),
        OutputVariable('sRLi', 'Snow Incoming Longwave', 'W/m2', None, Tier.IGNORE),
        OutputVariable('sRSi', 'Snow Absorbed Shortwave', 'W/m2', None, Tier.IGNORE),
        OutputVariable('Uerr', 'Snow Energy Error', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('IntSWE', 'Canopy-Intercepted Snow', 'cm', None, Tier.HIDE),
        OutputVariable(
            'IntSub',
            'Canopy Snow Sublimation',
            '-cm',
            'mm',
            Tier.PRIORITY,
            factor=-10.0,
            description=(
                'Sublimation of canopy-intercepted snow (cell average). Value for the last met time step only '
                '(METSTEP, usually 1 hr), not a total since the previous file.'
            ),
        ),
        OutputVariable('IntUnl', 'Canopy Snow Unloading', 'cm', None, Tier.HIDE),
        OutputVariable(
            'SoilMoist',
            'Surface Soil Moisture (Top 10 cm)',
            '[-]',
            '% saturation',
            Tier.PRIORITY,
            factor=100.0,
            description=('Relative saturation (θ/θs) of the top 100 mm of soil.'),
        ),
        OutputVariable(
            'RootMoist',
            'Root-Zone Soil Moisture',
            '[-]',
            '% saturation',
            Tier.PRIORITY,
            factor=100.0,
            description=('Relative saturation (θ/θs) of the top 1m of soil.'),
        ),
        OutputVariable('CanStorage', 'Canopy Water Storage', 'mm', None, Tier.HIDE, aliases=('CanStorg', )),
        OutputVariable('ActEvp', 'Actual Evaporation (Intermediate)', 'mm/hr', None, Tier.IGNORE),
        OutputVariable(
            'EvpSoil',
            'Soil Evaporation',
            'mm/hr',
            'mm/hr',
            Tier.PRIORITY,
            description=('Bare-soil evaporation rate (cell average). Already included in ET. 0 under snow.'),
        ),
        OutputVariable(
            'ET',
            'Evapotranspiration',
            'mm/hr',
            'mm/hr',
            Tier.PRIORITY,
            description=(
                'Total evapotranspiration rate: wet canopy evaporation + transpiration + soil evaporation (cell '
                'average). Rate at the time of output, not a total since the previous file. Does not include snow'
                ' losses.'
            ),
        ),
        OutputVariable(
            'GFlux',
            'Ground Heat Flux',
            'W/m2',
            'W/m²',
            Tier.SECONDARY,
            description=('Ground heat flux at the land surface. Set to 0 under snow.'),
        ),
        OutputVariable(
            'HFlux',
            'Sensible Heat Flux',
            'W/m2',
            'W/m²',
            Tier.SECONDARY,
            description=('Sensible heat flux at the land surface. Set to 0 under snow.'),
        ),
        OutputVariable(
            'LFlux',
            'Latent Heat Flux',
            'W/m2',
            'W/m²',
            Tier.SECONDARY,
            description=('Latent heat flux at the land surface. Set to 0 under snow.'),
        ),
        OutputVariable(
            'Qstrm',
            'Streamflow',
            'm3/s',
            'm³/s',
            Tier.SECONDARY,
            description=('Channel discharge at stream nodes; 0 elsewhere.'),
        ),
        OutputVariable('Hlev', 'Stream Stage (Flow Depth)', 'm', None, Tier.HIDE),
        OutputVariable('FlwVlc', 'Flow Velocity', 'm/s', None, Tier.HIDE),
        OutputVariable('CanStorParam', 'Canopy Storage Parameter', 'mm', None, Tier.HIDE),
        OutputVariable('IntercepCoeff', 'Interception Coefficient', '[-]', None, Tier.HIDE),
        OutputVariable('ThroughFall', 'Free Throughfall Coefficient', '[-]', None, Tier.HIDE),
        OutputVariable('CanFieldCap', 'Canopy Field Capacity', 'mm', None, Tier.HIDE),
        OutputVariable('DrainCoeff', 'Canopy Drainage Coefficient', 'mm/hr', None, Tier.HIDE),
        OutputVariable('DrainExpPar', 'Canopy Drainage Exponent', '1/mm', None, Tier.HIDE),
        OutputVariable('LandUseAlb', 'Surface Albedo', '[-]', None, Tier.HIDE),
        OutputVariable('VegHeight', 'Vegetation Height', 'm', None, Tier.HIDE),
        OutputVariable('OptTransmCoeff', 'Optical Transmission Coefficient', '[-]', None, Tier.HIDE),
        OutputVariable('StomRes', 'Stomatal Resistance', 's/m', None, Tier.HIDE),
        OutputVariable(
            'VegFraction',
            'Vegetation Fraction',
            '[-]',
            '%',
            Tier.SECONDARY,
            factor=100.0,
            description=('Fraction of the cell covered by vegetation.'),
        ),
        OutputVariable(
            'LeafAI',
            'Leaf Area Index',
            'm2/m2',
            'm²/m²',
            Tier.SECONDARY,
            description=('Leaf area index.'),
        ),
    ),
}

# Variables the dynamic sheet asks to be shown combined rather than column by column.
DERIVED_VARIABLES = {
    DYNAMIC: (
        DerivedVariable(
            'SnowWE',
            'Snow Water Equivalent',
            'mm',
            Tier.PRIORITY,
            'Snow water equivalent of the snowpack: its ice plus its liquid water (IWE + LWE).',
            terms=(('IWE', 10.0, False), ('LWE', 10.0, False)),
        ),
        DerivedVariable(
            'TotalET',
            'Evapotranspiration',
            'mm/hr',
            Tier.PRIORITY,
            (
                'Total evapotranspiration rate including the snow losses: wet canopy evaporation, transpiration and '
                'soil evaporation (ET) plus snowpack sublimation, snowpack evaporation and canopy snow sublimation '
                '(SnSub, SnEvap and IntSub over the last met time step).'
            ),
            # The snow losses are written as negative centimetres per met time step
            terms=(('ET', 1.0, False), ('SnSub', -10.0, True), ('SnEvap', -10.0, True), ('IntSub', -10.0, True)),
        ),
    ),
}

_INDEX = {
    kind: {
        alias: variable
        for variable in variables
        for alias in (variable.name, *variable.aliases)
    }
    for kind, variables in OUTPUT_VARIABLES.items()
}
for _kind, _derived in DERIVED_VARIABLES.items():
    _INDEX[_kind].update({variable.name: variable for variable in _derived})

_TIER_ORDER = {Tier.PRIORITY: 0, Tier.SECONDARY: 1}
_OFFERED_TIERS = (Tier.PRIORITY, Tier.SECONDARY)


def kind_for_dataset_type(dataset_type):
    """The variable table (``QOUT``, ``MRF``, ``INTEGRATED``, ``DYNAMIC``) for a dataset type; None when it has none."""
    return KIND_BY_DATASET_TYPE.get(dataset_type)


def lookup(kind, name):
    """The ``OutputVariable`` (or ``DerivedVariable``) called ``name`` (or aliased to it) in the table ``kind``; None
    when unknown."""
    if kind is None or name is None:
        return None
    return _INDEX.get(kind, {}).get(name)


def derived_variables(kind, columns):
    """The derived variables of the table ``kind`` that can be computed from ``columns``: those whose source columns
    are all there. Without a table, or when a source is missing, there are none (the columns are then offered by
    themselves)."""
    columns = set(columns)
    return [variable for variable in DERIVED_VARIABLES.get(kind, ()) if columns.issuperset(variable.sources)]


def derived_terms(variable, met_step_hours=1.0):
    """The ``(column, factor)`` pairs a derived variable is the sum of, for a meteorological time step of
    ``met_step_hours`` (METSTEP in hours; anything but a positive number counts as one hour)."""
    valid = isinstance(met_step_hours, (int, float)) and not isinstance(met_step_hours, bool) and met_step_hours > 0
    hours = float(met_step_hours) if valid else 1.0
    return [(column, factor / hours if per_met_step else factor) for column, factor, per_met_step in variable.terms]


def split_unit_suffix(layer_name):
    """Split a pixel/qout layer name into its column name and header unit token: ``'Qstrm_m3-s'`` -> ``('Qstrm',
    'm3-s')``. Names without a known unit token (``'MAP'``) come back with None."""
    base, sep, token = layer_name.rpartition('_')
    if sep and token in UNIT_TOKEN_NAMES:
        return base, token
    return layer_name, None


def describe(kind, name, unit_token=None, file_units=None):
    """How to present a variable: ``{'label', 'units', 'tier', 'description', 'factor'}``.

    Variables in the table get the sheet's label, display units, tier and conversion factor. Unknown variables (no
    table for the file kind, or a column the sheet does not list) keep their name as the label, units from the
    header ``unit_token`` (``'mm'``) or the ``file_units`` row of mrf/rft files, no tier and no conversion.
    """
    variable = lookup(kind, name)
    if variable is not None:
        return dict(
            label=variable.label,
            units=variable.display_units,
            tier=variable.tier.value if variable.tier in _OFFERED_TIERS else None,
            description=variable.description,
            factor=variable.factor,
        )
    if unit_token is not None:
        units = UNIT_TOKEN_NAMES.get(unit_token, unit_token)
    else:
        units = None if file_units in (None, '', '[]', '[-]') else file_units
    return dict(label=name, units=units, tier=None, description='', factor=1.0)


def visible_variables(kind, names):
    """The variables of ``names`` to offer, in display order: PRIORITY, then SECONDARY, then variables the table does
    not know, keeping the file order within each group. INDEX, HIDE and IGNORE variables are left out, and so are
    the source columns of a derived variable that is in ``names``; the derived variable takes the place of the
    column of its first term. Without a table (``kind`` None) every name is kept as is."""
    names = list(names)
    if kind is None:
        return names
    position_of = {name: position for position, name in enumerate(names)}
    derived = [variable for variable in DERIVED_VARIABLES.get(kind, ()) if variable.name in position_of]
    superseded = {source for variable in derived for source in variable.sources}
    for variable in derived:
        position_of[variable.name] = position_of.get(variable.sources[0], position_of[variable.name])
    kept = []
    for name in names:
        if name in superseded:
            continue
        variable = lookup(kind, name)
        if variable is None:
            kept.append((2, position_of[name], name))
        elif variable.tier in _OFFERED_TIERS:
            kept.append((_TIER_ORDER[variable.tier], position_of[name], name))
    return [name for _, _, name in sorted(kept)]


def scale_range(low, high, factor):
    """``(low, high)`` converted to display units, ordered so a negative factor does not swap them. None stays None."""
    if low is None or high is None:
        return low, high
    scaled = sorted((low * factor, high * factor))
    return scaled[0], scaled[1]
