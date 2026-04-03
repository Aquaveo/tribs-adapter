from tethysext.atcore.services.app_users.roles import Roles
from tethysext.atcore.services.app_users.licenses import Licenses


class TribsRoles(Roles):
    def list(self):
        """
        Get a list of all roles.
        Returns:
            tuple: All available roles.
        """
        all_roles = (self.ORG_USER, self.ORG_ADMIN, self.APP_ADMIN, self.DEVELOPER)
        return all_roles


class TribsLicenses(Licenses):
    def list(self):
        """
        Get a list of all licenses.
        Returns:
            tuple: All available licenses.
        """
        all_licenses = (self.STANDARD, self.CONSULTANT)
        return all_licenses
