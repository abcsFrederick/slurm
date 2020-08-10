from bson import ObjectId
import os
import subprocess

from girder import events
from girder.models.setting import Setting
from girder.api.rest import Resource
from girder.api.describe import Description, autoDescribeRoute
from girder.api import access
from girder.constants import AccessType, TokenScope

from girder.plugins.jobs.models.job import Job
from girder.plugins.jobs.constants import JobStatus

from . import event_handlers
from .constants import PluginSettings
import datetime


class Slurm(Resource):
    def __init__(self):
        super(Slurm, self).__init__()
        self.resourceName = 'slurm'

        self.name = 'test'
        self.entry = None
        self.partition = 'norm'
        self.nodes = 1
        self.ntasks = 2
        self.gres = 'gpu:p100:1'
        self.mem_per_cpu = '32gb'

        self.route('GET', (), self.getSlurm)
        self.route('PUT', ('cancel', ':id'), self.cancelSlurm)
        self.route('POST', (), self.submitSlurmJob)
        self.route('GET', ('settings',), self.getSettings)
        self.route('POST', ('update',), self.update)
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

        job['meta']['slurm_info'] = {}
        job['meta']['slurm_info']['name'] = Slurm().name
        job['meta']['slurm_info']['entry'] = 'test.py'

        settings = Setting()
        SHARED_PARTITION = settings.get(PluginSettings.SHARED_PARTITION)
        shared_partition_log = os.path.join(SHARED_PARTITION, 'logs')
        shared_partition_output = os.path.join(SHARED_PARTITION, 'outputs')
        modulesPath = os.path.join(SHARED_PARTITION, 'modules')
        pythonScriptPath = os.path.join(modulesPath, job['meta']['slurm_info']['entry'])

        Job().updateJob(job, status=JobStatus.QUEUED)

        batchscript = """#!/bin/bash
            #SBATCH --partition={partition}
            #SBATCH --job-name={name}
            #SBATCH --nodes={nodes}
            #SBATCH --ntasks={ntasks}
            #SBATCH --gres={gres}
            #SBATCH --mem-per-cpu={mem_per_cpu}
            #SBATCH --output={shared_partition_log}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID.out
            #SBATCH --error={shared_partition_log}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID.err

            mkdir -p {shared_partition_output}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID
            python {pythonScriptPath} --output {shared_partition_output}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID
        """
        script = batchscript.format(name=Slurm().name,
                                    partition=Slurm().partition,
                                    nodes=Slurm().nodes,
                                    ntasks=Slurm().ntasks,
                                    gres=Slurm().gres,
                                    mem_per_cpu=Slurm().mem_per_cpu,
                                    shared_partition_log=shared_partition_log,
                                    shared_partition_output=shared_partition_output,
                                    pythonScriptPath=pythonScriptPath)

        shellPath = os.path.join(SHARED_PARTITION, 'shells')
        shellScriptPath = os.path.join(shellPath, 'test.sh')
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
            job['meta']['slurm_info']['slurm_id'] = slurmJobId
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
        job = Job().findOne({'meta.slurm_info.slurm_id': slurmJobId})
        Job().updateJob(job, status=JobStatus.SUCCESS)
        return commentId + ' crontab remove and update ' + slurmJobId + ' slurm job id.'
