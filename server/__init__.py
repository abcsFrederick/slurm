from . import rest
from . import event_handlers
from girder import events


def load(info):
    info['apiRoot'].slurm = rest.Slurm()
    events.bind('jobs.schedule', 'slurm', event_handlers.schedule)
