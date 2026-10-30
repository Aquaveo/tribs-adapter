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
        OutputVariable('Hlev', 'Stream stage (flow depth)', 'm', None, Tier.HIDE),
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
            'Basin runoff discharge',
            'm3/s',
            'm³/s',
            Tier.SECONDARY,
            description=('Basin runoff hydrograph at the outlet from the flow-results accumulator.'),
        ),
        OutputVariable(
            'MAP',
            'Mean areal precipitation',
            'mm/hr',
            'mm/hr',
            Tier.PRIORITY,
            description=('Basin-average precipitation rate.'),
        ),
        OutputVariable('RainMax', 'Maximum precipitation rate', 'mm/hr', None, Tier.IGNORE, aliases=('Max', )),
        OutputVariable('RainMin', 'Minimum precipitation rate', 'mm/hr', None, Tier.IGNORE, aliases=('Min', )),
        OutputVariable('FState', 'Forecast state', 'flag', None, Tier.IGNORE),
        OutputVariable(
            'MSM100',
            'Surface soil moisture (top 10 cm)',
            '[-]',
            '% saturation',
            Tier.SECONDARY,
            factor=100.0,
            description=('Basin-average relative saturation (θ/θs) of the top 100 mm of soil.'),
        ),
        OutputVariable(
            'MSMRt',
            'Root-zone soil moisture',
            '[-]',
            '% saturation',
            Tier.PRIORITY,
            factor=100.0,
            description=('Basin-average relative saturation (θ/θs) of the top 1m of soil.'),
        ),
        OutputVariable(
            'MSMU',
            'Unsaturated-zone soil moisture',
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
            'Depth to groundwater',
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
        OutputVariable('SatPercent', 'Saturated area fraction', '[-]', None, Tier.HIDE, aliases=('%Sat', )),
        OutputVariable('RainPercent', 'Raining area fraction', '[-]', None, Tier.HIDE, aliases=('%Rain', )),
        OutputVariable(
            'AvSWE',
            'Snow water equivalent',
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
            'Snowpack sublimation',
            '-cm',
            'mm',
            Tier.PRIORITY,
            factor=-10.0,
            description=('Basin-average sublimation from the snowpack.'),
        ),
        OutputVariable(
            'AvSnEvap',
            'Snowpack evaporation',
            '-cm',
            'mm',
            Tier.PRIORITY,
            factor=-10.0,
            description=('Basin-average evaporation of liquid water from the snowpack.'),
        ),
        OutputVariable('AvSTC', 'Snowpack temperature', '°C', None, Tier.IGNORE),
        OutputVariable('AvDUInt', 'Snowpack energy change', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSLHF', 'Snow latent heat flux', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSSHF', 'Snow sensible heat flux', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSPHF', 'Snow precipitation heat flux', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSGHF', 'Snow ground heat flux', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSRLI', 'Snow incoming longwave', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSRLO', 'Snow outgoing longwave', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvSRSI', 'Snow incoming shortwave', 'kJ/m2', None, Tier.IGNORE),
        OutputVariable('AvInSn', 'Canopy-intercepted snow', 'cm', None, Tier.HIDE),
        OutputVariable(
            'AvInSu',
            'Canopy snow sublimation',
            '-cm',
            'mm',
            Tier.PRIORITY,
            factor=-10.0,
            description=('Basin-average sublimation of canopy-intercepted snow.'),
        ),
        OutputVariable('AvInUn', 'Canopy snow unloading', 'cm', None, Tier.HIDE),
        OutputVariable(
            'SCA',
            'Snow-covered area fraction',
            '[-]',
            '% of basin',
            Tier.SECONDARY,
            factor=100.0,
            description=('Fraction of basin area covered by snow.'),
        ),
        OutputVariable('ChannelPercolation', 'Channel transmission loss', 'm3', None, Tier.HIDE),
        OutputVariable('Qunsat', 'Net lateral unsaturated flow', 'mm/hr', None, Tier.HIDE),
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
        OutputVariable('BndCd', 'Boundary code', 'code', None, Tier.HIDE),
        OutputVariable(
            'Z',
            'Elevation',
            'm',
            'm',
            Tier.PRIORITY,
            description=('Node elevation.'),
        ),
        OutputVariable('VAr', 'Cell area', 'm2', None, Tier.HIDE),
        OutputVariable(
            'CAr',
            'Contributing area',
            'km2',
            'km²',
            Tier.SECONDARY,
            description=('Upslope drainage area flowing through the node.'),
        ),
        OutputVariable('Curv', 'Curvature', 'model-internal', None, Tier.HIDE),
        OutputVariable('EdgL', 'Flow edge length', 'm', None, Tier.HIDE),
        OutputVariable('Slp', 'Slope', 'm/m', None, Tier.HIDE),
        OutputVariable('FWidth', 'Flow width', 'm', None, Tier.HIDE),
        OutputVariable('Aspect', 'Aspect', 'radians', None, Tier.HIDE, aliases=('Aspct', )),
        OutputVariable('SV', 'Sky view factor', '[-]', None, Tier.HIDE),
        OutputVariable('LV', 'Land view factor', '[-]', None, Tier.HIDE),
        OutputVariable(
            'AvSM',
            'Mean surface soil moisture (top 10 cm)',
            '[-]',
            '% saturation',
            Tier.PRIORITY,
            factor=100.0,
            description=('Time-averaged relative saturation (θ/θs) of the top 100 mm over the run.'),
        ),
        OutputVariable(
            'AvRtM',
            'Mean root-zone soil moisture',
            '[-]',
            '% saturation',
            Tier.PRIORITY,
            factor=100.0,
            description=('Time-averaged relative saturation (θ/θs) of the root zone over the run.'),
        ),
        OutputVariable(
            'HOccr',
            'Infiltration-excess runoff occurrences',
            'count',
            'time steps',
            Tier.SECONDARY,
            description=('Number of model time steps with infiltration-excess (Hortonian) runoff.'),
        ),
        OutputVariable(
            'HRt',
            'Mean infiltration-excess runoff rate',
            'mm/hr',
            'mm/hr',
            Tier.SECONDARY,
            description=('Mean infiltration-excess runoff rate during the time steps when it occurred.'),
        ),
        OutputVariable(
            'SbOccr',
            'Saturation-excess runoff occurrences',
            'count',
            'time steps',
            Tier.SECONDARY,
            description=('Number of model time steps with saturation-excess runoff.'),
        ),
        OutputVariable(
            'SbRt',
            'Mean saturation-excess runoff rate',
            'mm/hr',
            'mm/hr',
            Tier.SECONDARY,
            description=('Mean saturation-excess runoff rate during the time steps when it occurred.'),
        ),
        OutputVariable('POccr', 'Perched return-flow occurrences', 'count', None, Tier.HIDE),
        OutputVariable('PRt', 'Mean perched return-flow rate', 'mm/hr', None, Tier.HIDE),
        OutputVariable('SatOccr', 'Groundwater exfiltration occurrences', 'count', None, Tier.HIDE),
        OutputVariable('SatRt', 'Mean groundwater exfiltration rate', 'mm/hr', None, Tier.HIDE),
        OutputVariable('SoiSatOccr', 'Surface saturation occurrences', 'count', None, Tier.HIDE),
        OutputVariable('RchDsch', 'Cumulative net recharge', 'm', None, Tier.HIDE),
        OutputVariable('AvET', 'Mean evapotranspiration rate', 'mm/hr', None, Tier.HIDE),
        OutputVariable(
            'EvpFrct',
            'Mean evaporative fraction',
            '[-]',
            None,
            Tier.SECONDARY,
            description=('Time-averaged evaporative fraction (share of available energy used for evaporation).'),
        ),
        OutputVariable(
            'cET',
            'Cumulative evapotranspiration',
            'mm',
            'mm',
            Tier.PRIORITY,
            description=('Total evapotranspiration over the run.'),
        ),
        OutputVariable(
            'cEsoil',
            'Cumulative soil evaporation',
            'mm',
            'mm',
            Tier.PRIORITY,
            description=('Total bare-soil evaporation over the run.'),
        ),
        OutputVariable('cLHF', 'Cumulative snow latent heat', 'kJ/m2', None, Tier.HIDE),
        OutputVariable(
            'cMelt',
            'Cumulative snowmelt',
            'cm',
            'mm',
            Tier.SECONDARY,
            factor=10.0,
            description=('Total liquid water released from the snowpack over the run.'),
        ),
        OutputVariable('cSHF', 'Cumulative snow sensible heat', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cPHF', 'Cumulative snow precipitation heat', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cRLIn', 'Cumulative incoming longwave (snow)', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cRLo', 'Cumulative outgoing longwave (snow)', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cRSIn', 'Cumulative incoming shortwave', 'mixed', None, Tier.HIDE),
        OutputVariable('cGHF', 'Cumulative snow ground heat', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cUErr', 'Cumulative snow energy error', 'kJ/m2', None, Tier.HIDE),
        OutputVariable('cHrsSun', 'Cumulative sunlit hours', 'hr', None, Tier.HIDE),
        OutputVariable('cHrsSnow', 'Snow-covered hours', 'hr', None, Tier.HIDE),
        OutputVariable('persTime', 'Longest continuous snow cover', 'hr', None, Tier.HIDE),
        OutputVariable(
            'peakWE',
            'Peak snow water equivalent',
            'cm',
            'mm',
            Tier.PRIORITY,
            factor=10.0,
            description=('Maximum SWE reached at the node during the run.'),
        ),
        OutputVariable('initTime', 'Snow cover start time', 'hr', None, Tier.HIDE),
        OutputVariable('peakTime', 'Peak SWE time', 'hr', None, Tier.HIDE),
        OutputVariable('cIntSub', 'Cumulative canopy snow sublimation', 'cm', None, Tier.HIDE),
        OutputVariable(
            'cSnSub',
            'Cumulative snowpack sublimation',
            'cm',
            'mm',
            Tier.PRIORITY,
            factor=10.0,
            description=('Total sublimation from the ground snowpack.'),
        ),
        OutputVariable(
            'cSnEvap',
            'Cumulative snowpack evaporation',
            'cm',
            'mm',
            Tier.PRIORITY,
            factor=10.0,
            description=('Total evaporation of liquid water from the snowpack.'),
        ),
        OutputVariable('cIntUnl', 'Cumulative canopy snow unloading', 'cm', None, Tier.HIDE),
        OutputVariable('AvCanStorParam', 'Canopy storage parameter', 'mm', None, Tier.HIDE),
        OutputVariable('AvIntercCoeff', 'Interception coefficient', '[-]', None, Tier.HIDE),
        OutputVariable('AvTF', 'Free throughfall coefficient', '[-]', None, Tier.HIDE),
        OutputVariable('AvCanFieldCap', 'Canopy field capacity', 'mm', None, Tier.HIDE),
        OutputVariable('AvDrainCoeff', 'Canopy drainage coefficient', 'mm/hr', None, Tier.HIDE),
        OutputVariable('AvDrainExpPar', 'Canopy drainage exponent', '1/mm', None, Tier.HIDE),
        OutputVariable('AvLUAlb', 'Surface albedo', '[-]', None, Tier.HIDE),
        OutputVariable('AvVegHeight', 'Vegetation height', 'm', None, Tier.HIDE),
        OutputVariable('AvOTCoeff', 'Optical transmission coefficient', '[-]', None, Tier.HIDE),
        OutputVariable('AvStomRes', 'Stomatal resistance', 's/m', None, Tier.HIDE),
        OutputVariable(
            'AvVegFract',
            'Vegetation fraction',
            '[-]',
            '%',
            Tier.SECONDARY,
            factor=100.0,
            description=('Fraction of the cell covered by vegetation.'),
        ),
        OutputVariable(
            'AvLeafAI',
            'Leaf area index',
            'm2/m2',
            'm²/m²',
            Tier.SECONDARY,
            description=('Leaf area index.'),
        ),
        OutputVariable('AvEvapThresh', 'Soil evaporation threshold', '[-]', None, Tier.HIDE),
        OutputVariable('AvTransThresh', 'Transpiration threshold', '[-]', None, Tier.HIDE),
        OutputVariable('Bedrock_Depth_mm', 'Depth to bedrock', 'mm', None, Tier.HIDE),
        OutputVariable('Ks', 'Saturated hydraulic conductivity', 'mm/hr', None, Tier.HIDE),
        OutputVariable('ThetaS', 'Saturated water content', '[-]', None, Tier.HIDE),
        OutputVariable('ThetaR', 'Residual water content', '[-]', None, Tier.HIDE),
        OutputVariable('PoreSize', 'Pore-size distribution index', '[-]', None, Tier.HIDE),
        OutputVariable('AirEBubPress', 'Air entry bubbling pressure', 'mm', None, Tier.HIDE),
        OutputVariable('DecayF', 'Conductivity decay parameter', '1/mm', None, Tier.HIDE),
        OutputVariable('SatAnRatio', 'Saturated anisotropy ratio', '[-]', None, Tier.HIDE),
        OutputVariable('UnsatAnRatio', 'Unsaturated anisotropy ratio', '[-]', None, Tier.HIDE),
        OutputVariable('Porosity', 'Porosity', '[-]', None, Tier.HIDE),
        OutputVariable('VolHeatCond', 'Soil thermal conductivity', 'J/(m·s·K)', None, Tier.HIDE),
        OutputVariable('SoilHeatCap', 'Soil heat capacity', 'J/(m³·K)', None, Tier.HIDE),
        OutputVariable('SoilID', 'Soil class', 'class ID', None, Tier.HIDE),
        OutputVariable('LandUseID', 'Land-use class', 'class ID', None, Tier.HIDE),
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
