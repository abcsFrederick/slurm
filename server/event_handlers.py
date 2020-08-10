from subprocess import Popen, PIPE
import datetime
import sys, os
import re
from crontab import CronTab

from girder.models.setting import Setting
from girder.plugins.jobs.constants import JobStatus
from girder.plugins.jobs.models.job import Job

from .constants import PluginSettings


'''
slurm_info = { 'name': 'slurm job name',
               'entry': 'entry.py'

}
'''
def schedule(event):
    """
    This is bound to the "jobs.schedule" event, and will be triggered any time
    a job is scheduled. This handler will process any job that has the
    handler field set to "worker_handler".
    """
    job = event.info
    # shellScript = job['shellScript']
    if job['handler'] == 'slurm_handler' and job['otherFields'] is not None:
        try:
            slurm_info = job['otherFields']['slurm_info']
        except Exception:
            return 'Slurm information is not provided'

        slurmJobName = slurm_info['name']
        Job().updateJob(job, status=JobStatus.QUEUED)

        batchscript = """
            #! /bin/bash
            #SBATCH --partition=gpu
            #SBATCH --job-name={name}
            #SBATCH --nodes=1
            #SBATCH --ntasks=2
            #SBATCH --gres=gpu:p100:1
            #SBATCH --mem-per-cpu=32gb
            #SBATCH --output={shared_partition_log}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID.out
            #SBATCH --error={log_dir}/{name}/%j.err

            mkdir -p {shared_partition_output}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID
            python {pythonScriptPath} --output {shared_partition_output}/slurm-$SLURM_JOB_NAME.$SLURM_JOB_ID
        """
        script = batchscript.format(name=job['name'],
                                    log_dir='/mnt')
        try:

            # res = Popen(['sbatch','test.sh'], stdout=PIPE, stderr=PIPE)
            # retcode = res.wait()
            job['slurmJobId'] = 'temp'
            job['type'] = 'slurm'
            job['log'] = ''
            Job().updateJob(job, status=JobStatus.RUNNING)
            while not retcode:
                retcode = res.wait()
            Job().updateJob(job, status=JobStatus.SUCCESS)
            out = res.stdout.read()
        except Exception:
            print 'something wrong during slurm'
        print 'asyc continue'
def watch(event):
    import random
    jobId = str(event.info['jobId'])
    settings = Setting()

    CRONTAB_PARTITION = settings.get(PluginSettings.CRONTAB_PARTITION)
    logPath = os.path.join(CRONTAB_PARTITION, jobId)
    shellPath = os.path.join(CRONTAB_PARTITION, 'crontab.sh')
    randomId = str(random.getrandbits(128))
    cron = CronTab(user=True)
    job = cron.new(command=shellPath + ' ' + jobId + ' ' + randomId + ' >> ' + logPath + ' 2>&1\n')

    job.set_comment(randomId)
    job.minute.every(1)
    job.enable()
    cron.write()
    # for result in cron.run_scheduler(cadence=1, warp=True):
    #     with cron.log as log:
    #         lines = list(log.readlines())
    #         if re.search(jobId, lines[0][-1]) is None:
    #             print 'slurm job finished'
    #             break

