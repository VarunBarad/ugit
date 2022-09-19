import argparse
import os
import subprocess
import sys
import textwrap

import base
import data
import diff
import remote


def main():
    with data.change_git_dir('.'):
        args = parse_args()
        args.func(args)


def parse_args():
    parser = argparse.ArgumentParser()

    commands = parser.add_subparsers(dest='command')
    commands.required = True

    get_oid = base.get_oid

    init_parser = commands.add_parser('init')
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser('hash-object')
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument('file')

    cat_file_parser = commands.add_parser('cat-file')
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument('object', type=get_oid)

    write_tree_parser = commands.add_parser('write-tree')
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser('read-tree')
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument('tree', type=get_oid)

    commit_parser = commands.add_parser('commit')
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument('-m', '--message', required=True)

    log_parser = commands.add_parser('log')
    log_parser.set_defaults(func=log)
    log_parser.add_argument('oid', default='@', type=get_oid, nargs='?')

    show_parser = commands.add_parser('show')
    show_parser.set_defaults(func=show)
    show_parser.add_argument('oid', default='@', type=get_oid, nargs='?')

    diff_parser = commands.add_parser('diff')
    diff_parser.set_defaults(func=_diff)
    diff_parser.add_argument('commit', default='@', type=get_oid, nargs='?')

    checkout_parser = commands.add_parser('checkout')
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument('commit')

    tag_parser = commands.add_parser('tag')
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument('name')
    tag_parser.add_argument('oid', default='@', type=get_oid, nargs='?')

    branch_parser = commands.add_parser('branch')
    branch_parser.set_defaults(func=branch)
    branch_parser.add_argument('name', nargs='?')
    branch_parser.add_argument('start_point', default='@', type=get_oid, nargs='?')

    k_parser = commands.add_parser('k')
    k_parser.set_defaults(func=k)

    status_parser = commands.add_parser('status')
    status_parser.set_defaults(func=status)

    reset_parser = commands.add_parser('reset')
    reset_parser.set_defaults(func=reset)
    reset_parser.add_argument('commit', type=get_oid)

    merge_parser = commands.add_parser('merge')
    merge_parser.set_defaults(func=merge)
    merge_parser.add_argument('commit', type=get_oid)

    merge_base_parser = commands.add_parser('merge-base')
    merge_base_parser.set_defaults(func=merge_base)
    merge_base_parser.add_argument('commit1', type=get_oid)
    merge_base_parser.add_argument('commit2', type=get_oid)

    fetch_parser = commands.add_parser('fetch')
    fetch_parser.set_defaults(func=fetch)
    fetch_parser.add_argument('remote')

    return parser.parse_args()


def init(args):
    base.init()
    print(f'Initialized empty ugit repository in {os.getcwd()}/{data.GIT_DIR}')


def hash_object(args):
    with open(args.file, 'rb') as f:
        print(data.hash_object(f.read()))


def cat_file(args):
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))


def write_tree(args):
    print(base.write_tree())


def read_tree(args):
    base.read_tree(args.tree)


def commit(args):
    print(base.commit(args.message))


def _print_commit(oid, commit_contents, refs=None):
    refs_str = f' ({", ".join(refs)})' if refs else ''
    print(f'commit {oid}{refs_str}\n')
    print(textwrap.indent(commit_contents.message, '\t'))
    print('')


def log(args):
    refs = {}
    for ref_name, ref in data.iter_refs():
        refs.setdefault(ref.value, []).append(ref_name)

    for oid in base.iter_commits_and_parents({args.oid}):
        commit_contents = base.get_commit(oid)
        _print_commit(oid, commit_contents, refs.get(oid))


def show(args):
    if not args.oid:
        return
    commit_contents = base.get_commit(args.oid)
    parent_tree = None
    if commit_contents.parents:
        parent_tree = base.get_commit(commit_contents.parents[0]).tree

    _print_commit(args.oid, commit_contents)
    result = diff.diff_trees(base.get_tree(parent_tree), base.get_tree(commit_contents.tree))
    sys.stdout.flush()
    sys.stdout.buffer.write(result)


def _diff(args):
    tree = args.commit and base.get_commit(args.commit).tree

    result = diff.diff_trees(base.get_tree(tree), base.get_working_tree())
    sys.stdout.flush()
    sys.stdout.buffer.write(result)


def checkout(args):
    base.checkout(args.commit)


def tag(args):
    base.create_tag(args.name, args.oid)


def branch(args):
    if not args.name:
        current_branch_name = base.get_branch_name()
        for branch_name in base.iter_branch_names():
            prefix = '*' if branch_name == current_branch_name else ' '
            print(f'{prefix} {branch_name}')
    else:
        base.create_branch(args.name, args.start_point)
        print(f'Branch {args.name} created at {args.start_point[:10]}')


def k(args):
    dot = 'digraph commits {\n'

    oids = set()
    for ref_name, ref in data.iter_refs(deref=False):
        dot += f'"{ref_name}" [shape=note]\n'
        dot += f'"{ref_name}" -> "{ref.value}"\n'
        if not ref.symbolic:
            oids.add(ref.value)

    for oid in base.iter_commits_and_parents(oids):
        commit_contents = base.get_commit(oid)
        dot += f'"{oid}" [shape=box style=filled label="{oid[:10]}"]\n'
        for parent in commit_contents.parents:
            dot += f'"{oid}" -> "{parent}"\n'

    dot += '}'
    print(dot)

    with subprocess.Popen(['dot', '-Tpng', '/dev/stdin'], stdin=subprocess.PIPE) as proc:
        proc.communicate(dot.encode())


def status(args):
    HEAD = base.get_oid('@')
    branch_name = base.get_branch_name()
    if branch_name:
        print(f'On branch {branch_name}')
    else:
        print(f'HEAD detached at {HEAD[:10]}')

    MERGE_HEAD = data.get_ref('MERGE_HEAD').value
    if MERGE_HEAD:
        print(f'Merging with {MERGE_HEAD[:10]}')

    print('\nChanges to be committed:\n')
    HEAD_tree = HEAD and base.get_commit(HEAD).tree
    for path, action in diff.iter_changed_files(base.get_tree(HEAD_tree), base.get_working_tree()):
        print(f'{action:>12}: {path}')


def reset(args):
    base.reset(args.commit)


def merge(args):
    base.merge(args.commit)


def merge_base(args):
    print(base.get_merge_base(args.commit1, args.commit2))


def fetch(args):
    remote.fetch(args.remote)


main()
