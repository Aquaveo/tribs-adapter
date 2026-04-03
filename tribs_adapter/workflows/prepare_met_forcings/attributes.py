import param


class PointAttributes(param.Parameterized):
    point_name = param.String(
        label="Name",
        doc="Name of point that will be used to reference it in results.",
        allow_None=False,  #: Required
    )
