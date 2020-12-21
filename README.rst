====================================
Slurm |build-status| |codecov-io|
====================================


.. |build-status| image:: https://travis-ci.org/abcsFrederick/slurm.svg?branch=master
    :target: https://travis-ci.org/abcsFrederick/slurm?branch=master
    :alt: Build Status

.. |codecov-io| image:: https://codecov.io/gh/abcsFrederick/slurm/branch/master/graphs/badge.svg?branch=master
    :target: https://codecov.io/gh/abcsFrederick/slurm/branch/master
    :alt: codecov.io


Girder plugin for FRCE slurm connection.

This plugin wrap sbatch command and shows the idea of submit slurm job to remote cluster and watch slurm status for getting result.
Two method to keep monitor submit job status: 

**Crontab:**
  As system based crontab will be started to monitor slurm task in minute. The limitation is it will not get immediate status for short-term task because crontab monitor per second.

**Repeated monitor(Currently Used):**
  It will start a thread for monitor each task in sec.


1. Prepare:
-----------

1. You need to have your a shared partition mounted (e.g. /mounted) on you girder environment and your remote slurm cluster.

2. You also need four subfolders:

**/mounted/tmp** for temp input data fetched from girder and output data after slurm task finish

**/mounted/modules** for python entry point script, put your python script for running under modules folder and run link_module.sh to copy paste your entry script to /mounted/modules.

**/mounted/logs** for slurm .info and .err log file

**/mounted/shells** slurm start up batch script

3. You need to have slurm client installed on you girder server

2. Install 
-----------
Install as normal girder plugin:

Direct to slurm folder

``pip install -e .``

3. How to use
-----------
Go to plugin configuration, type and save required information

SHARED_PARTITION: Your_mount_partition

CRONTAB_PARTITION: Your_crontab_partition_on_girder_server (For using crontab method)

API_URL: API

Following explain how to use slurm model in your code:

.. code-block:: python

  # Import slurm model and util
  from girder_slurm.models.slurm import Slurm as slurmModel
  from girder_slurm import utils as slurmUtils

  # Use slurm model to create a slurm job
  # Make handler as 'slurm_handler' instead on 'worker_handler' will force task to run on slurm cluster
  job = slurmModel().createJob(title='title', type='type',
                               taskName='taskName',
                               taskEntry='taskEntry.py',
                               modules=['module_available_on_slurm', 'torch/1.7.0'],
                               handler='slurm_handler', user=user)

  jobToken = Job().createJobToken(job)
  # Use slurm util to setup task json schema
  inputs = {
      'inputImage': slurmGirderInput.girderInputSpec(
                      fileObj, resourceType='file', token=token)
  }
  reference = json.dumps({'jobId': str(job['_id'])})
  pushItem = Item().load(outputId, level=level, user=self.getCurrentUser())
  # Name can be anything because output will be found based on slurm job id
  outputs = {
      'whateverName': slurmGirderOutput.girderOutputSpec(pushItem, token,
                                              parentType='item',
                                              name='',
                                              reference=reference),
  }
  job['meta'] = {
      'creator': 'creator',
      'task': 'task',
  }
  job['kwargs'] = {
      'inputs': inputs,
      'outputs': outputs,
      'jobInfo': slurmUtils.jobInfoSpec(job, jobToken),
      'auto_convert': True,
      'validate': True,
  }
  job = Job().save(job)
  # Schedule to start slurm job which will trigger slurm handler to submit sbatch
  slurmModel().scheduleSlurm(job)