#!/usr/bin/env python

import unittest
import random
import dots

import os
import shutil
import tempfile

class TempDirTestCase(unittest.TestCase):
    """
    Create and set temporary home and dot dirs.

    """
    def setUp(self):
        super(TempDirTestCase, self).setUp()
        self.orig_home_dir = dots.HOME_DIR
        self.home_dir = tempfile.mkdtemp()
        self.dot_dir = os.path.join(self.home_dir, "dotfiles")
        os.mkdir(self.dot_dir)
        os.environ['PWD'] = self.dot_dir
        dots.HOME_DIR = self.home_dir

    def tearDown(self):
        super(TempDirTestCase, self).tearDown()
        dots.HOME_DIR = self.orig_home_dir

class GlobalTests(unittest.TestCase):

    def test_home_dir(self):
        """
        HOME_DIR is set to the environment variable HOME.

        """
        self.assertEqual(dots.HOME_DIR, os.environ["HOME"])

    def test_dot_dir_current(self):
        self.dot_dir = os.path.join(tempfile.mkdtemp(), "dotfiles")
        os.environ['PWD'] = self.dot_dir
        self.assertEqual(self.dot_dir, dots.dot_dir())

    def test_dot_to_target(self):
        pass

class AddTests(TempDirTestCase):
    def test_normal_file(self):
        dotname = os.path.join(self.home_dir, ".testfile")
        open(dotname, "w").close()
        targetname = os.path.join(dots.dot_dir(), "testfile")

        self.assertFalse(os.path.islink(dotname))
        self.assertFalse(os.path.exists(targetname))
        result = dots.add(dotname)
        self.assertTrue(os.path.islink(dotname))
        self.assertTrue(os.path.isfile(targetname))
        self.assertEqual(result, os.path.abspath(targetname))
        self.assertEqual(os.path.abspath(os.readlink(dotname)),
                         os.path.abspath(targetname))

    def test_link_correct(self):
        dotpath = os.path.join(self.home_dir, ".testfile")
        targetpath = dots.dot_to_target(dotpath)
        os.symlink(targetpath, dotpath)

        self.assertTrue(os.path.islink(dotpath))
        self.assertEqual(os.path.abspath(os.readlink(dotpath)),
                         os.path.abspath(targetpath))

        self.assertRaises(dots.AlreadyManagedException, dots.add, dotpath)

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
        self.assertRaises(dots.NotManageableException, dots.add, dotpath)
        # Nothing should have changed
        self.assertTrue(os.path.islink(dotpath))
        self.assertEqual(os.path.abspath(os.readlink(dotpath)),
                         os.path.abspath("something"))

class RestoreTests(TempDirTestCase):
    def test_managed_file(self):
        dotpath = os.path.join(self.home_dir, ".testfile")
        open(dotpath, "w").close()
        targetpath = dots.add(dotpath)
        self.assertTrue(os.path.exists(targetpath))
        self.assertFalse(os.path.islink(targetpath))
        self.assertTrue(os.path.islink(dotpath))
        dots.restore(dotpath)
        self.assertFalse(os.path.exists(targetpath))
        self.assertFalse(os.path.islink(dotpath))
        self.assertTrue(os.path.isfile(dotpath))

    def test_unmanaged_file(self):
        dotpath = os.path.join(self.home_dir, ".testfile")
        open(dotpath, "w").close()
        self.assertTrue(os.path.exists(dotpath))
        self.assertFalse(os.path.islink(dotpath))
        self.assertRaises(dots.NotManagedException, dots.restore, dotpath)

    def test_nonexistent_file(self):
        dotpath = os.path.join(self.home_dir, ".testfile")
        self.assertFalse(os.path.exists(dotpath))
        self.assertFalse(os.path.islink(dotpath))
        self.assertRaises(dots.NotManagedException, dots.restore, dotpath)

class UpdateTests(TempDirTestCase):
    pass

if __name__ == "__main__":
    unittest.main()
