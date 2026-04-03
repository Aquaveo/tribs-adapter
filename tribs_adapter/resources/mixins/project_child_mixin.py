from __future__ import annotations

from sqlalchemy.orm import object_session


class ProjectChildMixin:
    """Mixin for Resources that are children of a Projects."""
    @property
    def project(self) -> Project:  # noqa: F821
        """Get the Project that this scenario belongs to."""
        from ..project import Project
        session = object_session(self)
        if session is not None:
            project = object_session(self).\
                query(Project).\
                filter(Project.children.contains(self)).\
                one_or_none()
            return project

    @project.setter
    def project(self, value: Project):  # noqa: F821
        """Set the Project that this Scenario belongs to."""
        from ..project import Project
        if not isinstance(value, Project):
            raise ValueError('project must be an instance of Project.')
        # Remove existing project if one is assigned
        prev_project = self.project
        if prev_project:
            self.parents.remove(prev_project)
        self.parents.append(value)
