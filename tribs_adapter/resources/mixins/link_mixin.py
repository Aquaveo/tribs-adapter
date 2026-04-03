from __future__ import annotations

from sqlalchemy.orm import object_session
from tethysext.atcore.models.app_users import Resource


class LinkMixin:
    """Adds properties for managing Linked Resources."""
    AS_PARENT = 'parent'
    AS_CHILD = 'child'

    link_as = AS_CHILD

    @property
    def valid_link_types(self):
        return (Resource, )

    def _raise_value_error(self):
        raise ValueError(
            f'{self.__class__.__name__} resources can only be linked to: '
            f'{", ".join([t.__name__ for t in self.valid_link_types])}'
        )

    def get_linked(self, of_type: Resource = None) -> list[Resource]:  # noqa: F821
        """Get all Resources that are linked to this Resource."""
        if of_type is not None and of_type not in self.valid_link_types:
            self._raise_value_error()

        result = []
        session = object_session(self)
        resource_types = self.valid_link_types if of_type is None else (of_type, )

        if self.link_as == self.AS_CHILD:
            for rt in resource_types:
                result.extend(session.query(rt).filter(rt.parents.contains(self)).all())

        else:  # link_as == parent
            for rt in resource_types:
                result.extend(session.query(rt).filter(rt.children.contains(self)).all())

        return result

    def add_link(self, resource: Resource):  # noqa: F821
        """Add link to the given Resource to this Resource."""
        if self.valid_link_types and not isinstance(resource, self.valid_link_types):
            self._raise_value_error()
        if self.link_as == self.AS_CHILD:
            self.children.append(resource)
        else:  # link_as == parent
            self.parents.append(resource)

    def remove_link(self, resource: Resource):  # noqa: F821
        """Remove link to the given Resource from this Resource."""
        if self.link_as == self.AS_CHILD:
            self.children.remove(resource)
        else:  # link_as == parent
            self.parents.remove(resource)
