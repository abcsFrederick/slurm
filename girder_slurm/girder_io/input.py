from girder.models.setting import Setting
from ..constants import PluginSettings
from .. import utils
from girder_slurm.girder_io import fetch_input
from girder.exceptions import FilePathException
from girder.models.file import File


def getWorkerApiUrl():
    """
    Return the API base URL to which the worker should callback to
    write output information back to the server. This is controlled
    via a system setting, and the default is to use the core server
    root setting.
    """
    apiUrl = Setting().get(PluginSettings.API_URL)
    return apiUrl or getApiUrl()

@utils.with_tmpdir
def girderInputSpec(resource, resourceType='file', name=None, token=None,
                    dataType='string', dataFormat='text', fetchParent=False, **kwargs):
    """
    Downstream plugins that are building Girder worker jobs that use Girder IO
    should use this to generate the input specs more easily.
    :param resource: The resource document to be downloaded at runtime.
    :type resource: dict
    :param resourceType: The resource type to download for the input. Should
        be "folder", "item", or "file".
    :type resourceType: str
    :param name: The name of the resource to download. If not passed, uses
        the "name" field of the resource document.
    :type name: str or None
    :param token: The Girder token document or raw token string to use to
        authenticate when downloading. Pass `None` for anonymous downloads.
    :type token: dict, str, or None
    :param dataType: The worker `type` field.
    :type dataType: str
    :param dataFormat: The worker `format` field.
    :type dataFormat: str
    :param fetchParent: Whether to fetch the whole parent resource of the
        specified resource as a side effect.
    :type fetchParent: bool
    """
    if isinstance(token, dict):
        token = token['_id']

    result = {
        'mode': 'girder',
        'api_url': getWorkerApiUrl(),
        'token': token,
        'id': str(resource['_id']),
        'name': name or resource['name'],
        'resource_type': resourceType,
        'type': dataType,
        'format': dataFormat,
        'fetch_parent': fetchParent,
        'kwargs': kwargs
    }

    if resourceType == 'file' and not fetchParent: # and Setting().get(PluginSettings.DIRECT_PATH):
        # If we are adding a file and it exists on the local filesystem include
        # that location.  This can permit the user of the specification to
        # access the file directly instead of downloading the file.
        try:
            result['direct_path'] = File().getLocalFilePath(resource)
        except FilePathException:
            pass
    path = fetch_input(result)
    result['data'] = path
    return result