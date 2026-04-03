from __future__ import annotations
import copy
import datetime
import logging
from pathlib import Path

from sqlalchemy.orm import Session, object_session
from tethysext.atcore.models.app_users import Resource

from tribs_adapter.common.file_to_dataset import FILE_TO_DATASET
from tribs_adapter.io.input_file import FileDatabasePath
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from .mixins import InputFileAttrMixin, LinkMixin, SridAttrMixin

log = logging.getLogger(__name__)


class Realization(Resource, InputFileAttrMixin, SridAttrMixin, LinkMixin):
    TYPE = 'realization_resource'
    DISPLAY_TYPE_SINGULAR = 'Realization'
    DISPLAY_TYPE_PLURAL = 'Realizations'

    UPLOAD_STATUS_KEY = 'upload'

    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }
    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

    link_as = LinkMixin.AS_CHILD

    @property
    def valid_link_types(self):
        from .dataset import Dataset
        return (Dataset, )

    @property
    def linked_datasets(self):
        """Get all Datasets that this Scenario is linked to."""
        from .dataset import Dataset
        return self.get_linked(of_type=Dataset)

    @property
    def exec_start(self) -> datetime.datetime:
        """Get model execution start time."""
        s = self.get_attribute('exec_start', None)
        if s is None:
            return None
        return datetime.datetime.strptime(s, self.DATETIME_FORMAT)

    @exec_start.setter
    def exec_start(self, value: datetime.datetime):
        """Set model execution start time."""
        if not isinstance(value, datetime.datetime):
            raise ValueError('exec_start must be an instance of datetime.datetime')
        s = datetime.datetime.strftime(value, self.DATETIME_FORMAT)
        self.set_attribute('exec_start', s)

    @property
    def exec_end(self) -> datetime.datetime:
        """Get model execution end time."""
        s = self.get_attribute('exec_end', None)
        if s is None:
            return None
        return datetime.datetime.strptime(s, self.DATETIME_FORMAT)

    @exec_end.setter
    def exec_end(self, value: datetime.datetime):
        """Set model execution end time."""
        if not isinstance(value, datetime.datetime):
            raise ValueError('exec_end must be an instance of datetime.datetime')
        s = datetime.datetime.strftime(value, self.DATETIME_FORMAT)
        self.set_attribute('exec_end', s)

    @property
    def project(self) -> Project | None:  # noqa: F821
        """Get the Project that this scenario belongs to."""
        from .project import Project

        def find_project_parent(resource):
            for parent in resource.parents:
                if isinstance(parent, Project):
                    return parent
                else:
                    return find_project_parent(parent)

        project = find_project_parent(self)
        return project

    @property
    def scenario(self) -> Scenario:  # noqa: F821
        """Get the Scenario that this scenario belongs to."""
        from .scenario import Scenario
        session = object_session(self)
        if session is not None:
            scenario = object_session(self).\
                query(Scenario).\
                filter(Scenario.children.contains(self)).\
                one_or_none()
            return scenario

    @scenario.setter
    def scenario(self, value: Scenario):  # noqa: F821
        """Set the Scenario that this Scenario belongs to."""
        from .scenario import Scenario
        if not isinstance(value, Scenario):
            raise ValueError('scenario must be an instance of Scenario.')
        # Remove existing Scenario if one is already assigned
        prev_scenario = self.scenario
        if prev_scenario:
            self.parents.remove(prev_scenario)
        self.parents.append(value)

    @classmethod
    def new(
        cls,
        session: Session,
        name: str,
        description: str,
        created_by: str,
        scenario: Scenario,  # noqa: F821
        model_root: Path | str,
        spatial_manager: TribsSpatialManager = None,
    ) -> Realization:
        """Create a new Realization from a given Scenario and directory of output files.

        Args:
            session: SQLAlchemy session.
            name: Name of the Realization.
            description: Description of the Realization.
            created_by: Username of the user creating the Realization.
            scenario: Scenario that the Realization will belong to.
            model_root: Path to the tRIBS model directory with output.
            spatial_manager: If given, use this spatial manager to generate visualizations for linked datasets.
        """
        # Create new Realization
        realization = cls(
            name=name,
            description=description,
            created_by=created_by,
        )

        session.add(realization)
        session.commit()

        try:
            realization.init(scenario=scenario, model_root=model_root, spatial_manager=spatial_manager)
        except Exception:
            session.delete(realization)
            session.commit()
            raise

        return realization

    def init(
        self,
        scenario: Scenario,  # noqa: F821
        model_root: str | Path,
        spatial_manager: TribsSpatialManager = None,
    ):
        """Initialize this Realization with the output in the given tRIBS model directory.

        Args:
            scenario: Scenario that this Realization belongs to.
            model_root: Path to the tRIBS model directory with output.
            spatial_manager: If given, use this spatial manager to generate visualizations for linked datasets.
        """
        from .dataset import Dataset

        if self.input_file is not None:
            raise RuntimeError('Realization is already initialized.')

        if not isinstance(model_root, Path):
            model_root = Path(model_root)

        if not model_root.is_dir():
            raise FileNotFoundError(f'model_root "{model_root}" is not a directory.')

        # Set the scenario
        self.scenario = scenario

        # Iterate through output file cards and fields in the input files and split into datasets by type
        session = object_session(self)
        project = scenario.project
        tribs_input = copy.deepcopy(scenario.input_file)
        for card, field in tribs_input.files(mode=tribs_input.FilesMode.OUTPUT_ONLY):
            # Get paths for the card
            existing_file_paths = tribs_input.expand_paths(card, model_root)

            # NOTE: Both output cards expect existing_file_paths to be a dictionary of file paths so assuming that here
            # Create a dataset for each
            for ext, file_paths in existing_file_paths.items():
                if len(file_paths) < 1:
                    continue

                dataset_attrs = FILE_TO_DATASET.get(card, {})
                card_path = Path(tribs_input.get_value(card).path)
                # NOTE: Both output cards expect basenames so assuming that here
                relative_path = model_root / card_path.parent

                try:
                    # Create new Dataset
                    dataset_type = dataset_attrs.get("dataset_type", {}).get(ext, card)
                    dataset = Dataset.new(
                        session=session,
                        name=dataset_attrs.get('dataset_name', {}).get(ext, card),
                        description=f'{dataset_attrs.get("dataset_name", {}).get(ext, card)} for {self.name}.',
                        created_by=self.created_by,
                        project=project,
                        dataset_type=dataset_type,
                        srid=scenario.srid if dataset_type in Dataset.SpatialDatasetTypes else None,
                        link=self,
                        items=file_paths,
                        relative_to=relative_path,
                        organizations=self.organizations,
                    )

                except Exception:
                    log.exception(
                        f'Failed to initialize Dataset "{dataset_attrs.get("dataset_name", {}).get(ext, "UNKNOWN")}" '
                        f'for card "{card}". Skipping...'
                    )
                    continue

                field.file_database_paths.append(
                    FileDatabasePath(
                        resource_id=dataset.id,
                        file_collection_id=dataset.file_collection.id,
                        file_collection_paths=[f for f in dataset.file_collection_client.files if '__meta__' not in f]
                    )
                )

        self.input_file = tribs_input
        session.commit()

        # Generate visualization if spatial_manager is given
        if spatial_manager is not None:
            for dataset in self.linked_datasets:
                try:
                    dataset.generate_visualization(session=session, spatial_manager=spatial_manager)
                except Exception:
                    log.exception(
                        f'Failed to generate visualization for Dataset named "{dataset.name}" ({dataset.id}).'
                    )

    def serialize_custom_fields(self, d: dict):
        """Hook for app-specific subclasses to add additional fields to serialization.

        Args:
            base: Base serialized Resource dictionary.

        Returns:
            dict: Serialized Resource.
        """
        # Remove the input_file from attributes
        d['attributes'].pop('input_file')

        # Add custom properties for Projects
        d.update({
            'input_file': self.input_file.model_dump() if self.input_file else None,
            'linked_datasets': [{
                'id': dataset.id,
                'name': dataset.name
            } for dataset in self.linked_datasets],
        })

        return d

    def delete_children(self):
        """Delete all children of this Realization."""
        session = object_session(self)

        for dataset in self.linked_datasets:
            session.delete(dataset)

        session.commit()
