from tethysext.atcore.models.app_users import ResourceWorkflow


class TribsWorkflow(ResourceWorkflow):
    """
    Base class for TRIBS workflows.
    """
    __abstract__ = True

    def get_url_name(self):
        from tethysapp.tribs.app import Tribs as app
        return f'{app().url_namespace}:{self.TYPE}_workflow'
