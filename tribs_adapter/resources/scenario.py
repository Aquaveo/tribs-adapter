from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session, object_session
from tethysext.atcore.models.app_users import Resource

from tribs_adapter.common.dataset_types import DatasetTypes
from tribs_adapter.common.file_to_dataset import FILE_TO_DATASET
from tribs_adapter.io.input_file import tRIBSInput, FileDatabasePath
from tribs_adapter.services.tribs_spatial_manager import TribsSpatialManager
from .mixins import InputFileAttrMixin, ProjectChildMixin, LinkMixin, SridAttrMixin

log = logging.getLogger(__name__)


class Scenario(Resource, InputFileAttrMixin, SridAttrMixin, ProjectChildMixin, LinkMixin):
    TYPE = 'scenario_resource'
    DISPLAY_TYPE_SINGULAR = 'Scenario'
    DISPLAY_TYPE_PLURAL = 'Scenarios'

    UPLOAD_STATUS_KEY = 'upload'

    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }

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
    def realizations(self) -> list[Realization]:  # noqa: F821
        """Get all Realizations that belong to this Scenario."""
        from .realization import Realization
        return object_session(self).\
            query(Realization).\
            filter(Realization.parents.contains(self)).\
            all()

    def get_realization(self, realization_id: str | GUID) -> Realization | None:  # noqa: F821
        """Get a specific Realization that belongs to this Scenario."""
        from .realization import Realization
        return object_session(self).\
            query(Realization).\
            filter(Realization.parents.contains(self)).\
            filter(Realization.id == realization_id).\
            one_or_none()

    def add_realization(self, realization: Realization):  # noqa: F821
        """Add given Realization to this Scenario."""
        from .realization import Realization
        if not isinstance(realization, Realization):
            raise ValueError('realization must be an instance of Realization.')
        self.children.append(realization)

    def remove_realization(self, realization: Realization):  # noqa: F821
        """Remove given Realization from this Scenario."""
        from .realization import Realization
        if not isinstance(realization, Realization):
            raise ValueError('realization must be an instance of Realization.')
        self.children.remove(realization)

    @classmethod
    def new(
        cls,
        session: Session,
        name: str,
        description: str,
        created_by: str,
        project: Project,  # noqa: F821
        srid: str | int = None,
        input_file: Optional[Path | str] = None,
        spatial_manager: TribsSpatialManager = None,
    ) -> Scenario:
        """Create a new Scenario from a given tRIBS Input File.

        Args:
            session: SQLAlchemy session.
            name: Name of the Scenario.
            description: Description of the Scenario.
            created_by: Username of the user creating the Scenario.
            project: Project that the Scenario will belong to.
            srid: SRID of spatial datasets in the Scenario. Required if input_file provided.
            input_file: Path to the tRIBS Input File.
            spatial_manager: If given, use this spatial manager to generate visualizations for linked datasets.
        """
        # Create new Scenario
        scenario = cls(
            name=name,
            description=description,
            created_by=created_by,
            srid=srid,
        )

        # Set the project
        session.add(scenario)
        session.commit()

        # Initialize the Scenario
        try:
            scenario.init(project=project, srid=srid, input_file=input_file)
        except Exception:
            session.delete(scenario)
            session.commit()
            raise

        return scenario

    def init(
        self,
        project: Project,  # noqa: F821
        srid: str | int = None,
        input_file: Optional[Path | str] = None,
        spatial_manager: TribsSpatialManager = None
    ):
        """Initialize this Scenario with the given tRIBS Input File.

        Args:
            project: Project that this Scenario belongs to.
            srid: SRID of spatial datasets in the Scenario. Required if input_file provided.
            input_file: Path to the tRIBS Input File.
            spatial_manager: If given, use this spatial manager to generate visualizations for linked datasets.
        """
        from .dataset import Dataset

        if self.input_file is not None:
            raise RuntimeError('Scenario is already initialized.')

        if srid is None and input_file is not None:
            raise ValueError('srid is required if input_file is provided.')

        # Set the project
        session = object_session(self)
        self.project = project
        organizations = self.organizations

        if input_file is None:
            # Intialize with empty input file
            tribs_input = tRIBSInput()
        else:
            # Parse input file
            input_file = Path(input_file)
            if not input_file.exists():
                raise FileNotFoundError(f'input_file "{input_file}" does not exist.')

            model_root = input_file.parent
            tribs_input = tRIBSInput.from_input_file(input_file)

            # Iterate through file cards and fields in the input file
            for card, field in tribs_input.files(mode=tribs_input.FilesMode.INPUT_ONLY):
                # Get paths for the card and verify files exist
                existing_file_paths = tribs_input.expand_paths(card, model_root)
                if len(existing_file_paths) < 1:
                    continue

                # Determine directory for preserving relative paths
                card_path = Path(tribs_input.get_value(card).path)
                dataset_attrs = FILE_TO_DATASET.get(card, {})
                if dataset_attrs.get('is_directory', False):
                    relative_to_dir = model_root / card_path
                else:
                    relative_to_dir = model_root / card_path.parent

                try:
                    # Create new Dataset
                    dataset_type = dataset_attrs.get('dataset_type', DatasetTypes.UNKNOWN)
                    dataset = Dataset.new(
                        session=session,
                        name=dataset_attrs.get('dataset_name', card),
                        description=f'{dataset_attrs.get("dataset_name", card)} for {self.name}.',
                        created_by=self.created_by,
                        dataset_type=dataset_type,
                        srid=srid if dataset_type in Dataset.SpatialDatasetTypes else None,
                        project=project,
                        link=self,
                        organizations=organizations if organizations else None,
                        items=existing_file_paths,
                        relative_to=relative_to_dir,
                    )

                except Exception:
                    log.exception(
                        f'Failed to initialize Dataset "{dataset_attrs.get("dataset_name", "UNKNOWN")}" '
                        f'for card "{card}". Skipping...'
                    )
                    continue

                # Update tRIBSInput field
                field.resource_id = dataset.id
                field.file_collection_id = dataset.file_collection.id
                field.file_collection_paths = [f for f in dataset.file_collection_client.files if '__meta__' not in f]

        self.input_file = tribs_input
        session.commit()

        # Generate visualization if spatial_manager is given
        if spatial_manager is not None:
            for dataset in self.linked_datasets:
                try:
                    dataset.generate_visualization(session=session, spatial_manager=spatial_manager)
                except Exception:
                    log.exception(f'Failed to generate visualization for Dataset named "{dataset.name}" ({dataset.id}.')

    def export(self, directory: Path | str, with_datasets=True):
        """Export the input file and input datasets for this Scenario.

        Args:
            directory: Directory to export the input file and input files to.
        """
        from .dataset import Dataset
        # Validate directory
        dir_path = Path(directory)  # ensure is a Path object
        if not dir_path.is_dir():
            raise ValueError(f'directory "{directory}" is not a directory.')

        # write the input file
        self.input_file.to_input_file(dir_path)

        if not with_datasets:
            return

        # write the datasets
        session = object_session(self)
        for card, f in self.input_file.files(mode=self.input_file.FilesMode.INPUT_ONLY):
            if not f.resource_id or not f.path:
                continue

            dataset = session.query(Dataset).get(f.resource_id)
            path_is_directory = FILE_TO_DATASET.get(card, {}).get('is_directory', False)

            # Append STARTDATE to LUGRID files before extension
            if card == 'LUGRID':
                client = dataset.file_collection_client
                startdate = self.input_file.run_parameters.time_variables.STARTDATE.strftime('%m%d%Y%H')
                dir = client.path
                for file in client.files:
                    old_file = f'{dir}/{file}'
                    if file.endswith('.asc'):
                        new_file = f'{dir}/{file[:2]}{startdate}.asc'  # e.g., LA0928202400.asc
                        os.rename(old_file, new_file)
                    elif file.endswith('.aux.xml'):
                        os.remove(old_file)

            # Reconstruct the same directory structure as the input file expects
            if not path_is_directory:
                sub_dirs = Path(f.path).parent  # e.g. "Input/salas.soi" or "Input/Nodes/oNodes.dat"
                dataset.export(dir_path / sub_dirs)  # e.g. "/tmp/srp_assemble__mqce9rj/Input"
                if Path(f.path).suffix == '.gdf':
                    # Prepend the folder path to the files listed in the .gdf file
                    file_path = dir_path / f.path
                    self._prepend_folder_path_to_gdf_files(sub_dirs.name, file_path)
            else:
                dataset.export(dir_path / f.path)  # e.g. "Forecast/" or "Restart/"

    def serialize_custom_fields(self, d: dict):
        """Hook for app-specific subclasses to add additional fields to serialization.

        Args:
            base: Base serialized Resource dictionary.

        Returns:
            dict: Serialized Resource.
        """
        # Remove the input_file from attributes
        if 'input_file' in d['attributes']:
            d['attributes'].pop('input_file')

        # Add custom properties for Projects
        d.update({
            'input_file': self.input_file.model_dump() if self.input_file else None,
            'linked_datasets': [{
                'id': dataset.id,
                'name': dataset.name
            } for dataset in self.linked_datasets],
            'realizations': [realization.serialize(format='dict') for realization in self.realizations],
        })

        return d

    def link_dataset(self, dataset: Dataset, card: str):  # noqa: F821
        """Link the given Dataset to this Scenario."""
        if dataset.project.id != self.project.id:
            raise ValueError('Dataset must belong to the same Project as the Scenario.')
        self.add_link(dataset)
        fdp = FileDatabasePath(
            resource_id=str(dataset.id),
            file_collection_id=str(dataset.file_collection.id),
            file_collection_paths=[f for f in dataset.file_collection_client.files if '__meta__' not in f],
            path=self.validate_link_dataset_path(dataset, card),
        )
        # fdp.path = self.validate_link_dataset_path(fdp, card)
        self.input_file = self.input_file.set_value(card, fdp)

    def validate_link_dataset_path(self, dataset: Dataset, card: str):  # noqa: F821
        """Update the path on the FileDatabasePath when linking."""
        path = ''
        files = [f for f in dataset.file_collection_client.files if '__meta__' not in f]
        if not files:
            return path
        if card == "INPUTDATAFILE":
            # Get the base name without extension of the first file, store in Output/Mesh directory
            for file in files:
                # Look for .edges, .nodes, .points, .z, and .tri files.
                # Don't use a .reach file with extra text in name before the extension.
                if Path(file).suffix in ['.edges', '.nodes', '.points', '.z', '.tri']:
                    path = str(Path('Output') / Path('Mesh') / Path(file).stem)
                    break
        elif card == "ARCINFOFILENAME":
            # Get the base name without extension of the first file, store in Output/Mesh directory
            path = str(Path('Output') / Path('Mesh') / Path(files[0]).stem)
        elif card in ["HYDROMETSTATIONS", "GAUGESTATIONS"]:
            # Look for file with the .sdf extension, store in Weather direcotry
            for file in files:
                if Path(file).suffix == '.sdf':
                    if card == "HYDROMETSTATIONS":
                        path = str(Path('Weather') / Path(file).name)
                    else:
                        path = str(Path('Rain') / Path(file).name)
        elif card in ["POINTFILENAME", "SOILTABLENAME", "SOILMAPNAME", "LANDTABLENAME", "LANDMAPNAME", "BEDROCKFILE"]:
            # Get the name of the first file, store in Input directory
            path = str(Path('Input') / Path(files[0]).name)
        elif card == "GWATERFILE":
            for file in files:
                if Path(file).suffix == '.iwt':
                    path = str(Path('Input') / Path(file).name)
        elif card == "SOILMAPNAME":
            for file in files:
                if Path(file).suffix == '.soi':
                    path = str(Path('Input') / Path(file).name)
        elif card == "LANDMAPNAME":
            for file in files:
                if Path(file).suffix == '.lan':
                    path = str(Path('Input') / Path(file).name)
        elif card in ["LUGRID", "SCGRID"]:
            # Look for file with the .gdf extension, store in Input direcotry
            for file in files:
                if Path(file).suffix == '.gdf':
                    path = str(Path('Input') / Path(file).name)
        elif card == "RAINFILE":
            # Get the name of the first file, store in Rain directory
            path = str(Path('Rain') / Path(files[0]).name[0])
        elif card in ["HYDROMETGRID", "HYDROMETCONVERT", "HYDROMETBASENAME"]:
            # Get the name of the first file, store in Weather directory
            path = str(Path('Weather') / Path(files[0]).name)
        elif card in ["GAUGECONVERT", "GAUGEBASENAME"]:
            # Get the name of the first file, store in Rain directory
            path = str(Path('Rain') / Path(files[0]).name)
        elif card in ["NODEOUTPUTLIST", "HYDRONODELIST", "OUTLETNODELIST"]:
            # Get the name of the first file, store in Input/Nodes directory
            path = str(Path('Input') / Path('Nodes') / Path(files[0]).name)
        return path

    def _prepend_folder_path_to_gdf_files(self, folder_path: str, file_path: str):
        """Prepend the given folder path to the files listed in the .gdf file."""
        lines = []
        with open(file_path, 'r') as file:
            for line in file.readlines():
                line = line.strip()
                if line.endswith('asc'):
                    var_name, filename, ext = line.split(' ')
                    new_line = ' '.join([var_name, str(Path(folder_path) / filename), ext])
                    line = new_line
                lines.append(line + '\n')

        with open(file_path, 'w') as file:
            file.writelines(lines)
            file.close()

    def unlink_dataset(self, dataset: Dataset, card: str):  # noqa: F821
        """Unlink the given Dataset from this Scenario."""
        self.remove_link(dataset)
        self.input_file = self.input_file.set_value(card, FileDatabasePath())

    def update_input_file(self, update: dict):
        """Update the input file with a sparse dictionary representation of the input file.

        Args:
            update: Dictionary representation of the input file to update with. Can be sparse.
            validate: If True, validate the input file after updating.

        Raises:
            pydantic.ValidationError: If the update dict is invalid and validate is True.
        """
        from .dataset import Dataset
        session = object_session(self)
        if not self.input_file:
            self.input_file = tRIBSInput()

        # Copy input file for comparisons below
        original_input_file = self.input_file.model_copy(deep=True)
        updated_input_file = original_input_file.copy_update(update)

        # Update linked datasets accordingly
        # Note: must iterate on the original_input_file b/c files only iterates over fields set on initialization
        for card, og_f in original_input_file.files(mode=tRIBSInput.FilesMode.INPUT_ONLY):
            up_f = updated_input_file.get_value(card)
            og_resource_id = og_f.resource_id if og_f else None
            up_resource_id = up_f.resource_id if up_f else None
            # Check for changes in resource_id (dataset assigned)
            if og_resource_id != up_resource_id:
                # Dataset was removed
                if og_resource_id and not up_resource_id:
                    dataset = session.query(Dataset).get(og_resource_id)
                    if dataset:
                        log.debug(f'Dataset "{dataset.id}" was removed from card "{card}" in Scenario "{self.id}".')
                        self.unlink_dataset(dataset, card)

                # Dataset was changed or added
                elif up_resource_id:
                    dataset = session.query(Dataset).get(up_resource_id)
                    if dataset and dataset.project.id == self.project.id:
                        # Unlink old dataset if it exists
                        if og_resource_id:
                            log.debug(f'Dataset "{dataset.id}" was changed for card "{card}" in Scenario "{self.id}".')
                            og_dataset = session.query(Dataset).get(og_resource_id)
                            if og_dataset:
                                self.unlink_dataset(og_dataset, card)

                        # Link new dataset
                        log.debug(f'Dataset "{dataset.id}" was added to card "{card}" in Scenario "{self.id}".')
                        self.link_dataset(dataset, card)
                        fdp_update = self.input_file.get_value(card)
                        updated_input_file.set_value(card, fdp_update)  # Preserve file collection info if missing
                    else:
                        log.warning(
                            f'Could not find Dataset with ID "{og_resource_id}" in Project '
                            f'"{self.project.id}": Resetting input file field for card {card} in Scenario '
                            f'"{self.id}".'
                        )
                        up_f = FileDatabasePath()

        self.input_file = updated_input_file
        session.commit()

    def delete_children(self):
        """Delete all children of this Scenario."""
        session = object_session(self)
        for realization in self.realizations:
            realization.delete_children()
            session.delete(realization)

        for dataset in self.linked_datasets:
            session.delete(dataset)

        session.commit()
