import os

import data


def write_tree(directory='.'):
    with os.scandir(directory) as it:
        for entry in it:
            full = f'{directory}/{entry.name}'
            if entry.is_file(follow_symlinks=False):
                # ToDo: Write the file to object store
                print(full)
            elif entry.is_dir(follow_symlinks=False):
                write_tree(full)

    # ToDo: Actually create the tree object
