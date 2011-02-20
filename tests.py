#!/usr/bin/env python

import unittest
import random
import imp
dotfiler = imp.load_source('dotfiler', './dotfiler')
import os
import shutil
import tempfile

class TempDirTestCase(unittest.TestCase):
    """
    Create and set temporary home and dot dirs.

    """
    def setUp(self):
        super(TempDirTestCase, self).setUp()
        self.orig_home_dir = dotfiler.HOME_DIR
        self.home_dir = tempfile.mkdtemp()
        self.dot_dir = os.path.join(self.home_dir, "dotfiles")
        os.mkdir(self.dot_dir)
        os.environ['DOTFILES_DIR'] = self.dot_dir
        dotfiler.HOME_DIR = self.home_dir

    def tearDown(self):
        super(TempDirTestCase, self).tearDown()
        dotfiler.HOME_DIR = self.orig_home_dir

class GlobalTests(unittest.TestCase):

    def test_home_dir(self):
        """
        HOME_DIR is set to the environment variable HOME.

        """
        self.assertEqual(dotfiler.HOME_DIR, os.environ["HOME"])

    def test_dot_dir_parent(self):
        exec_dir = os.path.dirname(os.path.abspath(__file__))
        dot_dir = os.path.split(exec_dir)[0]
        os.environ['DOTFILES_DIR'] = ''
        self.assertEqual(dot_dir, dotfiler.dot_dir())
        self.assertEqual(dotfiler.dot_dir(), os.path.abspath(dotfiler.dot_dir()))

    def test_dot_dir_env(self):
        self.dot_dir = os.path.join(tempfile.mkdtemp(), "dotfiles")
        os.environ['DOTFILES_DIR'] = self.dot_dir
        self.assertEqual(self.dot_dir, dotfiler.dot_dir())
        self.assertEqual(dotfiler.dot_dir(), os.path.abspath(dotfiler.dot_dir()))

class FilenamesTest(TempDirTestCase):
    def test_target_paths(self):
        _, _, dotfiler_path = dotfiler.get_dot_dir()
        targets = dotfiler.get_target_paths()
        self.assertFalse(dotfiler_path in targets)
        self.assertTrue(all([not os.path.basename(f).startswith('.')
                             for f in targets]))
        self.assertTrue(all([os.path.dirname(f) == dotfiler.dot_dir()
                             for f in targets]))

    def test_dot_paths(self):
        dots = dotfiler.get_dot_paths()
        self.assertTrue(all([os.path.basename(f).startswith('.')
                             for f in dots]))
        self.assertTrue(all([os.path.dirname(f) == dotfiler.HOME_DIR
                             for f in dots]))

class AddTests(TempDirTestCase):
    def test_dot_to_target(self):
        targetpath = os.path.join(self.dot_dir, "testfile")
        dotpath = os.path.join(self.home_dir, ".testfile")
        self.assertEqual(dotfiler.dot_to_target(dotpath), targetpath)

    def test_normal_file(self):
        dotname = os.path.join(self.home_dir, ".testfile")
        open(dotname, "w").close()
        targetname = os.path.join(dotfiler.dot_dir(), "testfile")

        self.assertFalse(os.path.islink(dotname))
        self.assertFalse(os.path.exists(targetname))
        result = dotfiler.add_path(dotname)
        self.assertTrue(os.path.islink(dotname))
        self.assertTrue(os.path.isfile(targetname))
        self.assertEqual(result, os.path.abspath(targetname))
        self.assertEqual(os.path.abspath(os.readlink(dotname)),
                         os.path.abspath(targetname))

    def test_link_correct(self):
        dotpath = os.path.join(self.home_dir, ".testfile")
        targetpath = dotfiler.dot_to_target(dotpath)
        os.symlink(targetpath, dotpath)

        self.assertTrue(os.path.islink(dotpath))
        self.assertEqual(os.path.abspath(os.readlink(dotpath)),
                         os.path.abspath(targetpath))

        self.assertRaises(dotfiler.AlreadyManagedException,
                          dotfiler.add_path, dotpath)

        # Nothing should have changed
        self.assertTrue(os.path.islink(dotpath))
        self.assertEqual(os.path.abspath(os.readlink(dotpath)),
                         os.path.abspath(targetpath))

    def test_link_other(self):
        dotpath = os.path.join(self.home_dir, ".testfile")
        os.symlink("something", dotpath)

        self.assertTrue(os.path.islink(dotpath))
        self.assertEqual(os.path.abspath(os.readlink(dotpath)),
                         os.path.abspath("something"))
        self.assertRaises(dotfiler.NotManageableException,
                          dotfiler.add_path, dotpath)

        # Nothing should have changed
        self.assertTrue(os.path.islink(dotpath))
        self.assertEqual(os.path.abspath(os.readlink(dotpath)),
                         os.path.abspath("something"))

