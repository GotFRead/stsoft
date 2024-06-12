

from fastapi.responses import FileResponse


import os

OBJECT_PATH = os.path.join(os.environ.get('cwd', './'), 'static')


def get_static_file(direction: str = '', filename: str = ''):
    if filename == '':
        return None

    object_override = os.path.join(OBJECT_PATH, direction, filename)
    object_web_static = os.path.join(OBJECT_PATH, 'static', direction, filename)
    default = os.path.join(filename)
    path_to_file = {
        os.path.isfile(default): default,
        os.path.isfile(object_override): object_override,
        os.path.isfile(object_web_static): object_web_static,
    }.get(True)

    if path_to_file == None:
        raise FileNotFoundError()

    return FileResponse(path_to_file)

def get_path_to_var_folder(direction: str = '', filename: str = ''):
    return os.path.join(os.environ.get('cwd', './src'), 'var', direction, filename)