import re

def open_file(path):
    data = None
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    return data

def write_in_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)
    return None

def change_version(version):
    version = version if 'v' in version else f'v{version}'

    # For changing in __version__.py, Animation.html and build.yml
    paths = ['Animation/Animation.html', './__version__.py', '.github/workflows/build.yml']
    
    for path in paths:
        version_file_data = open_file(path)
        changed_data = re.sub(r'v\d+\.\d+', version, version_file_data)
        write_in_file(path, changed_data)

if __name__ == '__main__':
    NEW_VERSION = 'v1.3' # CHANGE VERSION HERE AND RUN THIS FILE
    change_version(NEW_VERSION)