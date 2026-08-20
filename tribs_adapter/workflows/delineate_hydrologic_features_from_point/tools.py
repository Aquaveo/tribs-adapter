from xms.tool_tribs.coverages.watershed_from_pour_point_tool import WatershedFromPourPointTool


class WatershedFromPourPointWebTool(WatershedFromPourPointTool):
    def initial_arguments(self):
        arguments = super().initial_arguments()
        for argument in arguments:
            if argument.name == 'pour_point_coverage':
                argument.hide = True
        return arguments
