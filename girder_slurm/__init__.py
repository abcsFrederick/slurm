# added for Girder V3
from girder import plugin
from . import rest
from . import event_handlers
from girder import events
from girder.utility import setting_utilities
from girder.settings import SettingDefault
from .constants import PluginSettings
from .models.slurm import Slurm as SlurmModel


@setting_utilities.default(PluginSettings.SHARED_PARTITION)
def _defaultSHARED_PARTITION():
    return '/Your_mount_partition'

@setting_utilities.default(PluginSettings.CRONTAB_PARTITION)
def _defaultCRONTAB_PARTITION():
    return '/Your_crontab_partition_on_girder_server'

@setting_utilities.default(PluginSettings.API_URL)
def _defaultAPI_URL():
    return 'http://localhost:8888/api/v1'

@setting_utilities.default(PluginSettings.SLURM_PARTITION)
def _defaultSLURM_PARTITION():
    return 'GPU'

@setting_utilities.default(PluginSettings.SLURM_NODES)
def _defaultSLURM_NODES():
    return 1

@setting_utilities.default(PluginSettings.SLURM_TASKS)
def _defaultSLURM_TASKS():
    return 1

@setting_utilities.default(PluginSettings.SLURM_CPU)
def _defaultSLURM_CPU():
    return 1

@setting_utilities.default(PluginSettings.SLURM_MEMERY)
def _defaultSLURM_MEMERY():
    return 16

@setting_utilities.default(PluginSettings.SLURM_TIME)
def _defaultSLURM_TIME():
    return 1


@setting_utilities.validator({
    PluginSettings.SHARED_PARTITION,
    PluginSettings.CRONTAB_PARTITION,
    PluginSettings.API_URL,
    PluginSettings.SLURM_PARTITION,
    PluginSettings.SLURM_NODES,
    PluginSettings.SLURM_TASKS,
    PluginSettings.SLURM_CPU,
    PluginSettings.SLURM_MEMERY,
    PluginSettings.SLURM_TIME
})
def _validateString(doc):
    if not isinstance(doc['value'], str):
        pass
        # raise ValidationException('The setting is not a string', 'value')
# SettingDefault.defaults.update({
#     PluginSettings.SHARED_PARTITION: '/Your_mount_partition', # hostname
#     PluginSettings.CRONTAB_PARTITION: '/Your_crontab_partition_on_girder_server', # hostname
#     PluginSettings.API_URL: 'http://localhost:8888/api/v1'
# })


class SlurmPlugin(plugin.GirderPlugin):
    DISPLAY_NAME = 'Slurm'
    CLIENT_SOURCE_PATH = 'web_client'

    def load(self, info):
        info['apiRoot'].slurm = rest.Slurm()
        SlurmModel()
        events.bind('slurm.schedule', 'slurm', event_handlers.schedule)
        # events.bind('cron.watch', 'slurm', event_handlers.cronWatch)