import girder_client
from ..constants import PluginSettings
import os
import json
import shutil


def _init_client(spec, require_token=False):
    if 'api_url' in spec:
        client = girder_client.GirderClient(
            apiUrl=spec['api_url'])
        # ,
        #     cacheSettings=_get_cache_settings(spec))
    elif 'host' in spec:
        scheme = spec.get('scheme', 'http')
        port = spec.get('port', {
            'http': 80,
            'https': 443
        }[scheme])
        api_root = spec.get('api_root', '/api/v1')
        client = girder_client.GirderClient(
            host=spec['host'], scheme=scheme, apiRoot=api_root, port=port,
            cacheSettings=_get_cache_settings(spec))
    else:
        raise Exception('You must pass either an api_url or host key for '
                        'Girder input and output bindings.')

    if 'token' in spec:
        client.setToken(spec['token'])
    elif require_token:
        raise Exception('You must pass a token for Girder authentication.')

    return client

def send_to_girder(data, spec, **kwargs):
    reference = spec.get('reference')

    if reference is None:
        # Check for reference in the job manager if none in the output spec
        reference = getattr(kwargs.get('_job_manager'), 'reference', None)

    task_output = kwargs.get('task_output', {})
    target = task_output.get('target', 'filepath')

    client = _init_client(spec, require_token=True)

    if target == 'memory':
        _send_to_girder(
            client=client, spec=spec, stream=StringIO(data), size=len(data), reference=reference)
    elif target == 'filepath':
        name = spec.get('name') or os.path.basename(data)
        if os.path.isdir(data):
            if spec['parent_type'] == 'item':
                for f in os.listdir(data):
                    path = os.path.join(data, f)
                    if os.path.isfile(path):
                        client.uploadFileToItem(spec['parent_id'], path, reference=reference)
            else:
                client.upload(data, spec['parent_id'], spec['parent_type'], reference=reference, leafFoldersAsItems=True)
        else:
            size = os.path.getsize(data)
            with open(data, 'rb') as fd:
                _send_to_girder(
                    client=client, spec=spec, stream=fd, size=size, reference=reference, name=name)
    else:
        raise Exception('Invalid Girder push target: ' + target)
def handler(spec):
    client = _init_client(spec)

def fetch_input(spec):
    resource_type = spec.get('resource_type', 'file').lower()
    client = _init_client(spec, require_token=True)
    dest = os.path.join(spec['kwargs']['_tempdir'], spec['name'])
    if resource_type == 'folder':
        client.downloadFolderRecursive(spec['id'], dest)
    elif resource_type == 'file':
        client.downloadFile(spec['id'], dest)
    else:
        raise Exception('Invalid resource type: ' + resource_type)
    return dest

def send_output(job, data):
    resource_type = job.get('resource_type', 'file').lower()
    outputs = json.loads(job['kwargs'])['outputs']
    for output in outputs:
        parent_id = outputs[output]['parent_id']
        parent_type = outputs[output]['parent_type']
        reference = outputs[output]['reference']
        leafFoldersAsItems = json.loads(reference)['leafFoldersAsItems'] if 'leafFoldersAsItems' in json.loads(reference) else True
        client = _init_client(outputs[output], require_token=True)
    if parent_type == 'folder':
        client.upload(data, parent_id, parent_type, reference=reference, leafFoldersAsItems=leafFoldersAsItems)
    elif parent_type == 'item':
        for root, dirs, files in os.walk(data):
            for file in files:
                path = os.path.join(root, file)
                client.uploadFileToItem(parent_id, path, reference=reference)

    inputs = json.loads(job['kwargs'])['inputs']
    girderInputSpec = {k: v for k, v in inputs.items() if v['mode'] == 'girder'}
    localInputSpec = {k: v for k, v in inputs.items() if v['mode'] == 'local'}
    for input in girderInputSpec:
        _tempdir = girderInputSpec[input]['kwargs']['_tempdir']
        shutil.rmtree(_tempdir)
    for input in localInputSpec:
        dataPathOnHPC = localInputSpec[input]['data']
        shutil.rmtree(dataPathOnHPC)
    return job