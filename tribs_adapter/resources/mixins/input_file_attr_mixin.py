from __future__ import annotations
import json

from tribs_adapter.io import tRIBSInput


class InputFileAttrMixin:
    """Mixin for Resources that have a tRIBS Input File."""
    @property
    def input_file(self) -> tRIBSInput:
        """Get tRIBS Input File data for the Scenario."""
        j = self.get_attribute('input_file', None)
        if j is None:
            return None
        d = json.loads(j)
        return tRIBSInput(**d)

    @input_file.setter
    def input_file(self, value: tRIBSInput):
        """Set tRIBS Input File data for the Scenario."""
        if not isinstance(value, tRIBSInput):
            raise ValueError('input_file must be an instance of tRIBSInput')
        j = value.model_dump_json()
        self.set_attribute('input_file', j)
