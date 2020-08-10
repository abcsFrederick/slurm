import subprocess
import datetime
import sys, os
import re
from crontab import CronTab

from girder.models.setting import Setting
from girder.plugins.jobs.constants import JobStatus
from girder.plugins.jobs.models.job import Job

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
        settings = Setting()
        SHARED_PARTITION = settings.get(PluginSettings.SHARED_PARTITION)
        shared_partition_log = os.path.join(SHARED_PARTITION, 'logs')
        shared_partition_output = os.path.join(SHARED_PARTITION, 'outputs')
        modulesPath = os.path.join(SHARED_PARTITION, 'modules')
        pythonScriptPath = os.path.join(modulesPath, slurm_info_new['entry'])

        Job().updateJob(job, status=JobStatus.QUEUED)

        batchscript = """
            #! /bin/bash
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
        script = batchscript.format(name=slurm_info_new['name'],
                                    partition=slurm_info_new['partition'],
                                    nodes=slurm_info_new['nodes'],
                                    ntasks=slurm_info_new['ntasks'],
                                    gres=slurm_info_new['gres'],
                                    mem_per_cpu=slurm_info_new['mem_per_cpu'],
                                    shared_partition_log=shared_partition_log,
                                    shared_partition_output=shared_partition_output,
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

            events.trigger('cron.watch', {'slurmJobId': slurmJobId})
            job['otherFields']['slurm_info']['slurm_id'] = slurmJobId
            Job().updateJob(job, status=JobStatus.RUNNING)
            
        except Exception:
            return 'something wrong during slurm start'
        
        return slurmJobId

def watch(event):
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

