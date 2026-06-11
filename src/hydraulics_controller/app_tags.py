from pydoover.tags import Tag, Tags, String

from .app_config import HydraulicsControllerConfig
from .utils import get_remote_key


class HydraulicsControllerTags(Tags):
    config: HydraulicsControllerConfig

    async def setup(self):
        for remote in self.config.hydraulic_remotes.elements:
            remote_key = get_remote_key(remote)
            # current command state published for this remote
            self.add_tag(remote_key, String(default="off"))
            # command request written by other apps (e.g. a scheduler)
            self.add_tag(f"request_{remote_key}", String(default=None))
