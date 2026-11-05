"""Metadata for tRIBS output variables: friendly labels, display units and the priority tier of each column.

Generated from the scientist's sheet ``tRIBS_v5.3.1_output_variables.xlsx`` (streamflow ``.qout``, basin averages
``.mrf`` and integrated spatial ``_i`` files); names, labels and descriptions are the sheet's text. Pixel, ``.rft``
and station variables are not covered yet: they keep their raw names and all stay visible. (Time-dynamic ``_d``
output is not offered as a dataset at all.)

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


QOUT = 'qout'
MRF = 'mrf'
INTEGRATED = 'integrated'

KIND_BY_DATASET_TYPE = {
    DatasetTypes.TRIBS_OUT_QOUT: QOUT,
    DatasetTypes.TRIBS_OUT_MRF: MRF,
    DatasetTypes.TRIBS_OUT_TIME_INTEGRATED: INTEGRATED,
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
}

_INDEX = {
    kind: {
        alias: variable
        for variable in variables
        for alias in (variable.name, *variable.aliases)
    }
    for kind, variables in OUTPUT_VARIABLES.items()
}

_TIER_ORDER = {Tier.PRIORITY: 0, Tier.SECONDARY: 1}
_OFFERED_TIERS = (Tier.PRIORITY, Tier.SECONDARY)


def kind_for_dataset_type(dataset_type):
    """The variable table (``QOUT``, ``MRF``, ``INTEGRATED``) for a dataset type, or None when it has none."""
    return KIND_BY_DATASET_TYPE.get(dataset_type)


def lookup(kind, name):
    """The ``OutputVariable`` called ``name`` (or aliased to it) in the table ``kind``; None when unknown."""
    if kind is None or name is None:
        return None
    return _INDEX.get(kind, {}).get(name)


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
    not know, keeping the file order within each group. INDEX, HIDE and IGNORE variables are left out. Without a
    table (``kind`` None) every name is kept as is."""
    names = list(names)
    if kind is None:
        return names
    kept = []
    for position, name in enumerate(names):
        variable = lookup(kind, name)
        if variable is None:
            kept.append((2, position, name))
        elif variable.tier in _OFFERED_TIERS:
            kept.append((_TIER_ORDER[variable.tier], position, name))
    return [name for _, _, name in sorted(kept)]


def scale_range(low, high, factor):
    """``(low, high)`` converted to display units, ordered so a negative factor does not swap them. None stays None."""
    if low is None or high is None:
        return low, high
    scaled = sorted((low * factor, high * factor))
    return scaled[0], scaled[1]
