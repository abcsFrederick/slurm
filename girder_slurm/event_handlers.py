import threading
import subprocess
import datetime
import sys, os
import re
from crontab import CronTab
from time import sleep

from girder import events
from girder.models.setting import Setting
from girder_jobs.constants import JobStatus
from girder_jobs.models.job import Job
import girder_slurm.girder_io.output as girderOutput

from .constants import PluginSettings

'''
slurm_info_basic = { 'name': 'test',
               'entry': 'entry.py',
               'partition': 'norm',
               'nodes': 1
               'ntasks': 2
               'gres': 'gpu:p100:1'
               'mem-per-cpu': '32gb'
}
'''
def schedule(event):
    """
    This is bound to the "jobs.schedule" event, and will be triggered any time
    a job is scheduled. This handler will process any job that has the
    handler field set to "worker_handler".
    """
    job = event.info
    slurm_info_new = job['otherFields']['slurm_info']
    # shellScript = job['shellScript']
    if job['handler'] == 'slurm_handler' and slurm_info_new['entry'] is not None:
        # fetch_input(job)
        settings = Setting()
        SHARED_PARTITION = settings.get(PluginSettings.SHARED_PARTITION)
        shared_partition_log = os.path.join(SHARED_PARTITION, 'logs')
        shared_partition_work_directory = os.path.join(SHARED_PARTITION, 'tmp')
        modulesPath = os.path.join(SHARED_PARTITION, 'modules')
        pythonScriptPath = os.path.join(modulesPath, slurm_info_new['entry'])

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

source /etc/profile.d/modules.sh
module load {modules}
mkdir -p {shared_partition_work_directory}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID
"""
        execCommand = """python3.6 {pythonScriptPath} --directory {shared_partition_work_directory}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID """
        for name in job['kwargs']['inputs']:
            if isinstance(job['kwargs']['inputs'][name]['data'], list):
                arg = "--" + name + " " + ' '.join('"{0}"'.format(i) for i in job['kwargs']['inputs'][name]['data']) + " "
            else:
                arg = "--" + name + " '" + str(job['kwargs']['inputs'][name]['data']) + "' "
            execCommand += arg
        batchscript += execCommand
        script = batchscript.format(name=slurm_info_new['name'],
                                    partition=slurm_info_new['partition'],
                                    nodes=slurm_info_new['nodes'],
                                    ntasks=slurm_info_new['ntasks'],
                                    gres=slurm_info_new['gres'],
                                    mem_per_cpu=slurm_info_new['mem_per_cpu'],
                                    modules=" ".join(slurm_info_new['modules']),
                                    shared_partition_log=shared_partition_log,
                                    shared_partition_work_directory=shared_partition_work_directory,
                                    pythonScriptPath=pythonScriptPath)
        shellPath = os.path.join(SHARED_PARTITION, 'shells')
        shellScriptPath = os.path.join(shellPath, slurm_info_new['name'] + '.sh')
        with open(shellScriptPath, "w") as sh:
            sh.write(script)
        try:
            args = ['sbatch']
            args.append(sh.name)
            res = subprocess.check_output(args).strip()
            if not res.startswith(b"Submitted batch"):
                return None
            slurmJobId = int(res.split()[-1])
            # crontab method
            # events.trigger('cron.watch', {'slurmJobId': slurmJobId})
            # thread method
            threading.Thread(target=loopWatch, args=([str(slurmJobId)])).start()
            job['otherFields']['slurm_info']['slurm_id'] = slurmJobId
            Job().save(job)
            Job().updateJob(job, status=JobStatus.RUNNING)
        except Exception:
            return 'something wrong during slurm start'
        
        return slurmJobId

def cronWatch(event):
    import random
    slurmJobId = str(event.info['slurmJobId'])
    settings = Setting()

    CRONTAB_PARTITION = settings.get(PluginSettings.CRONTAB_PARTITION)
    logPath = os.path.join(CRONTAB_PARTITION, slurmJobId)
    shellPath = os.path.join(os.path.dirname(__file__), 'crontab.sh')
    commentId = str(random.getrandbits(128))
    cron = CronTab(user=True)
    job = cron.new(command=shellPath + ' ' + slurmJobId + ' ' + commentId + ' >> ' + logPath + ' 2>&1\n')
    job.set_comment(commentId)
    job.minute.every(1)
    job.enable()
    cron.write()

def loopWatch(slurmJobId):
    settings = Setting()
    SHARED_PARTITION = settings.get(PluginSettings.SHARED_PARTITION)
    shared_partition_log = os.path.join(SHARED_PARTITION, 'logs')
    shared_partition_work_directory = os.path.join(SHARED_PARTITION, 'tmp')
    while True:
        args = 'squeue -j {}'.format(slurmJobId)
        output = subprocess.Popen(args,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out_put = output.communicate()[0]
        found = re.findall(slurmJobId, out_put.decode())
        if len(found) == 0:
            job = Job().findOne({'otherFields.slurm_info.slurm_id': int(slurmJobId)})
            Job().updateJob(job, status=JobStatus.SUCCESS)
            log_file_name = 'slurm-{}.{}.out'.format(job['otherFields']['slurm_info']['name'], slurmJobId)
            log_file_path = os.path.join(shared_partition_log, log_file_name)
            f = open(log_file_path, "r")
            content = f.read()
            Job().updateJob(job, log=content)
            f.close()
            err_file_name = 'slurm-{}.{}.err'.format(job['otherFields']['slurm_info']['name'], slurmJobId)
            err_file_path = os.path.join(shared_partition_log, err_file_name)
            f = open(err_file_path, "r")
            content = f.read()
            Job().updateJob(job, log=content)
            f.close()
            # Job().save(job)
            # _send_to_girder
            slurm_output_name = 'slurm-{}.{}'.format(job['otherFields']['slurm_info']['name'], slurmJobId)
            data = os.path.join(shared_partition_work_directory, slurm_output_name)
            girderOutput.sendOutputToGirder(job, data)
            break
        sleep(1)