from girder.models.setting import Setting
from ..constants import PluginSettings
from .. import utils
from girder_slurm.girder_io import send_output


def getWorkerApiUrl():
    """
    Return the API base URL to which the worker should callback to
    write output information back to the server. This is controlled
    via a system setting, and the default is to use the core server
    root setting.
    """
    apiUrl = Setting().get(PluginSettings.API_URL)
    return apiUrl or getApiUrl()

def sendOutputToGirder(job, data):
    job = send_output(job, data)
    print ('send finished')
    return job

def girderOutputSpec(parent, token, parentType='folder', name=None,
                     dataType='string', dataFormat='text', reference=None):
    if isinstance(token, dict):
        token = token['_id']

    return {
        'mode': 'girder',
        'api_url': getWorkerApiUrl(),
        'token': token,
        'name': name,
        'parent_id': str(parent['_id']),
        'parent_type': parentType,
        'type': dataType,
        'format': dataFormat,
        'reference': reference
    }