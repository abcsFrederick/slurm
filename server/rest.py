from bson import ObjectId
import os
import subprocess
from subprocess import PIPE, Popen
from girder import events
from girder.models.setting import Setting
from girder.models.folder import Folder

from girder.api.rest import Resource
from girder.api.describe import Description, autoDescribeRoute
from girder.api import access
from girder.constants import AccessType, TokenScope

from girder.plugins.jobs.models.job import Job
from girder.plugins.jobs.constants import JobStatus

import girder_io.input as girderInput
from . import event_handlers
from .constants import PluginSettings
import datetime

from .models.slurm import Slurm as SlurmModel

class Slurm(Resource):
    def __init__(self):
        super(Slurm, self).__init__()
        self.resourceName = 'slurm'
        self.user = self.getCurrentUser()
        self.token = self.getCurrentToken()

        self.name = 'test'
        self.entry = None
        self.partition = 'norm'
        self.nodes = 1
        self.ntasks = 2
        self.gres = 'gpu:p100:1'
        self.mem_per_cpu = '32gb'

        settings = Setting()
        self.SHARED_PARTITION = settings.get(PluginSettings.SHARED_PARTITION)
        self._shared_partition_log = os.path.join(self.SHARED_PARTITION, 'logs')
        self._shared_partition_work_directory = os.path.join(self.SHARED_PARTITION, 'tmp')
        self._modulesPath = os.path.join(self.SHARED_PARTITION, 'modules')
        self._shellPath = os.path.join(self.SHARED_PARTITION, 'shells')

        self.route('GET', ('slurmOption',), self.getSlurmOption)
        self.route('PUT', ('slurmOption',), self.setSlurmOption)
        self.route('GET', (), self.getSlurm)
        self.route('PUT', ('cancel', ':id'), self.cancelSlurm)
        self.route('POST', (), self.submitSlurmJob)
        self.route('GET', ('settings',), self.getSettings)
        self.route('POST', ('update',), self.update)
        self.route('PUT', ('updatestep',), self.updateStep)

    # for test propose
    @access.public
    @autoDescribeRoute(
        Description('Search for segmentation by certain properties.')
        .notes('You must pass a "parentId" field to specify which parent folder'
               'you are searching for children folders and items segmentation information.')
        .errorResponse()
        .errorResponse('Read access was denied on the parent resource.', 403)
    )
    def getSlurmOption(self):
        if SlurmModel().findOne({'user': self.getCurrentUser()['_id']}) is None:
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
            SlurmModel().save(doc)
        return SlurmModel().findOne({'user': self.getCurrentUser()['_id']})

    @access.public
    @autoDescribeRoute(
        Description('Search for segmentation by certain properties.')
        .param('partition', 'Partition.', required=True, enum=['quick', 'norm', 'gpu'])
        .param('gres', 'Generic Resource (GRES) Scheduling.', required=False)
        .param('nodes', 'Node count required for the job.', required=True, dataType='integer')
        .param('ntasks', 'Number of task.', required=True, dataType='integer')
        .param('cpu_per_task', 'Cpu per task.', required=True, dataType='integer')
        .param('mem_per_cpu', 'Memery per cpu (GB).', required=True, dataType='integer')
        .param('time', 'Time out (hour).', required=True, dataType='integer')
    )
    def setSlurmOption(self, partition, gres, nodes, ntasks, cpu_per_task, mem_per_cpu, time):
        doc = SlurmModel().findOne({'user': self.getCurrentUser()['_id']})
        doc['partition'] = partition
        doc['gres'] = gres
        doc['nodes'] = nodes
        doc['ntasks'] = ntasks
        doc['cpu_per_task'] = cpu_per_task
        doc['mem_per_cpu'] = mem_per_cpu
        doc['time'] = mem_per_cpu
        return SlurmModel().save(doc)
    # Find link record based on original item ID or parentId(to check chirdren links)
    # Return only record that have READ access(>=0) to user.
    # @access.user(scope=TokenScope.DATA_READ)
    @access.public
    @autoDescribeRoute(
        Description('Search for segmentation by certain properties.')
        .notes('You must pass a "parentId" field to specify which parent folder'
               'you are searching for children folders and items segmentation information.')
        .errorResponse()
        .errorResponse('Read access was denied on the parent resource.', 403)
    )
    def getSlurm(self):
        hostname = ''
        res = Popen(['squeue'], stdout=PIPE, stderr=PIPE)
        for line in res.stdout:
            line = line.rstrip()
            print(line)
        return res.stdout

    @access.public
    @autoDescribeRoute(
        Description('Search for segmentation by certain properties.')
        .notes('You must pass a "parentId" field to specify which parent folder'
               'you are searching for children folders and items segmentation information.')
        .errorResponse()
        .errorResponse('Read access was denied on the parent resource.', 403)
    )
    def cancelSlurm(self):
        res = Popen(['scancel',''], stdout=PIPE, stderr=PIPE)
        retcode = res.wait()
        while not retcode:
            retcode = res.wait()

    @access.public
    @autoDescribeRoute(
        Description('Testing slurm job sumbit')
        .notes('You must pass a "parentId" field to specify which parent folder'
               'you are searching for children folders and items segmentation information.')
        .errorResponse()
        .errorResponse('Read access was denied on the parent resource.', 403)
    )
    def submitSlurmJob(self):
        title = 'slurm test'

        job = Job().createJob(title=title, type='split',
                              handler='slurm_handler', user=self.getCurrentUser())
        folder = Folder().load('5eda8bd57441a06858e80c82', level=AccessType.READ, user=self.user)

        inputs = {
            'subfolders': {
                'mode': 'inline',
                'type': 'string',
                'format': 'string',
                'data': ["Implants_1/425362-245-T_1505_1506_1507_1 00016036/00016881 425362-245-T (AY7U80T73)_Melanoma/00066314 TSE45 MR"]
            },
            'axis': {
                'mode': 'inline',
                'type': 'string',
                'format': 'string',
                'data': ["1"],
            },
            'n_of_split': {
                'mode': 'inline',
                'type': 'string',
                'format': 'string',
                'data': [3],
            },
            'order': {
                'mode': 'inline',
                'type': 'string',
                'format': 'string',
                'data': ["1,1,1"],
            }
        }
        job['kwargs'] = {
            'inputs': inputs
        }
        job['otherFields'] = {}
        job['otherFields']['slurm_info'] = {}
        job['otherFields']['slurm_info']['name'] = Slurm().name
        job['otherFields']['slurm_info']['entry'] = 'test.py'

        inputs['topFolder'] = girderInput.girderInputSpec(
                    folder, resourceType='folder', token=self.token)

        pythonScriptPath = os.path.join(self._modulesPath, job['otherFields']['slurm_info']['entry'])

        Job().updateJob(job, status=JobStatus.QUEUED)

        batchscript = """#!/bin/bash
#SBATCH --partition={partition}
#SBATCH --job-name={name}
#SBATCH --nodes={nodes}
#SBATCH --ntasks={ntasks}
#SBATCH --gres={gres}
#SBATCH --mem-per-cpu={mem_per_cpu}
#SBATCH --output={shared_partition_log}/slurm-%x.%j.out
#SBATCH --error={shared_partition_log}/slurm-%x.%j.err

mkdir -p {shared_partition_work_directory}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID
"""
        execCommand = """python {pythonScriptPath} --directory {shared_partition_work_directory}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID """

        for name in job['kwargs']['inputs']:
            arg = "--" + name + " " + str(inputs[name]['data']) + " "
            execCommand += arg
        batchscript += execCommand

        script = batchscript.format(name=Slurm().name,
                                    partition=Slurm().partition,
                                    nodes=Slurm().nodes,
                                    ntasks=Slurm().ntasks,
                                    gres=Slurm().gres,
                                    mem_per_cpu=Slurm().mem_per_cpu,
                                    shared_partition_log=self._shared_partition_log,
                                    shared_partition_work_directory=self._shared_partition_work_directory,
                                    pythonScriptPath=pythonScriptPath)

        print script
        shellScriptPath = os.path.join(self._shellPath, job['otherFields']['slurm_info']['name'] + '.sh')
        with open(shellScriptPath, "w") as sh:
            sh.write(script)
        try:
            args = ['sbatch']
            args.append(sh.name)
            res = subprocess.check_output(args).strip()
            if not res.startswith(b"Submitted batch"):
                return None
            slurmJobId = int(res.split()[-1])

            events.trigger('cron.watch', {'slurmJobId': slurmJobId})
            job['otherFields']['slurm_info']['slurm_id'] = slurmJobId
            job = Job().save(job)
            Job().updateJob(job, status=JobStatus.RUNNING)
            
        except Exception:
            return 'something wrong during slurm start'

        return slurmJobId
    @access.public
    @autoDescribeRoute(
        Description('Getting Slurm task settings.')
    )
    def getSettings(self):
        settings = Setting()
        return {
            PluginSettings.SHARED_PARTITION:
                settings.get(PluginSettings.SHARED_PARTITION),
            PluginSettings.CRONTAB_PARTITION:
                settings.get(PluginSettings.CRONTAB_PARTITION)
            }

    @access.public
    @autoDescribeRoute(
        Description('Update job info on girder when slurm job is finished.')
        .param('slurmJobId', 'slurm job id.', required=True)
        .param('commentId', 'crontab id for monitoring.', required=True)
    )
    def update(self, slurmJobId, commentId):
        from crontab import CronTab

        cron = CronTab(user=True)
        crons = cron.find_comment(commentId)

        for cronjob in crons:
            cron.remove(cronjob)
            cron.write()
        job = Job().findOne({'otherFields.slurm_info.slurm_id': int(slurmJobId)})
        Job().updateJob(job, status=JobStatus.SUCCESS)

        log_file_name = 'slurm-{}.{}.out'.format(job['otherFields']['slurm_info']['name'], slurmJobId)
        log_file_path = os.path.join(self._shared_partition_log, log_file_name)
        f = open(log_file_path, "r")
        content = f.read()
        job['log'].append(content)
        f.close()
        job.save()
        # _send_to_girder
        # push_output(job, slurmJobId)
        return commentId + ' crontab remove and update ' + str(job['_id']) + ' job status.'

    @access.public
    @autoDescribeRoute(
        Description('Update job info on girder when slurm job is finished.')
        .param('slurmJobId', 'slurm job id.', required=True)
    )
    def updateStep(self, slurmJobId):
        job = Job().findOne({'otherFields.slurm_info.slurm_id': int(slurmJobId)})
        # send log to girder periodic
        log_file_name = 'slurm-{}.{}.out'.format(job['otherFields']['slurm_info']['name'], slurmJobId)
        log_file_path = os.path.join(self._shared_partition_log, log_file_name)
        f = open(log_file_path, "r")
        content = f.read()
        job['log'].append(content)
        f.close()
        job.save()
        return 'Updated log'
