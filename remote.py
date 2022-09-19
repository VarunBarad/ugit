import data


def fetch(remote_path):
    print('Will fetch the following refs:')
    with data.change_git_dir(remote_path):
        for ref_name, _ in data.iter_refs('refs/heads'):
            print(f'- {ref_name}')
