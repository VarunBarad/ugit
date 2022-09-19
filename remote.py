import data


def fetch(remote_path):
    print('Will fetch the following refs:')
    for ref_name, _ in _get_remote_refs(remote_path, 'refs/heads').items():
        print(f'- {ref_name}')


def _get_remote_refs(remote_path, prefix=''):
    with data.change_git_dir(remote_path):
        return {ref_name: ref.value for ref_name, ref in data.iter_refs(prefix)}
