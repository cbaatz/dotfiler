#!/usr/bin/env python
"""
dotfiler is a Python script for simplifying handling and versioning of
Unix dotfiles.

dotfiler works with undotted files in a separate directory then links
these to your home directory with leading dots. This allows you to
easily backup and version-control the dotfiles you care about.

dotfiler features:

dotfiler init DIRNAME
Initialises dotfiler usage setting the dotfiles dir to DIRNAME

dotfiler manage FILES
Adds dotfiles listed in FILES to the managed files.

dotfiler unmanage FILES
Unmanage dotfiles listed in FILES; this moves the file from the
dotfiles dir to the home dir.

dotfiler restore 
Restores dotfiler links to a new system given an existing backup.

"""
from __future__ import print_function
import os
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
CONFIG_NAME = ".dotfiles"

class ConfigMissingException(Exception):
    pass
class ConfigExistsException(Exception):
    pass
class ConfigInvalidException(Exception):
    pass
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

def symlink_filename():
    return os.path.abspath(os.path.join(HOME_DIR, CONFIG_NAME))

def nodot(string):
    return string.lstrip(".")

def get_config():
    symlink = symlink_filename()
    if not os.path.exists(symlink):
        raise ConfigMissingException("%s or its target is missing." % symlink)
    else:
        try:
            target = os.readlink(symlink)
            if os.path.isfile(target):
                return open(target, "rw")
            elif os.path.isdir(target):
                raise ConfigInvalidException(
                    "Config target '%s' is a directory." % target)
            else:
                raise ConfigInvalidException(
                    "Config target '%s' is not a normal file." % target)
        except OSError:
            raise ConfigInvalidException("%s not a symlink." % symlink)
 
def init(dot_dir):
    """
    Create dot_dir, put dotfiles file in it and symlink from home dir.

    """
    symlink = symlink_filename()
    if os.path.exists(dot_dir):
        raise DirExistsException("%s already exists." % dot_dir)
    elif os.path.lexists(symlink):
        raise ConfigExistsException("%s already exists." % symlink)
    else:
        try:
            os.makedirs(dot_dir)
            target = os.path.join(dot_dir, nodot(CONFIG_NAME))
            f = open(target, "w")
            f.close()
            os.symlink(target, symlink)
        except OSError:
            raise Exception("Conflicting files added during action")

def is_managed(dotfile_path):
    config_file = get_config()
    dot_dir = os.path.dirname(config_file.name)
    check_path = dotfile_path
    while check_path.lstrip(HOME_DIR):
        if os.path.islink(check_path):
            target = os.readlink(check_path)
            return os.path.dirname(target).startswith(dot_dir) and os.path.exists(target)
        check_path, _ = os.path.split(check_path)
    else:
        return False

def generate_filenames(path):
    """
    Generate list of absolute filenames inside the given file/dir.

    """
    path = os.path.abspath(path)
    if os.path.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                yield os.path.join(dirpath, f)

def is_partially_managed(dotfile_path):
    """
    Checks if one or more files inside a directory is managed.

    """
    config_file = get_config()
    dot_dir = os.path.dirname(config_file.name)
    for f in generate_filenames(dotfile_path):
        if is_managed(f):
            return True
    return False

def manage(dotfile_path):
    """
    Put a file under management by moving it to DOT_DIR and then
    symlinking from HOME dir.
    
    """
    config_file = get_config()
    dot_dir = os.path.dirname(config_file.name)
    
    if not os.path.exists(dotfile_path):
        raise NotManageableException("%s does not exist." % dotfile_path)
    elif not os.path.dirname(dotfile_path).startswith(HOME_DIR):
        raise NotManageableException("%s is not in your home dir.")
    else:
        rel_path = dotfile_path.lstrip(HOME_DIR)
        if not rel_path.startswith("."):
            raise NotManageableException("%s is not a dotfile." % dotfile_path)
        elif is_managed(dotfile_path):
            raise AlreadyManagedException(
                "%s (or a parent dir) is already managed." % dotfile_path)
        elif os.path.islink(dotfile_path):
            raise NotManageableException("%s is a link." % dotfile_path)
        elif is_partially_managed(dotfile_path):
            raise PartiallyManagedException(
                "%s is partially managed" % dotfile_path)
        else:
            dotless_rel_path = nodot(rel_path)
            managed_path = os.path.join(dot_dir, dotless_rel_path)
            # Create dir if it does not already exist
            try:
                managed_dir = os.path.dirname(managed_path)
                os.makedirs(managed_dir)
            except OSError:
                pass
            shutil.move(dotfile_path, managed_path)
            os.symlink(managed_path, dotfile_path)
            return managed_path

def unmanage(dotfile_path):
    """
    Moves a managed dotfile back to the homedir.

    """
    config_file = get_config()
    dot_dir = os.path.dirname(config_file.name)
    files = []

    if is_partially_managed(dotfile_path):
        files = list(generate_filenames(dotfile_path))
    elif not is_managed(dotfile_path):
        raise NotManagedException("%s is not a managed dotfile." % dotfile_path)
    else:
        files = [dotfile_path]

    for f in files:
        if is_managed(f):
            target_file = os.path.join(os.path.dirname(f), os.readlink(f))
            os.remove(f)
            shutil.move(target_file, f)
        
if __name__ == "__main__":
#    unmanage(sys.argv[1])
 #   manage(sys.argv[1])
    init(os.path.abspath("dotfiler"))
