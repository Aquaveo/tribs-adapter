import param


class PolygonAttributes(param.Parameterized):
    polygon_name = param.String(
        label="Name",
        doc="Name of polygon and the dataset with bulk data.",
        allow_None=False,  #: Required
    )
