from xms.tool_tribs.ugrids.ugrids_from_watersheds_tool import UGridsFromWatershedsTool
from tribs_adapter.workflows.generate_tin.constants import REDIS_STREAM_LINES, REDIS_WATERSHED_BOUNDARIES


class UGridsFromWatershedsWebTool(UGridsFromWatershedsTool):
    def initial_arguments(self):
        arguments = super().initial_arguments()
        for argument in arguments:
            if argument.name == 'redis_watershed_boundaries':
                argument.value = REDIS_WATERSHED_BOUNDARIES
                argument.hide = True
            elif argument.name == 'redis_stream_lines':
                argument.value = REDIS_STREAM_LINES
                argument.hide = True
        return arguments
