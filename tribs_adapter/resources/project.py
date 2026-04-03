from __future__ import annotations
import os
import logging
from pathlib import Path

from geoalchemy2 import Geometry
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import Session, backref, relationship, object_session
from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.models.types import GUID
from tethysext.atcore.services.file_database import FileDatabaseClient

from .scenario import Scenario

log = logging.getLogger(__name__)


class Project(Resource):
    TYPE = 'project_resource'
    DISPLAY_TYPE_SINGULAR = 'Project'
    DISPLAY_TYPE_PLURAL = 'Projects'
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }

    # Additional Columns
    file_database_id = Column(GUID, ForeignKey('file_databases.id'))
    area_of_interest = Column(Geometry(geometry_type='POLYGON', srid=4326))

    # Relationships
    file_database = relationship('FileDatabase', backref=backref('project', uselist=False))

    @property
    def scenarios(self):
        """Get all Scenarios that belong to this Project."""
        return object_session(self).\
            query(Scenario).\
            filter(Scenario.parents.contains(self)).\
            all()

    def get_scenario(self, scenario_id: str | GUID) -> Scenario:
        """Get a specific Scenario that belongs to this Project."""
        return object_session(self).\
            query(Scenario).\
            filter(Scenario.parents.contains(self)).\
            filter(Scenario.id == scenario_id).\
            one_or_none()

    def add_scenario(self, scenario: Scenario):
        """Add given Scenario to this Project."""
        if not isinstance(scenario, Scenario):
            raise ValueError('scenario must be an instance of Scenario.')
        self.children.append(scenario)

    def remove_scenario(self, scenario: Scenario):
        """Remove given Scenario from this Project."""
        if not isinstance(scenario, Scenario):
            raise ValueError('scenario must be an instance of Scenario.')
        self.children.remove(scenario)

    @property
    def datasets(self) -> list[Dataset]:  # noqa: F821
        """Get all Datasets that belong to this Scenario."""
        from .dataset import Dataset
        return object_session(self).\
            query(Dataset).\
            filter(Dataset.parents.contains(self)).\
            all()

    def get_dataset(self, dataset_id: str | GUID) -> Dataset | None:  # noqa: F821
        """Get a specific Dataset that belongs to this Scenario."""
        from .dataset import Dataset
        return object_session(self).\
            query(Dataset).\
            filter(Dataset.parents.contains(self)).\
            filter(Dataset.id == dataset_id).\
            one_or_none()

    def add_dataset(self, dataset: Dataset):  # noqa: F821
        """Add given Dataset to this Scenario."""
        from .dataset import Dataset
        if not isinstance(dataset, Dataset):
            raise ValueError('dataset must be an instance of Dataset.')
        self.children.append(dataset)

    def remove_dataset(self, dataset: Dataset):  # noqa: F821
        """Remove given Dataset from this Scenario."""
        from .dataset import Dataset
        if not isinstance(dataset, Dataset):
            raise ValueError('dataset must be an instance of Dataset.')
        self.children.remove(dataset)

    @property
    def fdb_root_directory(self) -> Path:
        """Get the root directory for the FileDatabase for this Project."""
        fdb_root_directory = Path(os.environ.get('FDB_ROOT_DIR'))
        log.debug(f'FDB_ROOT_DIR: {fdb_root_directory}')
        if not fdb_root_directory:
            raise RuntimeError('Coud not determine the file database root directory for project. Is FDB_ROOT_DIR set?')
        if not fdb_root_directory.exists():
            raise RuntimeError(f'File database root directory does not exist: {fdb_root_directory}')
        return fdb_root_directory

    @property
    def file_database_client(self) -> FileDatabaseClient:
        """Get the FileDatabaseClient for this Project."""
        session = object_session(self)
        return FileDatabaseClient(session, self.fdb_root_directory, self.file_database.id)

    @classmethod
    def new(cls, session: Session, name: str, description: str, created_by: str) -> Project:
        """Create and initialize a new Project.

        Args:
            session: SQLAlchemy Session.
            name: Name of the Project.
            description: Description of the Project.
            created_by: Username of the user that created the Project.
        """  # noqa: E501
        # Create new Project
        project = cls(
            name=name,
            description=description,
            created_by=created_by,
        )
        session.add(project)
        session.commit()

        # Initialize FileDatabase
        try:
            project.init()
        except Exception:
            session.delete(project)
            session.commit()
            raise
        return project

    def init(self):
        """Initialize this Project with a file database at the given location."""
        if self.file_database is not None:
            raise RuntimeError('Project is already initialized.')

        # Initialize FileDatabase
        file_db_metadata = {
            'project_id': str(self.id),
            'description': f'File Database for Project "{self.name}" ({self.id})',
        }

        session = object_session(self)
        file_db_client = FileDatabaseClient.new(
            session=session,
            root_directory=self.fdb_root_directory,
            meta=file_db_metadata,
        )
        self.file_database = file_db_client.instance
        session.commit()

    def serialize_custom_fields(self, d: dict):
        """Hook for app-specific subclasses to add additional fields to serialization.

        Args:
            base: Base serialized Resource dictionary.

        Returns:
            dict: Serialized Resource.
        """
        # Add custom properties for Projects
        d.update({
            'datasets': [dataset.serialize() for dataset in self.datasets],
            'scenarios': [scenario.serialize(format='dict') for scenario in self.scenarios],
        })

        return d

    def delete_children(self):
        """Delete all children of this Project."""
        session = object_session(self)
        for scenario in self.scenarios:
            scenario.delete_children()
            session.delete(scenario)

        session.commit()
