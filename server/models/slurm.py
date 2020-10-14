from girder import events
from girder.constants import AccessType
from girder.exceptions import ValidationException
from girder.models.model_base import AccessControlledModel


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
            'time'
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
            'time'
        )
        self.exposeFields(AccessType.READ, fields)
        events.bind('model.user.save.created', 'slurm', self._createSlurmConfiguration)

    def _createSlurmConfiguration(self, event):
        user = event.info
        if self.findOne({'user': user['_id']}) is None:
            doc = {
                'user': user['_id'],
                'partition': 'norm',
                'gres': "",
                'nodes': 1,
                'ntasks': 1,
                'cpu_per_task': 1,
                'mem_per_cpu': 16,
                'time': 1
            }
            self.save(doc)

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