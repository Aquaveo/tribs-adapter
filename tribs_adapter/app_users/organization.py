from tethysext.atcore.models.app_users import Organization
from .permissions import TribsLicenses


class TribsOrganization(Organization):
    TYPE = "tribs_organization"
    LICENSES = TribsLicenses()

    # Polymorphism
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }
