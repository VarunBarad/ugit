import os

import base
import data

REMOTE_REFS_BASE = 'refs/heads/'
LOCAL_REFS_BASE = 'refs/remote/'


def fetch(remote_path):
    # Get refs from server
    refs = _get_remote_refs(remote_path, REMOTE_REFS_BASE)

    # Fetch missing objects by iterating and fetching on demand
    for oid in base.iter_objects_in_commits(refs.values()):
        data.fetch_object_if_missing(oid, remote_path)

    # Update local refs to match server
    for remote_name, value in refs.items():
        ref_name = os.path.relpath(remote_name, REMOTE_REFS_BASE)
        data.update_ref(f'{LOCAL_REFS_BASE}/{ref_name}'), data.RefValue(symbolic=False, value=value)


def _get_remote_refs(remote_path, prefix=''):
    with data.change_git_dir(remote_path):
        return {ref_name: ref.value for ref_name, ref in data.iter_refs(prefix)}
