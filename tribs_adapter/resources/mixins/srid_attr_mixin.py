class SridAttrMixin:
    """Mixin for Resources that have an SRID attribute."""
    @property
    def srid(self):
        return self.get_attribute('srid', None)

    @srid.setter
    def srid(self, value):
        self.set_attribute('srid', value)
