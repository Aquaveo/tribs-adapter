from xms.tool_tribs.coverages.watershed_from_pour_point_tool import WatershedFromPourPointTool


class WatershedFromPourPointWebTool(WatershedFromPourPointTool):
    def initial_arguments(self):
        arguments = super().initial_arguments()
        for argument in arguments:
            if argument.name == 'pour_point_coverage':
                argument.hide = True
            elif argument.name == 'preprocessing_engine':
                argument.value = self.WHITEBOX_FULL_WORKFLOW
            elif argument.name == 'watershed_boundaries':
                argument.value = 'Watersheds'
            elif argument.name == 'stream_lines':
                argument.value = 'Streams'
        return arguments
