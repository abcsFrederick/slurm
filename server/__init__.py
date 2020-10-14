from . import rest
from . import event_handlers
from girder import events
from girder.utility import setting_utilities
from girder.constants import SettingDefault
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
    PluginSettings.SHARED_PARTITION: '/mnt/hpc/webdata/server/fr-s-ivg-ssr-d1', # hostname
    PluginSettings.CRONTAB_PARTITION: '/mnt/data/fr-s-ivg-infv-p/tmp/crontab', # hostname
    PluginSettings.API_URL: 'http://localhost:8888/api/v1'
})

def load(info):
    info['apiRoot'].slurm = rest.Slurm()
    SlurmModel()
    events.bind('slurm.schedule', 'slurm', event_handlers.schedule)
    events.bind('cron.watch', 'slurm', event_handlers.cronWatch)