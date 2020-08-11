def _init_client(spec, require_token=False):
    if 'api_url' in spec:
        client = girder_client.GirderClient(
            apiUrl=spec['api_url'],
            cacheSettings=_get_cache_settings(spec))
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