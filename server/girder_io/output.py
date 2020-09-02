from girder.models.setting import Setting
from ..constants import PluginSettings
from .. import utils
from girder.plugins.slurm.girder_io import send_output


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
def girderOutputSpec(job, slurmJobId, token=None):
    if isinstance(token, dict):
        token = token['_id']

    job['outputs'] = {
        'api_url': getWorkerApiUrl(),
        'token': token,
        
    }
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

    if resourceType == 'file' and not fetchParent and Setting().get(PluginSettings.DIRECT_PATH):
        # If we are adding a file and it exists on the local filesystem include
        # that location.  This can permit the user of the specification to
        # access the file directly instead of downloading the file.
        try:
            result['direct_path'] = File().getLocalFilePath(resource)
        except FilePathException:
            pass
    folderPath = send_output(result)
    result['data'] = folderPath
    return result