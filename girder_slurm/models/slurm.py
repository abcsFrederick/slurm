import datetime
from bson import json_util

from girder import events
from girder.constants import AccessType
from girder.exceptions import ValidationException
from girder.models.model_base import AccessControlledModel
from girder.models.notification import Notification
from girder_jobs.constants import JobStatus
from girder_jobs.models.job import Job as JobModel

class Slurm(AccessControlledModel):
    def initialize(self):
        self.name = 'slurm'
        self.ensureIndices([
            'user',
            'partition',
            'gres',
            'nodes',
            'ntasks',
            'mem_per_cpu',
            'time',
            'modules'
        ])
        fields = (
            '_id',
            'user',
            'partition',
            'gres',
            'nodes',
            'ntasks',
            'cpu_per_task',
            'mem_per_cpu',
            'time',
            'modules'
        )
        fields += ('title', 'type', 'created', 'interval', 'when', 'status',
            'progress', 'log', 'meta', '_id', 'public', 'parentId', 'async',
            'updated', 'timestamps', 'handler', 'jobInfoSpec', 'otherFields')
        self.exposeFields(AccessType.READ, fields)
        # events.bind('model.user.save.created', 'slurm', self._createSlurmConfiguration)

    def list(self, user=None, types=None, statuses=None,
             limit=0, offset=0, sort=None, currentUser=None, parentJob=None):
        jobs = list(JobModel().findWithPermissions(
            offset=offset, limit=limit, sort=sort, user=currentUser,
            types=types, statuses=statuses, jobUser=user, parentJob=parentJob))

        slurm_jobs = [x for x in jobs if x['handler'] == 'slurm_handler']

        return slurm_jobs
    def createJob(self, title, type, taskName, taskEntry, modules="", requirements=None, args=(), kwargs=None, user=None, when=None,
                  interval=0, public=False, handler=None, asynchronous=False,
                  save=True, parentJob=None, otherFields=None, env=None, mem=None):
        now = datetime.datetime.utcnow()

        if when is None:
            when = now

        if kwargs is None:
            kwargs = {}
        # resource should depend on each task
        # slurmOptions = self.findOne({'user': user['_id']})

        # if slurmOptions is None:
        slurmOptions = {
            'user': user['_id'],
            'partition': 'gpu',
            'gres': "gpu:4",
            'nodes': 1,
            'ntasks': 1,
            'cpu_per_task': 1,
            'mem_per_cpu': 32,
            'time': 1,
            'modules': "",
        }
        self.save(slurmOptions)
        if mem:
            slurmOptions['mem_per_cpu'] = mem

        otherFields = {
            'otherFields': {
                'slurm_info': {
                    'name': taskName,
                    'entry': taskEntry,
                    'partition': slurmOptions['partition'],
                    'nodes': slurmOptions['nodes'],
                    'ntasks': slurmOptions['ntasks'],
                    'gres': slurmOptions['gres'],
                    'cpu_per_task': slurmOptions['cpu_per_task'],
                    'mem_per_cpu': str(slurmOptions['mem_per_cpu']) + 'gb',
                    'time': str(slurmOptions['time']) + ':00:00',
                    'modules': modules
                }
            }
        }
        if requirements:
            otherFields['otherFields']['slurm_info']['requirements'] = requirements
        if env:
            otherFields['otherFields']['slurm_info']['env'] = env
        parentId = None
        if parentJob:
            parentId = parentJob['_id']
        job = {
            'title': title,
            'type': type,
            'args': args,
            'kwargs': kwargs,
            'created': now,
            'updated': now,
            'when': when,
            'interval': interval,
            'status': JobStatus.INACTIVE,
            'progress': None,
            'log': [],
            'meta': {},
            'handler': handler,
            'asynchronous': asynchronous,
            'timestamps': [],
            'parentId': parentId
        }
        job.update(otherFields)

        self.setPublic(job, public=public)

        if user:
            job['userId'] = user['_id']
            self.setUserAccess(job, user=user, level=AccessType.ADMIN)
        else:
            job['userId'] = None
        if save:
            job = JobModel().save(job)
        if user:
            deserialized_kwargs = job['kwargs']
            job['kwargs'] = json_util.dumps(job['kwargs'])

            Notification().createNotification(
                type='job_created', data=job, user=user,
                expires=datetime.datetime.utcnow() + datetime.timedelta(seconds=30))

            job['kwargs'] = deserialized_kwargs
        return job
    def scheduleSlurm(self, job):
        """
        Trigger the event to schedule this job. Other plugins are in charge of
        actually scheduling and/or executing the job, except in the case when
        the handler is 'local'.
        """
        if job.get('async') is True:
            events.daemon.trigger('slurm.schedule', info=job)
        else:
            events.trigger('slurm.schedule', info=job)

    def validate(self, doc):
        validation = (
            ('partition', 'Partition'),
            ('nodes', 'Number of node'),
            ('ntasks', 'Number of task'),
            ('cpu_per_task', 'Cpu per task'),
            ('mem_per_cpu', 'Memery per cpu')
        )
        for field, message in validation:
            if doc.get(field) is None:
                raise ValidationException(message, field)
        return doc

    # Todo: GPU resource move to task based
    # def _createSlurmConfiguration(self, event):
    #     user = event.info
    #     if self.findOne({'user': user['_id']}) is None:
    #         if settings.get(PluginSettings.SLURM_PARTITION) == 'GPU':
    #             gres = 'gpu:1'
    #         else:
    #             gres = ''

    #         doc = {
    #             'user': user['_id'],
    #             'partition': settings.get(PluginSettings.SLURM_PARTITION),
    #             'gres': gres,
    #             'nodes': settings.get(PluginSettings.SLURM_NODES),
    #             'ntasks': settings.get(PluginSettings.SLURM_TASKS),
    #             'cpu_per_task': settings.get(PluginSettings.SLURM_TASKS),
    #             'mem_per_cpu': settings.get(PluginSettings.SLURM_CPU),
    #             'time': settings.get(PluginSettings.SLURM_TIME),
    #             'modules': ""
    #         }
    #         self.save(doc)
