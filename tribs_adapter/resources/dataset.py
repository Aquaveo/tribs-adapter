from __future__ import annotations
import logging
from pathlib import Path
import shutil

from sqlalchemy.orm import Session, backref, object_session, relationship
from tethysext.atcore.models.app_users import Resource
from tethysext.atcore.models.file_database import FileCollection, resource_file_collection_association
from tethysext.atcore.services.file_database import FileCollectionClient

from tribs_adapter.common.dataset_types import DatasetTypes, SpatialDatasetTypes
from tribs_adapter.app_users import TribsOrganization
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from .mixins import ProjectChildMixin, LinkMixin, SridAttrMixin

log = logging.getLogger(__name__)


class Dataset(Resource, ProjectChildMixin, LinkMixin, SridAttrMixin):
    TYPE = 'dataset_resource'
    DISPLAY_TYPE_SINGULAR = 'Dataset'
    DISPLAY_TYPE_PLURAL = 'Datasets'
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }
    DatasetTypes = DatasetTypes
    SpatialDatasetTypes = SpatialDatasetTypes

    # Relationships
    file_collection = relationship(
        FileCollection,
        secondary=resource_file_collection_association,
        uselist=False,
        backref=backref('dataset', uselist=False)
    )

    link_as = LinkMixin.AS_PARENT

    @property
    def valid_link_types(self):
        from .scenario import Scenario
        from .realization import Realization
        return (Scenario, Realization)

    @property
    def linked_scenarios(self):
        """Get all Scenarios that this Dataset is linked to."""
        from .scenario import Scenario
        return self.get_linked(of_type=Scenario)

    @property
    def linked_realizations(self):
        """Get all Realizations that this Dataset is linked to."""
        from .realization import Realization
        return self.get_linked(of_type=Realization)

    @property
    def dataset_type(self):
        value = self.get_attribute('dataset_type', None)
        return None if value is None else self.DatasetTypes(value)

    @dataset_type.setter
    def dataset_type(self, value):
        if getattr(self, '_valid_dataset_types', None) is None:
            self._valid_dataset_types = [e.value for e in self.DatasetTypes]

        if value not in self._valid_dataset_types:
            raise ValueError(
                f'Invalid dataset type: "{value}" given. '
                'See Dataset.DatasetTypes for a list of valid types.'
            )

        self.set_attribute('dataset_type', value)

    @property
    def file_collection_client(self) -> FileCollectionClient:
        """Get a File Collection Client for this Dataset's file collection."""
        session = object_session(self)
        project = self.project
        if project is None:
            raise ValueError('Dataset must be associated with a Project to get a file collection client.')

        return FileCollectionClient(
            session=session,
            file_database_client=project.file_database_client,
            file_collection_id=self.file_collection.id
        )

    @classmethod
    def duplicate(
        cls,
        dataset: Dataset,
        created_by: str = None,
        name: str = None,
    ) -> Dataset:
        """Create a new dataset that is the duplicate of the given dataset.

        Args:
            dataset: The Dataset to duplicate.
            created_by: Username of the user creating the duplicate Dataset.
            name: Name of the duplicated Dataset if want to be different (optional).

        Returns:
            Dataset: The duplicated Dataset.
        """
        dp_fcc = dataset.file_collection_client.duplicate()
        try:
            dp_dataset = Dataset.new(
                session=object_session(dataset),
                name=name if name else dataset.name,
                description=dataset.description,
                created_by=created_by if created_by else dataset.created_by,
                project=dataset.project,
                dataset_type=dataset.dataset_type,
                srid=dataset.srid,
                organizations=dataset.organizations,
                fcc=dp_fcc,
            )
        except Exception:
            # Rollback duplicating files if exception occurred
            dp_fcc.delete()
            raise

        return dp_dataset

    @classmethod
    def new(
        cls,
        session: Session,
        name: str,
        description: str,
        created_by: str,
        project: Project,  # noqa: F821
        dataset_type: DatasetTypes,
        srid: int | str = None,
        items: list[Path | str] = None,
        fcc: FileCollectionClient = None,
        link: Scenario | Realization = None,  # noqa: F821
        relative_to: Path | str = '',
        organizations: list[TribsOrganization] | None = None,
    ) -> Dataset:
        """Factory method for creating a new Dataset instance.

        Args:
            session: SQLAlchemy session.
            name: Name of the Dataset.
            description: Description of the Dataset.
            created_by: Username of the user creating the Dataset.
            project: The Project this Dataset should belong to.
            dataset_type: Type of the Dataset.
            srid: Spatial Reference ID for the Dataset, if applicable. Required by spatial dataset types.
            items: List of paths to files or directories to add to the Dataset's file collection.
            link: The Scenario or Realization this Dataset should be linked to.
            relative_to: Preserve realtive path of items relative to this directory.
            organizations: Organizations that will have access to this Dataset.
        """
        # Create new dataset
        dataset = cls(
            name=name,
            description=description,
            created_by=created_by,
        )

        if not organizations:
            organizations = project.organizations

        if organizations is not None:
            for organization in organizations:
                dataset.organizations.append(organization)

        session.add(dataset)
        session.commit()

        # Create a new file collection
        try:
            dataset.init(
                project=project,
                link=link,
                dataset_type=dataset_type,
                srid=srid,
                items=items,
                fcc=fcc,
                relative_to=relative_to
            )
        except Exception:
            session.delete(dataset)
            session.commit()
            raise
        return dataset

    def init(
        self,
        project: Project,  # noqa: F821
        dataset_type: DatasetTypes,
        srid: int | str = None,
        items: list[Path | str] = None,
        fcc: FileCollectionClient = None,
        link: Scenario | Realization = None,  # noqa: F821
        relative_to: Path | str = '',
    ):
        """Initialize this Dataset with given files and/or directories.

        Args:
            project: The Project this Dataset should belong to.
            dataset_type: Type of the Dataset.
            srid: Spatial Reference ID for the Dataset, if applicable. Required by spatial dataset types.
            items: List of paths to files or directories to add to the Dataset's file collection.
            fcc: FileCollectionClient for existing FileCollection to use for this Dataset.
            link: The Scenario or Realization this Dataset should be linked to.
            relative_to: Preserve realtive path of items relative to this directory.
        """
        if self.file_collection is not None:
            raise RuntimeError('Dataset is already initialized.')

        if items is None and fcc is None:
            raise ValueError('At least one of "items" or "file_collection" must be given.')

        if srid is None and dataset_type in self.SpatialDatasetTypes:
            raise ValueError(f'SRID is required for dataset type "{dataset_type.value}".')

        if relative_to:
            relative_to = Path(relative_to)
            if not relative_to.is_dir():
                raise ValueError(f'"{relative_to}" must be a directory.')

        # First associate the Dataset with the given Project
        self.project = project

        # Link the Dataset to the given Scenario or Realization
        if link:
            self.add_link(link)

        self.dataset_type = dataset_type
        self.srid = srid

        if items is not None:
            # Verify files exist
            dne_files = []
            str_items = []
            for item in items:
                # Convert to Path for validation
                if not isinstance(item, Path):
                    item = Path(item)

                if not item.exists():
                    dne_files.append(str(item))

                # File Collection add_item requires string paths
                str_items.append(str(item))

            if dne_files:
                raise ValueError(f'The following files/directories were given but do not exist: {", ".join(dne_files)}')

            # Create a new file collection
            fdc = self.project.file_database_client
            fcc = fdc.new_collection(
                items=str_items,
                meta={
                    'dataset_id': str(self.id),
                    'dataset_type': dataset_type.value,
                    'description': f'File collection for dataset "{self.name}" ({self.id})',
                    'display_name': 'Dataset Files',
                },
                relative_to=str(relative_to),
            )
            self.file_collection = fcc.instance
        else:
            fcc.set_meta('dataset_id', str(self.id))
            fcc.set_meta('dataset_type', dataset_type.value)
            fcc.set_meta('description', f'File collection for dataset "{self.name}" ({self.id})')
            fcc.set_meta('display_name', 'Dataset Files')
            self.file_collection = fcc.instance

        session = object_session(self)
        session.commit()

    def export(self, target: Path | str):
        """Export the Dataset to the given directory.

        Args:
            target: Path to the directory to export the Dataset to.
        """
        target_dir_path = Path(target)
        target_dir_path.mkdir(parents=True, exist_ok=True)
        fc_path = Path(self.file_collection_client.path)
        for path in fc_path.glob('**/*'):
            rel_path = path.relative_to(fc_path)
            if '__meta__' in path.name or path.is_dir():
                continue
            target_rel_path = target_dir_path / rel_path
            target_rel_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(path, target_rel_path)

    def serialize_custom_fields(self, d: dict):
        """Hook for app-specific subclasses to add additional fields to serialization.

        Args:
            base: Base serialized Resource dictionary.

        Returns:
            dict: Serialized Resource.
        """
        # Remove vals from attributes
        if 'dataset_type' in d['attributes']:
            d['attributes'].pop('dataset_type')

        if 'srid' in d['attributes']:
            d['attributes'].pop('srid')

        viz = None
        if 'viz' in d['attributes']:
            viz = d['attributes'].pop('viz')

        if viz:
            if 'extent' not in viz or not viz['extent'] or float('inf') in viz['extent'] \
               or float('-inf') in viz['extent']:
                log.warning(f'Invalid extent values in viz extent: {viz.get("extent")}. Defaulting to U.S. extent.')
                viz['extent'] = [-124.914551, 24.766785, -67.412109, 49.152970]  # U.S.

            if 'origin' not in viz or not viz['extent'] or float('inf') in viz['origin'] \
               or float('-inf') in viz['origin']:
                log.warning(f'Invalid origin values in viz origin: {viz.get("origin")} Defaulting to None.')
                viz['origin'] = None

            d.update({'viz': viz})

        # Add custom properties for Projects
        d.update({
            'dataset_type': self.dataset_type.value,
            'srid': self.srid,
        })

        return d

    def generate_visualization(self, session: Session, spatial_manager: TribsSpatialManager, **kwargs):
        """Generate a visualization for this Dataset.

        Args:
            session: SQLAlchemy session.
            kwargs: Additional keyword arguments to pass to the visualization generation method.
        """
        style = kwargs.get('style', None)
        spatial_manager.create_layer_for_dataset(self, self.get_attribute('srid'), session, style)

    def remove_visualization(self, session: Session, spatial_manager: TribsSpatialManager, **kwargs):
        """Remove the visualization for this Dataset.

        Args:
            session: SQLAlchemy session.
            kwargs: Additional keyword arguments to pass to the visualization removal method.
        """
        spatial_manager.delete_layer_for_dataset(self)
