from subprocess import Popen, PIPE
import datetime
import sys

from girder.plugins.jobs.constants import JobStatus
from girder.plugins.jobs.models import Job


def schedule(event):
    """
    This is bound to the "jobs.schedule" event, and will be triggered any time
    a job is scheduled. This handler will process any job that has the
    handler field set to "worker_handler".
    """
    job = event.info
    # shellScript = job['shellScript']
    if job['handler'] == 'slurm_handler':

        Job().updateJob(job, status=JobStatus.QUEUED)

        batchscript = """
            #! /bin/bash
            #SBATCH --partition=gpu
            #SBATCH --job-name={name}
            #SBATCH --nodes=1
            #SBATCH --ntasks=2
            #SBATCH --gres=gpu:p100:1
            #SBATCH --mem-per-cpu=32gb
            #SBATCH --mail-type=END
            #SBATCH --output={log_dir}/{name}/%J.out
            #SBATCH --error={log_dir}/{name}/%J.err
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