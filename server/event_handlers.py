import subprocess
import datetime
import sys


def schedule(event):
    """
    This is bound to the "jobs.schedule" event, and will be triggered any time
    a job is scheduled. This handler will process any job that has the
    handler field set to "worker_handler".
    """
    job = event.info
    if job['handler'] == 'slurm_handler':

        batchscript = """
            #! /bin/bash
            #SBATCH --partition=norm
            #SBATCH --job-name=Test
            #SBATCH --time=100-00:00:00
            #SBATCH --nodes=1
            #SBATCH --ntasks=16
            #SBATCH --mem-per-cpu=32gb
            #SBATCH --mail-type=END
            #SBATCH --error=/path/to/error/file 

            cd /path/to/work/dir
        """
        res = subprocess.check_output('squeue').strip()
        print res