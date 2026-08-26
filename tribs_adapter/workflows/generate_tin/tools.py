from xms.tool_tribs.ugrids.ugrids_from_watersheds_tool import UGridsFromWatershedsTool


class UGridsFromWatershedsWebTool(UGridsFromWatershedsTool):
    def initial_arguments(self):
        arguments = super().initial_arguments()
        for argument in arguments:
            if argument.name == 'redis_watershed_boundaries':
                argument.value = 'Rewatersheds'
                argument.hide = True
            elif argument.name == 'redis_stream_lines':
                argument.value = 'Restreams'
                argument.hide = True
        return arguments
