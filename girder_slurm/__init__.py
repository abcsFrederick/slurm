# added for Girder V3
from girder import plugin
from . import rest
from . import event_handlers
from girder import events
from girder.utility import setting_utilities
from girder.settings import SettingDefault
from .constants import PluginSettings
from .models.slurm import Slurm as SlurmModel


@setting_utilities.validator({
    PluginSettings.SHARED_PARTITION,
    PluginSettings.CRONTAB_PARTITION,
    PluginSettings.API_URL
})
def validateString(doc):
    pass

SettingDefault.defaults.update({
    PluginSettings.SHARED_PARTITION: '/Your_mount_partition', # hostname
    PluginSettings.CRONTAB_PARTITION: '/Your_crontab_partition_on_girder_server', # hostname
    PluginSettings.API_URL: 'http://localhost:8888/api/v1'
})

class SlurmPlugin(plugin.GirderPlugin):
    DISPLAY_NAME = 'Slurm'
    CLIENT_SOURCE_PATH = 'web_client'

    def load(self, info):
        info['apiRoot'].slurm = rest.Slurm()
        SlurmModel()
        events.bind('slurm.schedule', 'slurm', event_handlers.schedule)
        # events.bind('cron.watch', 'slurm', event_handlers.cronWatch)