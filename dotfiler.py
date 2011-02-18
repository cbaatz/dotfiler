#!/usr/bin/env python
"""
Dotfiler makes it easier to manage dot-files using symlinks to a
separate directory. The dot-files you want to manage are symlinks to a
file with the same name but without the leading dot in a separate
dot-files directory. See README.org for usage.

"""
from __future__ import print_function
import os
from os.path import exists, isfile, islink
import shutil
import sys

# Flush stdoutput immediately
class flushfile(object):
    def __init__(self, f):
        self.f = f
    def write(self, x):
        self.f.write(x)
        self.f.flush()
sys.stdout = flushfile(sys.stdout)

HOME_DIR = os.environ['HOME']

def dot_dir():
    return os.path.abspath(os.environ['PWD'])

class DirExistsException(Exception):
    pass
class NotManageableException(Exception):
    pass
class AlreadyManagedException(Exception):
    pass
class PartiallyManagedException(Exception):
    pass
class NotManagedException(Exception):
    pass
class TargetIsSymlinkException(Exception):
    pass
class DotfileExistsException(Exception):
    pass

def undot(string):
    return string.lstrip(".")

def dot_to_target(path):
    # TODO: exception if dir is not home
    filename = os.path.basename(path)
    if filename.startswith("."):
        nakedname = filename[1:]
#    else:
#        raise NotManageableException("%s does not start with a dot.", filename)
    return os.path.join(dot_dir(), nakedname)

def target_to_dot(path):
    filename = os.path.basename(path)
    if not filename.startswith("."):
        dotname = "." + filename
    # else:
    #     raise Exception
    return os.path.join(HOME_DIR, dotname)

def add_path(dot_path):
    """
    Add dot_path to managed dot-files by moving it to dot_dir without
    leading dot, and creating a symlink from the home directory to
    that.

    """
    if os.path.islink(dot_path):
        if os.readlink(dot_path) == dot_to_target(dot_path):
            raise AlreadyManagedException("%s is already a managed link" % dot_path)
        else:
            raise NotManageableException("%s is a link." % dot_path)

    target_path = dot_to_target(dot_path)
    shutil.move(dot_path, target_path)
    os.symlink(target_path, dot_path)
    return target_path

def restore_path(dot_path):
    """
    Restore dot_path to the home directory by moving it from the
    dot-files directory.

    """
    if not os.path.exists(dot_path):
        raise NotManagedException("%s does not exist." % dot_path)
    elif not os.path.islink(dot_path):
        raise NotManagedException("%s is not a link." % dot_path)
    elif os.readlink(dot_path) != dot_to_target(dot_path):
        raise NotManagedException(
            "%s is not a link to the dot-files directory." % dot_path)
    else:
        os.remove(dot_path)
        shutil.move(dot_to_target(dot_path), dot_path)

def update_path(target_path, overwrite=False):
    """
    Update target_path in home directory (creating symlink to it).

    """
    dot_path = target_to_dot(target_path)
    if os.path.islink(target_path):
        raise TargetIsSymlinkException("%s is a symlink." % target_path)
    elif exists(dot_path) and not islink(dot_path) \
             and not (isfile(dot_path) and overwrite):
        raise DotfileExistsException("%s exists." % dot_path)
    else: # Overwrite symlink
        try:
            os.remove(dot_path)
        except:
            pass
        os.symlink(target_path, dot_path)
    return dot_path

def add(namespace):
    files = namespace.files
    for f in map(os.path.abspath, files):
        print("Adding %s to managed files..." % f, end="")
        try:
            add_path(f)
            print(" DONE.")
        except NotManageableException as e:
            print(" ERROR: %s" % e.message)
        except AlreadyManagedException as e:
            print(" ERROR: %s" % e.message)

def restore(namespace):
    files = namespace.files
    for f in map(os.path.abspath, files):
        print("Removing %s from management..." % f, end="")
        try:
            restore_path(f)
            print(" DONE.")
        except NotManagedException as e:
            print(" ERROR: %s" % e.message)

def update(namespace):
    overwrite = namespace.overwrite
    path = dot_dir()
    files = map(lambda x: os.path.join(path, x), os.listdir(path))

    if len(files) < 1:
        print("Nothing to do. DONE.")
    else:
        print("%d file(s) to update" % len(files))
        for f in files:
            print("Symlinking to %s..." % f, end="")
            try:
                update_path(f)
                print(" DONE.")
            except DotfileExistsException as e:
                print(" SKIPPING: %s" % e.message)
            except TargetIsSymlink as e:
                print(" SKIPPING: %s" % e.message)

    # TODO: Add clean-up broken links function

import argparse

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="Available commands",
                                       help='sub-command help')

    parser_a = subparsers.add_parser('add', help='Add dot-file to management')
    parser_a.set_defaults(func=add)
    parser_a.add_argument('files', metavar='DOTFILE', type=str, nargs='+',
                          help='File to add')

    parser_r = subparsers.add_parser('restore', help='Restore dot-file to home-dir')
    parser_r.set_defaults(func=restore)
    parser_r.add_argument('files', metavar='DOTFILE', type=str, nargs='+',
                          help='File to restore')

    parser_u = subparsers.add_parser('update',
                                     help='Update symlinks to managed files')
    parser_u.add_argument('--overwrite', action='store_true',
                          help='OVERWRITE existing dot-files with symlink.')
    parser_u.set_defaults(func=update)

    if not sys.argv[1:]:
        parser.print_help()
    else:
        args = parser.parse_args(sys.argv[1:])
        args.func(args)

if __name__ == "__main__":
    main()