class RestoreTests(TempDirTestCase):
    def test_managed_file(self):
        dotpath = os.path.join(self.home_dir, ".testfile")
        open(dotpath, "w").close()
        targetpath = dotfiler.add_path(dotpath)
        self.assertTrue(os.path.exists(targetpath))
        self.assertFalse(os.path.islink(targetpath))
        self.assertTrue(os.path.islink(dotpath))
        dotfiler.restore_path(dotpath)
        self.assertFalse(os.path.exists(targetpath))
        self.assertFalse(os.path.islink(dotpath))
        self.assertTrue(os.path.isfile(dotpath))

    def test_unmanaged_file(self):
        dotpath = os.path.join(self.home_dir, ".testfile")
        open(dotpath, "w").close()
        self.assertTrue(os.path.exists(dotpath))
        self.assertFalse(os.path.islink(dotpath))
        self.assertRaises(dotfiler.NotManagedException,
                          dotfiler.restore_path, dotpath)

    def test_nonexistent_file(self):
        dotpath = os.path.join(self.home_dir, ".testfile")
        self.assertFalse(os.path.exists(dotpath))
        self.assertFalse(os.path.islink(dotpath))
        self.assertRaises(dotfiler.NotManagedException,
                          dotfiler.restore_path, dotpath)

class UpdateTests(TempDirTestCase):
    def test_target_to_dot(self):
        targetpath = os.path.join(self.dot_dir, "testfile")
        dotpath = os.path.join(self.home_dir, ".testfile")
        self.assertEqual(dotpath, dotfiler.target_to_dot(targetpath))

    def test_symlink_target(self):
        targetpath = os.path.join(self.dot_dir, "testfile")
        os.symlink(os.path.join(self.dot_dir, "atarget"), targetpath)
        self.assertRaises(dotfiler.TargetIsSymlinkException,
                          dotfiler.update_path, targetpath)

    def test_dotfile_nonexistent(self):
        targetpath = os.path.join(self.dot_dir, "testfile")
        open(targetpath, "w").close()
        dotpath = dotfiler.target_to_dot(targetpath)
        dotfiler.update_path(targetpath)
        self.assertTrue(os.path.exists(dotpath))
        self.assertTrue(os.path.islink(dotpath))
        self.assertEqual(os.readlink(dotpath), targetpath)

    def test_dotfile_islink(self):
        targetpath = os.path.join(self.dot_dir, "testfile")
        dotpath = dotfiler.target_to_dot(targetpath)
        open(targetpath, "w").close()
        os.symlink(targetpath, dotpath)
        dotfiler.update_path(targetpath)
        self.assertTrue(os.path.exists(dotpath))
        self.assertTrue(os.path.islink(dotpath))
        self.assertEqual(os.readlink(dotpath), targetpath)

    def test_dotfile_exists_default(self):
        targetpath = os.path.join(self.dot_dir, "testfile")
        dotpath = dotfiler.target_to_dot(targetpath)
        open(targetpath, "w").close()
        open(dotpath, "w").close()
        self.assertRaises(dotfiler.DotfileExistsException,
                          dotfiler.update_path, targetpath)

    def test_dotfile_exists_overwrite(self):
        targetpath = os.path.join(self.dot_dir, "testfile")
        dotpath = dotfiler.target_to_dot(targetpath)
        open(targetpath, "w").close()
        open(dotpath, "w").close()
        dotfiler.update_path(targetpath, overwrite=True)
        self.assertTrue(os.path.exists(dotpath))
        self.assertTrue(os.path.islink(dotpath))
        self.assertEqual(os.readlink(dotpath), targetpath)

if __name__ == "__main__":
    unittest.main()
