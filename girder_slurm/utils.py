import os
import tempfile
import contextlib
import functools
import shutil
from girder.models.setting import Setting
from .constants import PluginSettings


@contextlib.contextmanager
def tmpdir(cleanup=True):
    # Make the temp dir underneath tmp_root config setting
    settings = Setting()
    tmp = os.path.join(settings.get(PluginSettings.SHARED_PARTITION), 'tmp')
    root = os.path.abspath(tmp)
    try:
        os.makedirs(root)
    except OSError:
        if not os.path.isdir(root):
            raise
    path = tempfile.mkdtemp(dir=root)

    try:
        yield path
    finally:
        # Cleanup the temp dir
        # if cleanup and os.path.isdir(path):
        #     shutil.rmtree(path)
        pass

def with_tmpdir(fn):
    """
    This function is provided as a convenience to allow use as a decorator of
    a function rather than using "with tmpdir()" around the whole function
    body. It passes the generated temp dir path into the function as the
    special kwarg "_tempdir".
    """
    @functools.wraps(fn)
    def wrapped(*args, **kwargs):
        if '_tempdir' in kwargs:
            return fn(*args, **kwargs)

        cleanup = kwargs.get('cleanup', True)
        with tmpdir(cleanup=cleanup) as tempdir:
            kwargs['_tempdir'] = tempdir
            return fn(*args, **kwargs)
    return wrapped

def jobInfoSpec(job, token=None, logPrint=True):
    """
    Build the jobInfo specification for a task to write status and log output
    back to a Girder job.

    :param job: The job document representing the worker task.
    :type job: dict
    :param token: The token to use. Creates a job token if not passed.
    :type token: str or dict
    :param logPrint: Whether standard output from the job should be
    """
    if token is None:
        token = Job().createJobToken(job)

    if isinstance(token, dict):
        token = token['_id']

    return {
        'method': 'PUT',
        'url': '/'.join((getWorkerApiUrl(), 'job', str(job['_id']))),
        'reference': str(job['_id']),
        'headers': {'Girder-Token': token},
        'logPrint': logPrint
    }