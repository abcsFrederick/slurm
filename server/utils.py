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