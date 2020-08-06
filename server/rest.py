from bson import ObjectId
import os
import subprocess

from girder import events
from girder.models.setting import Setting
from girder.api.rest import Resource
from girder.api.describe import Description, autoDescribeRoute
from girder.api import access
from girder.constants import AccessType, TokenScope
from . import event_handlers
from .constants import PluginSettings
import datetime


class Slurm(Resource):
    def __init__(self):
        super(Slurm, self).__init__()
        self.resourceName = 'slurm'

        self.route('GET', (), self.getSlurm)
        self.route('PUT', ('cancel', ':id'), self.cancelSlurm)
        self.route('POST', (), self.submitSlurmJob)
        self.route('GET', ('settings',), self.getSettings)
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
        Description('Search for segmentation by certain properties.')
        .notes('You must pass a "parentId" field to specify which parent folder'
               'you are searching for children folders and items segmentation information.')
        .errorResponse()
        .errorResponse('Read access was denied on the parent resource.', 403)
    )
    def submitSlurmJob(self):
        settings = Setting()
        script = '''#!/bin/bash             
#SBATCH --job-name=ssr
#SBATCH --output=hello.log
#
#SBATCH --ntasks=1
#SBATCH --time=10:00
#SBATCH --mem-per-cpu=100

#for (( i=60; i>0; i--)); do
#  sleep 1 &
#  printf " $i "
#  wait
#done

python3 test.py
'''
        slurmJobName = 'test'
        SHARED_PARTITION = settings.get(PluginSettings.SHARED_PARTITION)
        shared_partition_log = os.path.join(SHARED_PARTITION, 'logs')
        shared_partition_output = os.path.join(SHARED_PARTITION, 'outputs')
        print SHARED_PARTITION
        # logPath = shared_partition
        modulesPath = os.path.join(SHARED_PARTITION, 'modules')
        pythonScriptPath = os.path.join(modulesPath, 'test.py')
        script = '''#!/bin/bash
#SBATCH --job-name={name}
#SBATCH --output={shared_partition_log}/slurm-%x.$SLURM_JOB_ID.out
mkdir -p {shared_partition_output}/slurm-%x.$SLURM_JOB_ID
python {pythonScriptPath} --output {shared_partition_output}/slurm-%x.$SLURM_JOB_ID
'''
        script = script.format(name=slurmJobName,
                               shared_partition_log=shared_partition_log,
                               shared_partition_output=shared_partition_output,
                               pythonScriptPath=pythonScriptPath)
        shellPath = os.path.join(SHARED_PARTITION, 'shells')
        shellScriptPath = os.path.join(shellPath, 'test.sh')
        with open(shellScriptPath, "w") as sh:
            sh.write(script)
        # res = Popen(['chmod', '755', sh.name], stdout=PIPE, stderr=PIPE)
        # res = Popen([sh.name], stdout=PIPE, stderr=PIPE)
        args = ['sbatch']
        args.append(sh.name)
        res = subprocess.check_output(args).strip()
        print res

        if not res.startswith(b"Submitted batch"):
            return None
        jobId = int(res.split()[-1])
        return jobId
        events.trigger('cron.watch', jobId=jobId)


        # slurmJob = {'id': jobId,
        #             'handler': 'slurm',
        #             'name': slurmJobName,
        #             'script': script,
        #             'status': 2,
        #             'timestamps':[]}
    @access.public
    @autoDescribeRoute(
        Description('Getting Slurm task settings.')
    )
    def getSettings(self):
        settings = Setting()
        return {
            PluginSettings.SHARED_PARTITION:
                settings.get(PluginSettings.SHARED_PARTITION)
        }