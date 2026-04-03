from tethysext.atcore.models.app_users import AppUser
from .permissions import TribsRoles


class TribsAppUser(AppUser):
    """
    Custom AppUser class for the TRIBS app.
    """
    ROLES = TribsRoles()
