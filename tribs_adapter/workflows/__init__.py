"""
********************************************************************************
* Name: __init__.py
* Author: EJones
* Created On: October 13, 2023
* Copyright: (c) Aquaveo 2023
********************************************************************************
"""
from .bulk_data_retrieval import BulkDataRetrievalWorkflow
from .prepare_met_forcings import PrepareMetWorkflow
from .prepare_soil_parameters import PrepareSoilsWorkflow
from .run_simulation import RunSimulationWorkflow

TRIBS_WORKFLOWS = {
    BulkDataRetrievalWorkflow.TYPE: BulkDataRetrievalWorkflow,
    PrepareMetWorkflow.TYPE: PrepareMetWorkflow,
    PrepareSoilsWorkflow.TYPE: PrepareSoilsWorkflow,
    RunSimulationWorkflow.TYPE: RunSimulationWorkflow,
}
