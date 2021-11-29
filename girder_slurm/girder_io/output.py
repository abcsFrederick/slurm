from girder.models.setting import Setting
from ..constants import PluginSettings
from .. import utils
from girder_slurm.girder_io import send_output

def sendOutputToGirder(job, data):
    job = send_output(job, data)
    return job

def girderOutputSpec(parent, token, parentType='folder', name=None,
                     dataType='string', dataFormat='text', reference=None):
    if isinstance(token, dict):
        token = token['_id']

    return {
        'mode': 'girder',
        'api_url': utils.getWorkerApiUrl(),
        'token': token,
        'name': name,
        'parent_id': str(parent['_id']),
        'parent_type': parentType,
        'type': dataType,
        'format': dataFormat,
        'reference': reference
    }