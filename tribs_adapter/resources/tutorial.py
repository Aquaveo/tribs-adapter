from __future__ import annotations
import logging
from tethysext.atcore.models.app_users import Resource
from .mixins import ProjectChildMixin, LinkMixin, SridAttrMixin

log = logging.getLogger(__name__)


class Tutorial(Resource, ProjectChildMixin, LinkMixin, SridAttrMixin):
    TYPE = 'tutorial_resource'
    DISPLAY_TYPE_SINGULAR = 'Tutorial'
    DISPLAY_TYPE_PLURAL = 'Tutorials'
    __mapper_args__ = {
        'polymorphic_identity': TYPE,
    }

    @property
    def link(self):
        return self.get_attribute('link', '')

    @link.setter
    def link(self, value):
        self.set_attribute('link', value)
