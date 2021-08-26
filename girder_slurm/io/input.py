import os


def localInputSpec(imagePath, name=None, **kwargs):
    result = {
        'mode': 'local',
        'name': name or os.path.basename(imagePath),
        'kwargs': kwargs,
        'data': imagePath
    }

    return result